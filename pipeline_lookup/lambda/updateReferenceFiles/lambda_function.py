import json

from version_checks import check_dbsnp_version, check_lookup_version
from dbsnp import update_dbsnp
from lookup import update_lookup


def lambda_handler(event, context):
    print(f"Event received: {json.dumps(event)}")
    if event.get("source") == "aws.events":
        dbsnp_outdated, dbsnp_version = check_dbsnp_version()
        lookup_outdated = check_lookup_version()

        if dbsnp_outdated:
            update_dbsnp(dbsnp_version)

        if lookup_outdated:
            update_lookup()
