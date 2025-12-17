import os

import boto3

from shared.utils import fetch_remote_content, query_references_table

s3_client = boto3.client("s3")

DBSNP_MD5_URL = (
    "https://ftp.ncbi.nlm.nih.gov/snp/organisms/human_9606/VCF/00-All.vcf.gz.md5"
)
LOOKUP_REFERENCE = os.environ["LOOKUP_REFERENCE"]


def check_dbsnp_version():
    id = "dbsnp_version"
    local_dbsnp_version = query_references_table(id)
    dbsnp_md5_content = fetch_remote_content(DBSNP_MD5_URL).decode("utf-8")
    latest_dbsnp_version = dbsnp_md5_content.strip().split(" ")[0]
    return latest_dbsnp_version != local_dbsnp_version, latest_dbsnp_version


def check_lookup_version():
    lookup_reference_staging = f"staging/{LOOKUP_REFERENCE}"
    reference_bucket = os.environ["REFERENCE_LOCATION"]
    try:
        s3_client.head_object(
            Bucket=reference_bucket,
            Key=lookup_reference_staging,
        )
        return True
    except s3_client.exceptions.NoSuchKey:
        return False
