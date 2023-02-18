import re

def get_attributes_from_dsn(dsn):
    if dsn is not None:
        dsn_string = re.search(".*?\/\/(.*)@.*\/(.*)", dsn)
        if dsn_string is not None:
            if len(dsn_string.groups()) == 2:
                return dsn_string
    raise Exception("Could no retrieve project key")

def filter_issues(issues, issueIDs):
    filtered_issues = []
    for issue in issues:
        if issue["id"] is not None and issue["id"] in issueIDs:
            filtered_issues.append(issue)
    return filtered_issues

def get_issue_metadata(event_id, metadata):
    for data in metadata:
        if data["event_id"] == event_id:
            return data["issue_metadata"]
    return None

def get_dry_run(args):
    if len(args) > 1:
        if "--dry-run" in args:
            return True
        else:
            raise Exception("Invalid argument : To dry-run script, please specify the '--dry-run' argument")
    return False

def replace_all(str, chars, new_val = ""):
    for char in chars:
        str = str.replace(char, new_val)
    return str