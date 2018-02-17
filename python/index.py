#! /usr/bin/env python
#
# The following IAM permissions are required . . .
#
#   ec2:DescribeVpcs
#   ec2:DescribeSubnets

import http.client
import json
import logging
import os
from urllib.parse import urlparse

import boto3

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'INFO').upper())

MSG_EMPTY_PROPS = 'Empty resource properties'
MSG_MISSING_PROP = 'Required resource property VpcId is not set'
MSG_UNKNOWN_ERROR = 'Unable to get VPC properties - See CloudWatch logs for ' \
                    'the Lambda function backing this custom resource for ' \
                    'details'


def send_response(request, response, status=None, reason=None):
    """ Send our response to the pre-signed URL supplied by CloudFormation
    If no ResponseURL is found in the request, there is no place to send a
    response. This may be the case if the supplied event was for testing.
    """
    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    logger.debug("Response body is: %s", response)

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urlparse(request['ResponseURL'])
        body = json.dumps(response)
        https = http.client.HTTPSConnection(url.hostname)
        logger.debug("Sending response to %s", request['ResponseURL'])
        https.request('PUT', url.path + '?' + url.query, body)
    else:
        logger.debug("No response sent (ResponseURL was empty)")

    return response


def send_fail(request, response, reason=None):
    if reason is not None:
        logger.error(reason)
    else:
        reason = 'Unknown Error - See CloudWatch log stream of the Lambda ' \
                 'function backing this custom resource for details'

    return send_response(request, response, 'FAILED', reason)


def lambda_handler(event, context=None):

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Status': 'SUCCESS'
    }

    # Make sure resource properties are there
    try:
        props = event['ResourceProperties']
    except KeyError:
        return send_fail(event, response, MSG_EMPTY_PROPS)

    try:
        vpc_id = props['VpcId']
    except KeyError:
        return send_fail(event, response, MSG_MISSING_PROP)

    # PhysicalResourceId is meaningless here, but CloudFormation requires it
    # returning the VPC ID seems to make the most sense...
    response['PhysicalResourceId'] = vpc_id

    # There is nothing to do for a delete request
    if event['RequestType'] == 'Delete':
        return send_response(event, response)

    # Lookup the subnets and availability zones for the VPC using supplied
    # filters, if any
    ec2 = boto3.resource('ec2')
    vpc = ec2.Vpc(vpc_id)

    try:
        cidr_block = vpc.cidr_block

        if 'SubnetFilters' not in props:
            subnets = vpc.subnets.all()
        else:
            subnets = vpc.subnets.filter(Filters=props['SubnetFilters'])

        subnet_ids = [subnet.id for subnet in subnets]
        availability_zones = list(set(
            [subnet.availability_zone for subnet in subnets]
        ))
    except Exception as E:
        logging.error(str(E))
        return send_fail(event, response, str(E))

    response['Data'] = {
        'SubnetIds': subnet_ids,
        'AvailabilityZones': availability_zones,
        'CidrBlock': cidr_block
    }

    return send_response(event, response)
