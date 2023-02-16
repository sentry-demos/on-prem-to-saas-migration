from dotenv import load_dotenv
from sentry import utils
from request import request
import os
import time

class Sentry:

    def __init__(self):
        load_dotenv()
        self.request_timeout = 5
        attributes = utils.get_attributes_from_dsn(os.environ["SAAS_PROJECT_DSN"])
        self.saas_options = {
            "endpoint" : os.environ["INGEST_SAAS_ENDPOINT"],
            "url" : os.environ["SAAS_URL"],
            "auth_token" : os.environ["SAAS_AUTH_TOKEN"],
            "org_name" : os.environ["SAAS_ORG_NAME"],
            "project_name" : os.environ["SAAS_PROJECT_NAME"],
            "sentry_key" : attributes.group(1),
            "project_key" : attributes.group(2)
        }

        self.on_prem_options = {
            "auth_token" : os.environ["ON_PREM_AUTH_TOKEN"],
            "url" : os.environ["ON_PREM_URL"],
            "org_name" : os.environ["ON_PREM_ORG_NAME"],
            "project_name" : os.environ["ON_PREM_PROJECT_NAME"]
        }

    def get_sass_project_name(self):
        return self.saas_options["project_name"]

    def get_on_prem_project_name(self):
        return self.on_prem_options["project_name"]

    def get_org_members(self):
        url = f'{self.saas_options["url"]}organizations/{self.saas_options["org_name"]}/members/'
        response = request(url, method = "GET")
        if response is not None and response.status_code == 200:
            return response.json()

        raise Exception(f'Could not fetch {self.saas_options["org_name"]} members')

    def get_issues_to_migrate(self):
        issue_list = os.environ["ISSUES"]
        if issue_list is not None:
            url = f'{self.on_prem_options["url"]}projects/{self.on_prem_options["org_name"]}/{self.on_prem_options["project_name"]}/issues/'
            response = request(url, method = "GET")
            if response is not None and response.status_code == 200:
                return utils.filter_issues(response.json(), issue_list)

        raise Exception(f'Could not get issues from on-prem {self.on_prem_options["project_name"]}')

    def get_latest_event_from_issue(self, id):
        if id is not None:
            url = f'{self.on_prem_options["url"]}issues/{id}/events/latest/'
            response = request(url, method = "GET")
            if response is not None and response.status_code == 200:
                return response.json()

        raise Exception(f'Could not get latest event from on-prem {self.on_prem_options["org_name"]} with issue ID {id}')

    def store_event(self, event):
        store_url = f'{self.saas_options["endpoint"]}{self.saas_options["project_key"]}/store/?sentry_key={self.saas_options["key"]}'
        response = request(store_url, method = "POST", payload = event)
        if response is not None and response.status_code == 200:
            return response.json()

        raise Exception(f'Could not store new event in SaaS instance')

    def update_issue(self, issue_id, payload):
        url = f'{self.saas_options["url"]}issues/{issue_id}/'
        response = request(url = url, method = "PUT", payload = payload)
        if response is not None and response.status_code == 200:
            return response.json()
        
        raise Exception(f'Could not update SaaS issue with ID {issue_id}')
    
    def get_issue_ids_from_events(self, eventIDs):
        time.sleep(10)
        failed_event_ids = []
        issues = []
        for eventID in eventIDs:
            url = f'{self.saas_options["url"]}projects/{self.saas_options["org_name"]}/{self.saas_options["project_name"]}/events/{eventID}/'
            response = request(url, method = "GET")
            start_time = time.time()
            if response is not None and response.status_code == 200:
                while "id" not in response.json():
                    time_delta = time.time() - start_time
                    response = request(url, method = "GET")

                    if time_delta > self.request_timeout:
                        failed_event_ids.append(eventID)
                        continue

            if "groupID" in response:
                issues.append({
                    "issue_id" : response["groupID"],
                    "event_id" : eventID
                    })

        return {
            "issues" : issues,
            "failed_event_ids" : failed_event_ids
        }



        


                

