import hashlib
import csv
import os

import boto3

from shared.utils import update_references_table

s3_client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")

LOCAL_DIR = "/tmp"
REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
LOOKUP_REFERENCE = os.environ["LOOKUP_REFERENCE"]
CHR_HEADER = os.environ["CHR_HEADER"]
START_HEADER = os.environ["START_HEADER"]
END_HEADER = os.environ["END_HEADER"]


def update_lookup():
    staging_lookup_reference = f"staging/{LOOKUP_REFERENCE}"
    prod_lookup_reference = f"prod/{LOOKUP_REFERENCE}"
    s3_client.download_file(
        Bucket=REFERENCE_LOCATION,
        Key=staging_lookup_reference,
        Filename=os.path.join(LOCAL_DIR, LOOKUP_REFERENCE),
    )

    with open(os.path.join(LOCAL_DIR, LOOKUP_REFERENCE), "rb") as f:
        # Read the CSV and sort it by chromosome and position
        reader = csv.DictReader(f)
        sorted_rows = sorted(
            reader,
            key=lambda x: (x[CHR_HEADER], int(x[START_HEADER]), int(x[END_HEADER])),
        )
    with open(os.path.join(LOCAL_DIR, LOOKUP_REFERENCE), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(sorted_rows)

    # Calculate MD5 checksum
    md5 = hashlib.md5()
    with open(os.path.join(LOCAL_DIR, LOOKUP_REFERENCE), "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    checksum = md5.hexdigest()

    # Upload the updated file back to S3 with new metadata
    s3_client.upload_file(
        Filename=os.path.join(LOCAL_DIR, LOOKUP_REFERENCE),
        Bucket=REFERENCE_LOCATION,
        Key=prod_lookup_reference,
    )
    # Update dynamodb table to reflect the new hash
    update_references_table("lookup_hash", checksum)
