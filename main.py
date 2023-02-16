from request import request
from processor import normalizeIssue
from dotenv import load_dotenv
from logger import customLogger
import members
import os
import time

LOGGER = None
TIMEOUT = 10

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

def processIssuesResponse(issues, memberObj, logger):
    for issue in issues:
        if issue["id"] is not None:
            logger.debug(f'Fetching data from issue with ID {issue["id"]}')
            # 2) Get the latest event for each of the issues
            url = get_on_prem_org_base_url() + "issues/" + issue["id"] + "/events/latest/"
            details = request(url = url, method = "GET")
            logger.info(f'Last event from issue with ID {issue["id"]} fetched succesfully')
            
            if "level" in issue:
                issueData = {
                    "level" : issue["level"] or "error"
                }
            else:
                logger.warn("No level attribute found in issue data object")

            # 3) Normalize and construct payload to send to SASS
            payload = normalizeIssue(details.json(), issueData)
            print(payload)
            if payload["exception"] is None:
                logger.error(f'Could not migrate issue with ID {issue["id"]} - Skipping...')
                continue
            
            logger.info(f'Data normalized correctly for Issue with ID {issue["id"]}')

            eventUrl = get_store_endpoint()
            eventResponse = request(url = eventUrl, method = "POST", payload = payload)
            eventResponseJSON = eventResponse.json()
            if eventResponseJSON is None or "id" not in eventResponseJSON or eventResponseJSON["id"] is None:
                logger.error(f'Could not store new event in SaaS instance - Skipping...')
                continue
            
            logger.info(f'Issue successfully created in SaaS instance with ID {eventResponseJSON["id"]}')

            # 4) Get the Issue linked to the event created - event data might not be available right away
            issueFound = False
            getIssueResponseJSON = None
            start_time = time.time()

            ############
            while not issueFound:
                time_delta = time.time() - start_time
                getIssueUrl = constructIssueUrl(eventResponseJSON["id"])
                getIssueResponse = request(url = getIssueUrl, method = "GET")
                getIssueResponseJSON = getIssueResponse.json()
                if "id" in getIssueResponseJSON:
                    issueFound = True
                '''
                if time_delta > TIMEOUT:
                    logger.error("Timeout reached, could not fetch newly created SaaS Issue data - Skipping Issue update operation")
                    continue'''
            ###########

            if "id" not in getIssueResponseJSON:
                logger.error("SaaS Issue not created successfully - Skipping Issue update operation")
                continue
            
            logger.debug(f'New SaaS Issue found with ID {getIssueResponseJSON["groupID"]}')
                
            # 5) Get the Issue ID of the event created
            issuePayload = {}
            issueID = getIssueResponseJSON["groupID"]

            if "firstSeen" in issue and issue["firstSeen"] is not None:
                issuePayload["firstSeen"] = issue["firstSeen"]
            else:
                logger.warn(f'firstSeen property could not be added to SaaS issue with ID {issueID}')
            
            if "lastSeen" in issue and issue["lastSeen"] is not None:
                issuePayload["lastSeen"] = issue["lastSeen"]
            else:
                logger.warn(f'lastSeen property could not be added to SaaS issue with ID {issueID}')

            #if "annotations" in issue and issue["annotations"] is not None:
             #   issuePayload["annotations"] = issue["annotations"]

            # 6) Assign member to an issue based on rules from on-prem
            if "assignedTo" in issue and issue["assignedTo"] is not None:
                if "email" not in issue["assignedTo"] or issue["assignedTo"]["email"] is None:
                    logger.warn(f'Issue assignee\'s email from on-prem issue with ID {issue["id"]} was not found')
                else:
                    userEmail = issue["assignedTo"]["email"]
                    #print(userEmail)
                    userId = memberObj.getUserID(userEmail)
                    #print(userId)
                    #if userId is not None:
                        #issuePayload["assignedBy"] = "assignee_selector"
                        #issuePayload["assignedTo"] = "user:" + userId
                    #else:
                        #logger.warn(f'Could not find the ID of user with email {userEmail} - Skipping issue assignee')
            else:
                logger.warn(f'On-prem issue with ID {issue["id"]} does not contain property "assignedTo" - Skipping issue assignee')
                    
            
            if len(issuePayload) != 0 and issueID is not None:
                issueUrl = get_sass_org_base_url() + "issues/" + issueID + "/"
                issueResponse = request(url = issueUrl, method = "PUT", payload = issuePayload)
                issueResponseJSON = issueResponse.json()
                if issueResponseJSON is not None and "id" in issueResponseJSON:
                    logger.info(f'SaaS Issue with ID {issueID} updated succesfully!')
                else:
                    logger.error(f'SaaS Issue with ID {issueID} could not be updated')
            else:
                logger.warn(f'Could not update SaaS issue with ID {issueID} (Issue created but not updated) - Skipping...')
        else:
            raise Exception("Issue ID not found")

def get_on_prem_org_base_url():
    return os.environ["ON_PREM_URL"]

def get_sass_org_base_url():
    return os.environ["SASS_URL"]

def constructIssueUrl(eventId):
    base_url = get_sass_org_base_url()
    url = base_url + "projects/" + os.environ["SASS_ORG_NAME"] + "/" + os.environ["SASS_PROJECT_NAME"] + "/events/" + eventId + "/"
    return url

def get_store_endpoint():
    return os.environ["INGEST_SASS_ENDPOINT"] + os.environ["SASS_PROJECT_KEY"] +  "/store/?sentry_key=" + os.environ["SASS_SENTRY_KEY"]

def main():
    try:
        LOGGER = customLogger.Logger()
        load_dotenv()
        memberObj = members.Members()
        getOrgMembers(memberObj)
        issues = os.environ["ISSUES"]
        if issues is not None:
            li = list(issues.split(","))

        # 1) Get on prem issues to migrate
        url = get_on_prem_org_base_url() + "projects/sentry/" + os.environ["ON_PREM_PROJECT_NAME"] + "/issues/"
        response = request(url = url, method = "GET")
        filteredIssues = filterIssues(response.json(), li)
        LOGGER.debug(f'READY TO MIGRATE {len(filteredIssues)} issues from {os.environ["ON_PREM_PROJECT_NAME"]} to {os.environ["SASS_PROJECT_NAME"]}')
        processIssuesResponse(filteredIssues, memberObj, LOGGER)

    except Exception as e:
        LOGGER.critical(str(e))


if __name__ == "__main__":
    main()

    #TODO: report of failed issue IDs
    #TODO: Implement functionality to migrate DIF/Sourcemaps?

    # Input a timeframe to fetch the issues
    # dry run mode - dont create the issue on SaaS
    # batch issues - 2 scripts to 1. Create issues and 2. Update Issues
