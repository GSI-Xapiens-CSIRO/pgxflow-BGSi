import os
import subprocess

import boto3

from utils import download_remote_content, tar_extract, execute_subprocess, update_references_table

REFERENCE_BUCKET = os.environ["REFERENCE_BUCKET"]
PHARMCAT_REFERENCE_SUFFIXES = [
    ".vcf.bgz",
    ".vcf.bgz.csi",
    ".fna.bgz",
    ".fna.bgz.fai",
    ".fna.bgz.gzi",
    ".bed",
]

s3_client = boto3.client("s3")

def install_pharmcat_deps():
    command = "pip install -r preprocessor/requirements.txt"
    execute_subprocess(command)
    
def download_pharmcat_reference():
    command = f"cd preprocessor && python -c \"from preprocessor.utilities import prep_pharmcat_positions; prep_pharmcat_positions()\""
    execute_subprocess(command)

def update_pharmcat_preprocessor(pharmcat_version):
    pharmcat_preprocessor_url = f"https://github.com/PharmGKB/PharmCAT/releases/download/{pharmcat_version}/pharmcat-preprocessor-{pharmcat_version.lstrip("v")}.tar.gz"
    pharmcat_preprocessor_filename = "pharmcat-preprocessor.tar.gz"
    download_remote_content(pharmcat_preprocessor_url, pharmcat_preprocessor_filename) 
    tar_extract(pharmcat_preprocessor_filename)

    install_pharmcat_deps() 
    
    download_pharmcat_reference()
    
    local_pharmcat_reference_path = os.path.join(os.getcwd(), "preprocessor")
    local_reference_files = []
    for file in os.listdir(local_pharmcat_reference_path):
        if any(file.endswith(suffix) for suffix in PHARMCAT_REFERENCE_SUFFIXES):
            local_reference_files.append(file)
            
    response = s3_client.list_objects_v2(
        Bucket=REFERENCE_BUCKET,
        Prefix="preprocessor/",
    )
    existing_references = [obj["Key"] for obj in response.get("Contents", [])]

    if not set(local_reference_files).issubset(existing_references):

    for reference in local_reference_files:
        s3_client.upload_file(
            os.path.join(os.getcwd(), "preprocessor", reference),
            REFERENCE_BUCKET,
            f"preprocessor/{reference}",
        )
        
    update_references_table(
        
    )    


    
if __name__=="__main__":
    pharmcat_version = os.environ["PHARMCAT_VERSION"]
    update_pharmcat_preprocessor(pharmcat_version)

    