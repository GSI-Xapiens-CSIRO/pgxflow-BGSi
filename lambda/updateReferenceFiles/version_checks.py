import json

from utils import fetch_remote_content, query_references_table

PHARMCAT_VERSION_URL = "https://api.github.com/repos/PharmGKB/PharmCAT/releases/latest"

def check_pharmcat_version():
    id = "pharmcat_version"
    local_pharmcat_version = query_references_table(id)
    pharmcat_metadata = fetch_remote_content(PHARMCAT_VERSION_URL)
    remote_pharmcat_version = json.loads(pharmcat_metadata)["tag_name"]
    return [remote_pharmcat_version != local_pharmcat_version, remote_pharmcat_version]
    