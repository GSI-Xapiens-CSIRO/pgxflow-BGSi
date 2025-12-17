import hashlib
import csv
import os

import boto3
from botocore.client import ClientError

from shared.utils import update_references_table
from shared.utils.chrom_matching import (
    match_chromosome_name,
    CHROMOSOME_LENGTHS_MBP,
    ChromosomeNotFoundError,
)

s3_client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")

LOCAL_DIR = "/tmp"
REFERENCE_LOCATION = os.environ["REFERENCE_LOCATION"]
LOOKUP_REFERENCE = os.environ["LOOKUP_REFERENCE"]
CHR_HEADER = os.environ["CHR_HEADER"]
START_HEADER = os.environ["START_HEADER"]
END_HEADER = os.environ["END_HEADER"]


def chromosome_sort_key(chr_name):
    """Convert chromosome name to sortable tuple using existing chromosome matching."""
    try:
        # Normalize chromosome name using existing utility
        normalized = match_chromosome_name(chr_name)

        # Get the order from CHROMOSOME_LENGTHS_MBP which is an ordered dict
        chrom_order = list(CHROMOSOME_LENGTHS_MBP.keys())

        # Return tuple: (index in standard order, 0)
        # If not in standard chromosomes, sort alphabetically at the end
        if normalized in chrom_order:
            return (0, chrom_order.index(normalized))
        else:
            return (1, normalized)  # Non-standard chromosomes sort last

    except ChromosomeNotFoundError:
        # If chromosome name doesn't match any known pattern, sort at the very end
        return (2, chr_name.lower())


def update_lookup():
    staging_lookup_reference = f"staging/{LOOKUP_REFERENCE}"
    prod_lookup_reference = f"prod/{LOOKUP_REFERENCE}"

    try:
        s3_client.download_file(
            Bucket=REFERENCE_LOCATION,
            Key=staging_lookup_reference,
            Filename=os.path.join(LOCAL_DIR, LOOKUP_REFERENCE),
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404" or error_code == "NoSuchKey":
            raise FileNotFoundError(
                f"Lookup reference file not found in S3. "
                f"Expected location: s3://{REFERENCE_LOCATION}/{staging_lookup_reference}. "
                f"Please ensure the file has been uploaded to the staging folder."
            ) from e
        else:
            # Other S3 errors (permissions, network, etc.)
            raise RuntimeError(
                f"Failed to download file from S3 at s3://{REFERENCE_LOCATION}/{staging_lookup_reference}. "
                f"Error: {e.response['Error']['Message']}"
            ) from e

    try:
        with open(os.path.join(LOCAL_DIR, LOOKUP_REFERENCE), "r") as f:
            reader = csv.DictReader(f)

            # Validate headers exist
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")

            required_headers = {CHR_HEADER, START_HEADER, END_HEADER}
            missing_headers = required_headers - set(reader.fieldnames)
            if missing_headers:
                raise ValueError(
                    f"CSV file is missing required headers: {missing_headers}. "
                    f"Found headers: {reader.fieldnames}"
                )
            sorted_rows = []
            for row_num, row in enumerate(reader, start=2):
                try:
                    sorted_rows.append(
                        (
                            row[CHR_HEADER],
                            int(row[START_HEADER]),
                            int(row[END_HEADER]),
                            row,
                        )
                    )
                except ValueError as ve:
                    raise ValueError(
                        f"Invalid data in row {row_num}: {START_HEADER} and {END_HEADER} must be integers. "
                        f"Got {START_HEADER}='{row.get(START_HEADER)}', {END_HEADER}='{row.get(END_HEADER)}'"
                    ) from ve
                except KeyError as ke:
                    raise ValueError(
                        f"Missing required column value in row {row_num}: {ke}"
                    ) from ke

            # Sort with natural chromosome ordering
            sorted_rows.sort(key=lambda x: (chromosome_sort_key(x[0]), x[1], x[2]))
            sorted_rows = [row[3] for row in sorted_rows]  # Extract just the row dicts

    except (csv.Error, UnicodeDecodeError) as e:
        raise ValueError(f"File is not a valid CSV or has encoding issues: {e}") from e

    with open(os.path.join(LOCAL_DIR, LOOKUP_REFERENCE), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(sorted_rows)

    md5 = hashlib.md5()
    with open(os.path.join(LOCAL_DIR, LOOKUP_REFERENCE), "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)
    checksum = md5.hexdigest()

    s3_client.upload_file(
        Filename=os.path.join(LOCAL_DIR, LOOKUP_REFERENCE),
        Bucket=REFERENCE_LOCATION,
        Key=prod_lookup_reference,
    )
    update_references_table("lookup_hash", checksum)
    s3_client.delete_object(Bucket=REFERENCE_LOCATION, Key=staging_lookup_reference)
