import os
import json
import math
import subprocess
import urllib.request

import boto3
from botocore.exceptions import ClientError

DYNAMO_PGXFLOW_REFERENCES_TABLE = os.environ.get("DYNAMO_PGXFLOW_REFERENCES_TABLE")

s3 = boto3.resource("s3")
dynamodb = boto3.client("dynamodb")


def truncate_tmp(filename):
    return filename.replace("/tmp/", "")


def prepend_tmp(filename):
    return f"/tmp/{truncate_tmp(filename)}"


def download_remote_content(url, filename):
    # Open the URL and fetch the headers to get content length
    with urllib.request.urlopen(url) as response:
        total_size = int(response.headers.get("Content-Length", 0))

        with open(filename, "wb") as file:
            bytes_downloaded = 0
            chunk_size = 8192
            iter = -1
            # Read the content in chunks
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                file.write(chunk)
                bytes_downloaded += len(chunk)

                percent_complete = (bytes_downloaded / total_size) * 100

                # Log every 10% complete
                decile = int(math.floor(percent_complete)) // 10
                if decile > iter:
                    print(
                        f"\rDownloading {filename}: {bytes_downloaded}/{total_size} bytes ({percent_complete:.2f}%)"
                    )
                    iter = decile


# Web fetching, downloading
def fetch_remote_content(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


# dynamodb actions
def query_references_table(id):
    kwargs = {
        "TableName": DYNAMO_PGXFLOW_REFERENCES_TABLE,
        "Key": {
            "id": {
                "S": id,
            },
        },
    }

    print(f"Calling dynamodb.get_item with kwargs: {json.dumps(kwargs)}")
    try:
        response = dynamodb.get_item(**kwargs)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            print(f"Table {DYNAMO_PGXFLOW_REFERENCES_TABLE} not found.")
            raise e
        else:
            print(f"Unexpected error: {error_code}")
            raise e
    print(f"Received response: {json.dumps(response, default=str)}")
    return response


def update_references_table(id, version):
    kwargs = {
        "TableName": DYNAMO_PGXFLOW_REFERENCES_TABLE,
        "Key": {
            "id": {
                "S": id,
            },
        },
        "UpdateExpression": "SET version = :version",
        "ConditionExpression": "attribute_exists(#id) OR attribute_not_exists(#id)",
        "ExpressionAttributeNames": {
            "#id": "id",
        },
        "ExpressionAttributeValues": {
            ":version": {
                "S": version,
            },
        },
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    try:
        response = dynamodb.update_item(**kwargs)
    except ClientError as e:
        print(f"Received unexpected ClientError: {json.dumps(e.response, default=str)}")
        raise e
    print(f"Received response: {json.dumps(response, default=str)}")


# S3 actions
def s3_download(bucket, keys, files=None):
    files = keys if files == None else files
    assert len(keys) == len(files)
    for key, file in zip(keys, files):
        print(f"Downloading from bucket: {bucket}, key: {key} -> local file: {file}.")
        s3.Bucket(bucket).download_file(key, file)
    print("Download(s) complete.")


def s3_upload(bucket, keys, files=None):
    files = keys if files == None else files
    assert len(keys) == len(files)
    for key, file in zip(keys, files):
        print(f"Uploading local file: {file} -> bucket: {bucket}, key: {key}.")
        s3.Bucket(bucket).upload_file(file, key)
    print("Upload(s) complete.")


# Bash subprocesses
def execute_subprocess(command, log=True):
    if log:
        print(f"Executing command: {command}")
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(f"Command failed: {e}")
        raise

def tar_extract(file):
    command = f"tar -xzvf {file}"
    execute_subprocess(command)
