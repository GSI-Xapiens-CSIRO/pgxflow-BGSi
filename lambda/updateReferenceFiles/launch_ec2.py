import base64
import bz2
import json
import math
import os

import boto3

EC2_IAM_INSTANCE_PROFILE = os.environ["EC2_IAM_INSTANCE_PROFILE"]
REFERENCE_BUCKET = os.environ["REFERENCE_BUCKET"]
DYNAMO_SVEP_REFERENCES_TABLE = os.environ["DYNAMO_SVEP_REFERENCES_TABLE"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]

REGION_AMI_MAP = {
    "ap-southeast-2": "ami-0d6560f3176dc9ec0",
    "ap-southeast-3": "ami-01ca3951ed2aa735e",
}

def launch_refupd_ec2(
    ec2_startup,
    object_key,
    size_gb,
):
    ec2_client = boto3.client("ec2")
    ami = REGION_AMI_MAP[AWS_DEFAULT_REGION]
    device_name = ec2_client.describe_images(ImageIds=[ami])["Images"][0][
        "RootDeviceName"
    ]

    try:
        response = ec2_client.run_instances(
            ImageId=ami,        
            InstanceType="m5.large",
            MinCount=1,
            MaxCount=1,
            BlockDeviceMappings=[
                {
                    "DeviceName": device_name,
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "VolumeSize": math.ceil(
                            size_gb
                        ),
                        "VolumeType": "gp3",
                        "Encrypted": True,
                    },
                }
            ],
            UserData=ec2_startup,
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "File", "Value": f"{object_key}"}],
                }
            ],
            IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE},
        )

        instance_id = response["Instances"][0]["InstanceId"]
        print(f"Launched EC2 instance {instance_id} for reference update")
    except Exception as e:
        print(f"Failed to launch EC2 instance: {e}")
