import csv
import json
import os
import subprocess
from io import StringIO

from shared.utils import (
    LoggingClient,
    CheckedProcess,
    get_chromosome_mapping,
    match_chromosome_name,
    handle_failed_execution,
)

LOCAL_DIR = "/tmp"
DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]
PGXFLOW_BUCKET = os.environ["PGXFLOW_BUCKET"]
REFERENCE_BUCKET = os.environ["REFERENCE_BUCKET"]
DBSNP_REFERENCE = os.environ["DBSNP_REFERENCE"]
LOOKUP_REFERENCE = os.environ["LOOKUP_REFERENCE"]
PGXFLOW_LOOKUP_LAMBDA = os.environ["PGXFLOW_LOOKUP_LAMBDA"]
CHR_HEADER = os.environ["CHR_HEADER"]
START_HEADER = os.environ["START_HEADER"]
END_HEADER = os.environ["END_HEADER"]

lambda_client = LoggingClient("lambda")
s3_client = LoggingClient("s3")


def generate_target_region_files(source_chromosome_mapping):
    assert LOOKUP_REFERENCE.endswith(".csv")

    response = s3_client.get_object(
        Bucket=REFERENCE_BUCKET,
        Key=LOOKUP_REFERENCE,
    )
    body = response["Body"]
    csvfile = StringIO(body.read().decode("utf-8"))
    reader = csv.DictReader(csvfile)

    local_regions_path = os.path.join(LOCAL_DIR, "regions.txt")
    local_norm_regions_path = os.path.join(LOCAL_DIR, "norm_regions.txt")
    reversed_chromosome_mapping = {v: k for k, v in source_chromosome_mapping.items()}
    regions_exists = False
    with open(local_regions_path, "w") as f, open(local_norm_regions_path, "w") as n_f:
        for row in reader:
            normalised_chr = match_chromosome_name(row[CHR_HEADER])
            if normalised_chr not in reversed_chromosome_mapping:
                continue
            regions_exists = True
            chr = reversed_chromosome_mapping[normalised_chr]
            start = row[START_HEADER]
            end = row[END_HEADER]
            f.write(f"{chr}\t{start}\t{end}\n")
            n_f.write(f"{normalised_chr}\t{start}\t{end}\n")

    return local_regions_path, local_norm_regions_path, regions_exists


def filter_and_rename_chrs(
    source_vcf_s3_uri, source_chromosome_mapping, local_regions_path, regions_exists
):
    local_chrs_path = os.path.join(LOCAL_DIR, "rename_chrs.txt")
    with open(local_chrs_path, "w") as f:
        for orig, normalised in source_chromosome_mapping.items():
            f.write(f"{orig}\t{normalised}\n")
    try:
        local_renamed_vcf_path = os.path.join(LOCAL_DIR, "renamed.vcf.gz")
        if regions_exists:
            rename_vcf_args = [
                "bcftools",
                "annotate",
                "--rename-chrs",
                local_chrs_path,
                "-R",
                local_regions_path,
                source_vcf_s3_uri,
                "-Oz",
                "-o",
                local_renamed_vcf_path,
            ]
        else:
            rename_vcf_args = [
                "bcftools",
                "annotate",
                "--rename-chrs",
                local_chrs_path,
                "-i", "0",
                source_vcf_s3_uri,
                "-Oz",
                "-o",
                local_renamed_vcf_path,
            ]
        rename_vcf_process = CheckedProcess(rename_vcf_args)
        rename_vcf_process.check()

        local_renamed_vcf_index_path = f"{local_renamed_vcf_path}.csi"
        index_renamed_vcf_args = ["bcftools", "index", local_renamed_vcf_path]
        index_renamed_vcf_process = CheckedProcess(index_renamed_vcf_args)
        index_renamed_vcf_process.check()

        return local_renamed_vcf_path, local_renamed_vcf_index_path 
    except subprocess.CalledProcessError as e:
        print(
            f"cmd {e.cmd} returned non-zero error code {e.returncode}. stderr:\n{e.stderr}"
        )


def annotate_rsids(local_renamed_vcf_path, dbsnp_vcf_s3_uri, local_norm_regions_path):
    try:
        local_annotated_vcf_path = os.path.join(LOCAL_DIR, "annotated.vcf.gz")
        annotate_vcf_args = [
            "bcftools",
            "annotate",
            "--annotations",
            dbsnp_vcf_s3_uri,
            "--columns",
            "ID",
            "-R",
            local_norm_regions_path,
            local_renamed_vcf_path,
            "-Oz",
            "-o",
            local_annotated_vcf_path,
        ]
        annotate_vcf_process = CheckedProcess(annotate_vcf_args)
        annotate_vcf_process.check()

        local_annotated_vcf_index_path = f"{local_annotated_vcf_path}.csi"
        index_annotated_vcf_args = ["bcftools", "index", local_annotated_vcf_path]
        index_annotated_vcf_process = CheckedProcess(index_annotated_vcf_args)
        index_annotated_vcf_process.check()

        return local_annotated_vcf_path, local_annotated_vcf_index_path
    except subprocess.CalledProcessError as e:
        print(
            f"cmd {e.cmd} returned non-zero error code {e.returncode}. stderr:\n{e.stderr}"
        )


def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")
    message = json.loads(event["Records"][0]["Sns"]["Message"])
    request_id = message["requestId"]
    source_vcf_key = message["sourceVcfKey"]
    project = message["projectName"]

    source_vcf_s3_uri = f"s3://{DPORTAL_BUCKET}/{source_vcf_key}"
    dbsnp_vcf_s3_uri = f"s3://{REFERENCE_BUCKET}/{DBSNP_REFERENCE}"

    try:
        source_chromosome_mapping = get_chromosome_mapping(source_vcf_s3_uri)

        local_regions_path, local_norm_regions_path, regions_exists = generate_target_region_files(
            source_chromosome_mapping
        )

        local_renamed_vcf_path, local_renamed_vcf_index_path = filter_and_rename_chrs(
            source_vcf_s3_uri, source_chromosome_mapping, local_regions_path, regions_exists
        )

        if regions_exists:
            local_annotated_vcf_path, local_annotated_vcf_index_path = annotate_rsids(
                local_renamed_vcf_path, dbsnp_vcf_s3_uri, local_norm_regions_path
            )
            os.remove(local_renamed_vcf_path)
        else:
            local_annotated_vcf_path = local_renamed_vcf_path
            local_annotated_vcf_index_path = local_renamed_vcf_index_path

        annotated_vcf_key = f"annotated_{request_id}.vcf.gz"
        s3_client.upload_file(
            Bucket=PGXFLOW_BUCKET,
            Key=annotated_vcf_key,
            Filename=local_annotated_vcf_path,
        )
        os.remove(local_annotated_vcf_path)

        s3_client.upload_file(
            Bucket=PGXFLOW_BUCKET,
            Key=f"{annotated_vcf_key}.csi",
            Filename=local_annotated_vcf_index_path,
        )
        os.remove(local_annotated_vcf_index_path)

        annotated_vcf_location = f"s3://{PGXFLOW_BUCKET}/{annotated_vcf_key}"

        lambda_client.invoke(
            FunctionName=PGXFLOW_LOOKUP_LAMBDA,
            InvocationType="Event",
            Payload=json.dumps(
                {
                    "requestId": request_id,
                    "projectName": project,
                    "dbsnpAnnotatedVcfLocation": annotated_vcf_location,
                }
            ),
        )
    except Exception as e:
        handle_failed_execution(request_id, e)
