from request import request
from processor import normalizeIssue
from dotenv import load_dotenv
import members
import os

def getOrgMembers(memberObj):
    url = get_sass_org_base_url() + "organizations/" + os.environ["SASS_ORG_NAME"] + "/members/"
    response = request(url = url, method = "GET")
    memberObj.populate(response.json())

def filterIssues(response, issueIDs):
    issues = []
    for issue in response:
        if issue["id"] is not None and issue["id"] in issueIDs:
            issues.append(issue)
    return issues

def processIssuesResponse(issues, memberObj):
    for issue in issues:
        if issue["id"] is not None:
            # 2) Get the latest event for each of the issues
            url = get_on_prem_org_base_url() + "issues/" + issue["id"] + "/events/latest/"
            details = request(url = url, method = "GET")
            issueData = {
                "level" : issue["level"] or "error"
            }
            # 3) Normalize and construct payload to send to SASS
            payload = normalizeIssue(details.json(), issueData)
            eventUrl = get_store_endpoint()
            eventResponse = request(url = eventUrl, method = "POST", payload = payload)
            eventResponseJSON = eventResponse.json()

            # 4) Get the Issue linked to the event created - event data might not be available right away
            issueFound = False
            getIssueResponseJSON = None
            while not issueFound:
                getIssueUrl = constructIssueUrl(eventResponseJSON["id"])
                getIssueResponse = request(url = getIssueUrl, method = "GET")
                getIssueResponseJSON = getIssueResponse.json()
                if "id" in getIssueResponseJSON:
                    issueFound = True
                

            # 5) Get the Issue ID of the event created
            issueID = None
            if "id" in getIssueResponseJSON:
                issueID = getIssueResponseJSON["groupID"]

            # 6) Assign member to an issue based on rules from on-prem
            if "assignedTo" in issue:
                userEmail = issue["assignedTo"]["email"]
                userId = memberObj.getUserID(userEmail)
                if userId is not None:
                    assignPayload = {
                        "assignedBy" : "assignee_selector",
                        "assignedTo" : "user:" + userId
                    }
                    assignUrl = get_sass_org_base_url() + "issues/" + issueID + "/"
                    assignResponse = request(url = assignUrl, method = "PUT", payload = assignPayload)
                    print("ASSIGN RESPONSE-----------------")
                    print(assignResponse.json())

def get_on_prem_org_base_url():
    return os.environ["ON_PREM_URL"]

def get_sass_org_base_url():
    return os.environ["SASS_URL"]

def constructIssueUrl(eventId):
    base_url = get_sass_org_base_url()
    url = base_url + "projects/" + os.environ["SASS_ORG_NAME"] + "/" + os.environ["SASS_PROJECT_NAME"] + "/events/" + eventId + "/"
    return url

def get_store_endpoint():
    return os.environ["INGEST_SASS_ENDPOINT"] + "/store/?sentry_key=" + os.environ["SASS_SENTRY_KEY"]

def main():
    load_dotenv()
    memberObj = members.Members()
    getOrgMembers(memberObj)
    issues = os.environ["ISSUES"]
    if issues is not None:
        li = list(issues.split(","))
    # 1) Get on prem issues to migrate
    url = get_on_prem_org_base_url() + "projects/sentry/react-web/issues/"
    response = request(url = url, method = "GET")
    filteredIssues = filterIssues(response.json(), li)
    processIssuesResponse(filteredIssues, memberObj)

if __name__ == "__main__":
    main()
