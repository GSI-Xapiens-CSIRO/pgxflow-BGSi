import json

from version_checks import check_dbsnp_version
from dbsnp import update_dbsnp


def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")
    if event.get("source") == "aws.events":
        dbsnp_outdated, dbsnp_version = check_dbsnp_version()

        if dbsnp_outdated:
            update_dbsnp(dbsnp_version)
