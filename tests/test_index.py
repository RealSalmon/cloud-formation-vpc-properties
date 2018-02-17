import boto3
from moto import mock_ec2
from index import lambda_handler
from index import MSG_EMPTY_PROPS, MSG_MISSING_PROP

vpc = '172.31.0.0/16'
subnets = {
    'us-east-1a': '172.31.0.0/20',
    'us-east-1b': '172.31.16.0/20'
}

vpc_id = None
subnet_ids = None


def create_network(module=None):

    global vpc_id, subnet_ids

    subnet_ids = []

    client = boto3.client('ec2')
    v = client.create_vpc(
        CidrBlock=vpc,
        InstanceTenancy='default'
    )
    
    vpc_id = v['Vpc']['VpcId']

    for az, cidr in subnets.items():
        print(az)
        print(cidr)
        net = client.create_subnet(
            AvailabilityZone=az,
            CidrBlock=cidr,
            VpcId=vpc_id
        )
        print(net['Subnet']['SubnetId'])
        subnet_ids.append(net['Subnet']['SubnetId'])


def teardown_module(module):
    pass


def get_event():
    return {
        "StackId": "12345",
        "RequestId": "ohai!",
        "LogicalResourceId": "best-logical-resource-evar",
        "RequestType": "Create",
        "ResourceProperties": {"VpcId": "changeme"}
    }


def test_empty_params():
    event = get_event()
    del event['ResourceProperties']
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == MSG_EMPTY_PROPS


def test_missing_params():
    event = get_event()
    event['ResourceProperties'] = {'SomeGarbage': 'DoNotWant'}
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == MSG_MISSING_PROP


def test_delete():
    event = get_event()
    event['RequestType'] = 'Delete'
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']


@mock_ec2
def test_no_such_vpc():
    event = get_event()
    response = lambda_handler(event)
    assert 'Status' in response
    assert response['Status'] == 'FAILED'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['RequestId'] == event['RequestId']
    assert response['Reason'] == 'An error occurred (InvalidVpcID.NotFound) ' \
                                 'when calling the DescribeVpcs operation: ' \
                                 'VpcID {\'changeme\'} does not exist.'


@mock_ec2
def test_success_basic():

    create_network()
    event = get_event()
    event['ResourceProperties']['VpcId'] = vpc_id
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['PhysicalResourceId'] == vpc_id
    assert response['RequestId'] == event['RequestId']

    data = response['Data']
    assert data['CidrBlock'] == vpc
    assert set(data['AvailabilityZones']) == set(subnets.keys())
    assert set(data['SubnetIds']) == set(subnet_ids)


@mock_ec2
def test_success_filters():

    create_network()
    event = get_event()
    event['ResourceProperties']['VpcId'] = vpc_id
    event['ResourceProperties']['SubnetFilters'] = [{
        'Name': 'availabilityZone',
        'Values': ['us-east-1b']
    }]
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['PhysicalResourceId'] == vpc_id
    assert response['RequestId'] == event['RequestId']

    data = response['Data']
    assert data['CidrBlock'] == vpc
    assert len(data['AvailabilityZones']) == 1
    assert len(data['SubnetIds']) == 1
    assert data['AvailabilityZones'][0] == 'us-east-1b'
    assert data['SubnetIds'][0] == subnet_ids[1]

@mock_ec2
def test_filters_return_empty():

    create_network()
    event = get_event()
    event['ResourceProperties']['VpcId'] = vpc_id
    event['ResourceProperties']['SubnetFilters'] = [{
        'Name': 'availabilityZone',
        'Values': ['us-east-1z']
    }]
    response = lambda_handler(event)
    assert response['Status'] == 'SUCCESS'
    assert response['StackId'] == event['StackId']
    assert response['LogicalResourceId'] == event['LogicalResourceId']
    assert response['PhysicalResourceId'] == vpc_id
    assert response['RequestId'] == event['RequestId']

    data = response['Data']
    assert data['CidrBlock'] == vpc
    assert len(data['AvailabilityZones']) == 0
    assert len(data['SubnetIds']) == 0

