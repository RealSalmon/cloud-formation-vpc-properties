# cloud-formation-vpc-properties

[![CircleCI](https://circleci.com/gh/RealSalmon/cloud-formation-vpc-properties.svg?style=svg)](https://circleci.com/gh/RealSalmon/cloud-formation-vpc-properties)

## A Lambda-backed custom resource for CloudFormation

### Purpose:

This custom resource allows for a little more sophistication and a little less
hassle when configuring stack resources that require VPC, Subnet, and 
Availability Zone parameters.

Rather than manually selecting subnets within a VPC and also needing to specify
matching availability zone (often several times), a VPC can be queried by this
resource to provide to correct values based on filter criteria.

### Installation
This custom resource can be installed on your AWS account by deploying the 
CloudFormation template at cloud-formation/cloud-formation.yml, and then 
updating the Lambda function it creates with the code from python/index.py

The Lambda function's ARN, which is needed for use as a service token when
using this custom resource in your CloudFormation  templates, will be exported
as an output with the name ```${AWS::StackName}-FunctionArn```. This service
token will also be stored in
[Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-paramstore.html)
at
```/cloud-formation/service-tokens/vpc-properties```

Once installed, you can test the custom resource by using the CloudFormation
template at cloud-formation/example-cloud-formation.yml, which will create a 
stack using outputs from the custom resource.

### Syntax:

The syntax for declaring this resource:

```yaml
VpcProperties:
  Type: "AWS::CloudFormation::CustomResource"
  Version: "1.0"
  Properties:
    ServiceToken: LAMDA_FUNCTION_ARN
    VpcId: VPC_ID
    SubnetFilters: [...]
```
### Properties

#### Service Token
##### The ARN of the Lambda function backing the custom resource

Type: String

Required: Yes

#### VpcId
##### The ID of the VPC to use

Type: String

Required: Yes

#### Subnet Filters
##### A list of filters to use when querying the VPC's subnets

Type: List of Filter Objects

Required: No (the default behavior is to return all subnets in the VPC)

For additional information, see the AWS documentation on the 
[DescribeSubnets API](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSubnets.html)

### Return Values

#### Ref
When the logical ID of this resource is provided to the Ref intrinsic function, 
Ref returns a meaningless GUID that is not useful for any purpose.

#### Fn::GetAtt

Fn::GetAtt returns a value for a specified attribute of this type. The 
following are the available attributes.

##### SubnetIds

A list of SubnetIds within the VPC that meet the optional filter criteria.

##### AvailabilityZones

A list of availability zones for subnets within the VPC that meet the optional
filter criteria

##### CidrBlock

The CIDR Block of the VPC. e.g. 172.31.0.0/16
