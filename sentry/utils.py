import re

def get_attributes_from_dsn(dsn):
    if dsn is not None:
        dsn_string = re.search(".*?\/\/(.*)@.*\/(.*)", dsn)
        if dsn_string is not None:
            if len(dsn_string.groups()) == 2:
                return dsn_string
    raise Exception("Could no retrieve project key")

def filter_issues(issues, issueIDs):
    issues = []
    for issue in issues:
        if issue["id"] is not None and issue["id"] in issueIDs:
            issues.append(issue)
    return issues

def get_issue_metadata(event_id, metadata):
    for data in metadata:
        if data["event_id"] == event_id:
            return data["issue_metadata"]
    return None