import subprocess
import os
import boto3
import json
from uuid import uuid4
from shared.apiutils import bad_request, bundle_response
from shared.utils import generate_presigned_get_url
from shared.auth import require_permission, PermissionError


s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

BUCKET_NAME = os.environ["FILE_LOCATION"]
RESULT_DURATION = int(os.environ["RESULT_DURATION"])

input_dir = "/tmp/input"
output_dir = "/tmp/output"
os.makedirs(input_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

mapping_formula = {
    "qc_hc": {
        "formula": "QUAL ~ 1",
        "title": "Variant Quality Score Distributions",
        "image_title": "QUAL Score Histogram",
        "identifier": "qual-score-histogram",
    },
    "gq": {
        "formula": "GQs ~ 1",
        "title": "Genotype Quality",
        "image_title": f"GQ Score Histogram",
        "identifier": "gq-score-histogram",
        "additional_args": [
            "--macro",
            "/var/task/gq_monkey_patch.py",
        ],
    },
    "low_var": {
        "formula": "QUAL ~ DPs",
        "title": "Low Variant Flagging",
        "image_title": f"QUAL Score vs DP Scatterplot",
        "identifier": "qual-score-vs-dp-scatterplot",
    },
    "alle_freq": {
        "formula": "AAF ~ CONTIG",
        "title": "Allele Frequency",
        "image_title": f"Allele Frequency",
        "identifier": "allele-frequency",
        "additional_args": [
            "--macro",
            "/var/task/violin_monkey_patch.py",
        ],
    },
    "snp_pass": {
        "formula": "COUNT(1, VARTYPE[snp]) ~ SUBST[A>T,A>G,A>C,T>A,T>G,T>C,G>A,G>T,G>C,C>A,C>T,C>G]",
        "title": "Only with SNP's Pass all filters",
        "image_title": f"Number of substitutions of SNPs (passed)",
        "identifier": "number-of-substitutions-of-snps-passed",
        "additional_args": ["--passed"],
    },
}


def get_result_type(file_name):
    for key, value in mapping_formula.items():
        identifier = value["identifier"]
        if identifier in file_name:
            return key, value["title"]


def get_formula_and_title(key, vcf_file):
    formula = mapping_formula.get(key, False)
    if not formula:
        return False, False
    return formula["formula"], f"{formula["image_title"]} ({vcf_file})"


def classify_error(stderr_msg):
    stderr_msg = stderr_msg.decode("utf-8", errors="ignore")
    if not stderr_msg:
        return "vcfstat_failed", "No stderr output."
    msg_lower = stderr_msg.lower()
    if (
        "keyerror" in msg_lower
        or "field not found" in msg_lower
        or "not present" in msg_lower
    ):
        return "no_data", stderr_msg.strip()
    elif "error" in msg_lower or "failed" in msg_lower:
        return "vcfstat_failed", stderr_msg.strip()
    else:
        return "other_error", stderr_msg.strip()


def lambda_handler(event, context):

    try:
        # 🔐 Permission check
        require_permission(event, "generate_report.read")

        event_body = event.get("body")

        if not event_body:
            return bad_request("No body sent with request.")

        body_dict = json.loads(event_body)
        project_name = body_dict["projectName"]
        file_name = body_dict["fileName"]
        key = body_dict["key"]

        input_vcf_file = f"projects/{project_name}/project-files/{file_name}"
        local_vcf_path = os.path.join(input_dir, os.path.basename(file_name))

        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix=f"projects/{project_name}/qc-figures/{file_name}/",
        )

        contents = response and "Contents" in response
        image_files = contents and [obj["Key"] for obj in response["Contents"]]

        formula_details = mapping_formula.get(key, {})
        if not formula_details:
            return bundle_response(
                400,
                {
                    "message": "Formula not found. Please check key parameter.",
                    "images": {},
                },
            )

        identifier = formula_details["identifier"]

        # ===============================
        # IF IMAGE EXISTS
        # ===============================
        if image_files and any(identifier in image_file for image_file in image_files):

            images = {}

            for image_file in image_files:
                image_file_name = image_file.split("/")[-1]

                if identifier in image_file_name:
                    output_vcfstats_file = (
                        f"projects/{project_name}/qc-figures/{file_name}/{image_file_name}"
                    )

                    result_url = generate_presigned_get_url(
                        BUCKET_NAME,
                        output_vcfstats_file,
                        RESULT_DURATION,
                    )

                    key_name, title = get_result_type(image_file_name)

                    images[key_name] = {
                        "title": title,
                        "url": result_url,
                    }

            return bundle_response(
                200,
                {
                    "message": "Image fetched successfully",
                    "images": images,
                },
            )

        # ===============================
        # GENERATE IMAGE
        # ===============================

        s3_resource.Bucket(BUCKET_NAME).download_file(
            input_vcf_file, local_vcf_path
        )

        formula, image_title = get_formula_and_title(key, file_name)
        if not formula:
            return bundle_response(
                400,
                {
                    "message": "Formula not found. Please check key parameter.",
                    "images": {},
                },
            )

        output_image = os.path.join(output_dir, f"{uuid4()}.png")

        vcfstats_params = [
            "vcfstats",
            "--vcf",
            local_vcf_path,
            "--outdir",
            output_dir,
            "--formula",
            formula,
            "--title",
            image_title,
        ] + formula_details.get("additional_args", [])

        subprocess.run(
            vcfstats_params,
            check=True,
            stderr=subprocess.PIPE,
            cwd="/tmp",
        )

        images = {}

        for image_file_name in os.listdir(output_dir):

            image_path = os.path.join(output_dir, image_file_name)

            output_vcfstats_file = (
                f"projects/{project_name}/qc-figures/{file_name}/{image_file_name}"
            )

            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=output_vcfstats_file,
                Body=image_data,
                ContentType="image/png",
            )

            result_url = generate_presigned_get_url(
                BUCKET_NAME,
                output_vcfstats_file,
                RESULT_DURATION,
            )

            key_name, title = get_result_type(image_file_name)

            images[key_name] = {
                "title": title,
                "url": result_url,
            }

            os.unlink(image_path)

        if os.path.isfile(local_vcf_path):
            os.unlink(local_vcf_path)

        return bundle_response(
            200,
            {
                "message": "Image generated and uploaded successfully",
                "images": images,
            },
        )

    except PermissionError as e:
        return bundle_response(
            403,
            {
                "status": "error",
                "message": str(e),
            },
        )

    except subprocess.CalledProcessError as e:
        error_type, message = classify_error(e.stderr)
        return bundle_response(
            500,
            {
                "status": "error",
                "error_type": error_type,
                "message": message,
            },
        )

    except Exception as e:
        return bundle_response(
            500,
            {
                "status": "error",
                "error_type": "other_error",
                "message": f"Error generating image: {str(e)}",
            },
        )