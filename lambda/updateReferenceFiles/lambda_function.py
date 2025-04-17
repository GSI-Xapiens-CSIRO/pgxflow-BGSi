from pharmcat_startup import update_pharmcat_preprocessor
from version_checks import check_pharmcat_version

def lambda_handler(event, _):
    pharmcat_outdated, pharmcat_version = check_pharmcat_version() 
    
    if pharmcat_outdated:
        print(f"Pharmcat version is outdated. Updating to {pharmcat_version}.")
        return
        update_pharmcat_preprocessor(pharmcat_version)
