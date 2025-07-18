import json
import os

import boto3

EC2_IAM_INSTANCE_PROFILE = os.environ["EC2_IAM_INSTANCE_PROFILE"]
REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
AWS_REGION = os.environ["AWS_REGION"]
FUNCTION_NAME = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
DYNAMO_PGXFLOW_REFERENCES_TABLE = os.environ["DYNAMO_PGXFLOW_REFERENCES_TABLE"]

REGION_AMI_MAP = {
    "ap-southeast-2": "ami-0822a7a2356687b0f",
    "ap-southeast-3": "ami-0f6fd501d5bfeb733",
}


def update_dbsnp(dbsnp_version):
    ec2_client = boto3.client("ec2")
    ami = REGION_AMI_MAP[AWS_REGION]
    device_name = ec2_client.describe_images(ImageIds=[ami])["Images"][0][
        "RootDeviceName"
    ]

    with open("dbsnp.sh") as user_data_file:
        ec2_startup = (
            user_data_file.read()
            .replace("__REGION__", AWS_REGION)
            .replace("__TABLE__", DYNAMO_PGXFLOW_REFERENCES_TABLE)
            .replace("__DBSNP_ID__", "dbsnp_version")
            .replace("__DBSNP_VERSION__", dbsnp_version)
            .replace("__REFERENCE_LOCATION__", REFERENCE_LOCATION)
        )
    try:
        response = ec2_client.run_instances(
            ImageId=REGION_AMI_MAP[AWS_REGION],
            InstanceType="t3.medium",
            MinCount=1,
            MaxCount=1,
            BlockDeviceMappings=[
                {
                    "DeviceName": device_name,
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "VolumeSize": 50,
                        "VolumeType": "gp3",
                        "Encrypted": True,
                    },
                },
            ],
            UserData=ec2_startup,
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": f"{FUNCTION_NAME}"}],
                }
            ],
            IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE},
        )
        instance_id = response["Instances"][0]["InstanceId"]
    except Exception as e:
        print(f"Error launching EC2 instance: {str(e)}")
        return {"statusCode": 500, "body": json.dumps("Error launching EC2 instance")}
    print(f"Launched EC2 instance {instance_id} to retrieve dbsnp references")
    return {
        "StatusCode": 200,
        "body": json.dumps(f"Launched EC2 instance {instance_id}"),
    }
