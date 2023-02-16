from request import request
from processor import normalizeIssue
from dotenv import load_dotenv
from logger import customLogger
from sentry import Sentry
from sentry import utils
import members
import os
import time

class Main:

    def init(self):
        try:
            self.sentry = Sentry.Sentry()
            self.logger = customLogger.Logger()
            self.memberObj = members.Members()
            
            self.memberObj.populate(self.sentry.get_org_members())
            issues = self.sentry.get_issues_to_migrate()
            if issues is None or len(issues) == 0:
                raise Exception("Issues list is empty")
            
            self.logger.debug(f'Ready to migrate {len(issues)} issues from {self.sentry.get_on_prem_project_name()} to {self.sentry.get_sass_project_name()}')
            metadata = self.create_issues_on_sass(issues)
            self.update_issues(metadata)

        except Exception as e:
            self.logger.critical(str(e))

    def update_issues(self, metadata):
        event_ids = [data["event_id"] for data in metadata]
        response = self.sentry.get_issue_ids_from_events(event_ids)
        if len(response["failed_event_ids"]) > 0:
            self.logger.warn(f'Could not find events with IDs {print(response["failed_event_ids"])} in {self.sentry.get_sass_project_name()} SaaS')
        
        if len(response["issues"]) == 0:
            self.logger.warn(f'Could not find new IDs in {self.sentry.get_sass_project_name()} SaaS')
            return

        for issue in response["issues"]:
            issue_id = issue["issue_id"]
            event_id = issue["event_id"]
            issue_metadata = utils.get_issue_metadata(event_id, metadata)

            if issue_metadata is None:
                self.logger.warn(f'Could not update SaaS issue with ID {issue_id} (Issue created but not updated) - Skipping...')
                continue
            
            response = self.sentry.update_issue(issue_id, issue_metadata)
            if "id" in response:
                self.logger.info(f'SaaS Issue with ID {issue_id} updated succesfully!')
            else:
                self.logger.error(f'SaaS Issue with ID {issue_id} could not be updated')

    def create_issues_on_sass(self, issues):
        metadata = []
        for issue in issues:
            if issue["id"] is not None:
                self.logger.debug(f'Fetching data from issue with ID {issue["id"]}')
                if "level" in issue:
                    issueData = {
                        "level" : issue["level"] or "error"
                    }
                else:
                    self.logger.warn("No level attribute found in issue data object")

                # 2) Get the latest event for each of the issues
                latest_event = self.sentry.get_latest_event_from_issue(issue["id"])

                # 3) Normalize and construct payload to send to SAAS
                payload = normalizeIssue(latest_event, issueData)
                if payload["exception"] is None:
                    self.logger.error(f'Could not migrate issue with ID {issue["id"]} - Skipping...')
                    continue
                
                self.logger.info(f'Data normalized correctly for Issue with ID {issue["id"]}')

                eventResponse = self.sentry.store_event(payload)

                if eventResponse is None or "id" not in eventResponse or eventResponse["id"] is None:
                    self.logger.error(f'Could not store new event in SaaS instance - Skipping...')
                    continue

                issue_metadata = {}

                if "firstSeen" in issue and issue["firstSeen"] is not None:
                    issue_metadata["firstSeen"] = issue["firstSeen"]
                else:
                    self.logger.warn(f'firstSeen property could not be added to SaaS issue with ID {issue["id"]}')
                
                if "lastSeen" in issue and issue["lastSeen"] is not None:
                    issue_metadata["lastSeen"] = issue["lastSeen"]
                else:
                    self.logger.warn(f'lastSeen property could not be added to SaaS issue with ID {issue["id"]}')
                
                if "assignedTo" in issue and issue["assignedTo"] is not None:
                    if "email" not in issue["assignedTo"] or issue["assignedTo"]["email"] is None:
                        self.logger.warn(f'Issue assignee\'s email from on-prem issue with ID {issue["id"]} was not found')
                    else:
                        userEmail = issue["assignedTo"]["email"]
                        userId = self.memberObj.getUserID(userEmail)
                        if userId is not None:
                            issue_metadata["assignedBy"] = "assignee_selector"
                            issue_metadata["assignedTo"] = "user:" + userId
                        else:
                            self.logger.warn(f'Could not find the ID of user with email {userEmail} - Skipping issue assignee')
                else:
                    self.logger.warn(f'On-prem issue with ID {issue["id"]} does not contain property "assignedTo" - Skipping issue assignee')


                
                self.logger.info(f'Issue successfully created in SaaS instance with ID {eventResponse["id"]}')
                obj = {
                    "event_id" : eventResponse["id"],
                    "issue_metadata" : issue_metadata
                }
                metadata.append(obj)

            else:
                raise Exception("Issue ID not found")

        return metadata

if __name__ == "__main__":
    Main.init()

    #TODO: report of failed issue IDs
    #TODO: Implement functionality to migrate DIF/Sourcemaps?

    # Input a timeframe to fetch the issues
    # dry run mode - dont create the issue on SaaS
