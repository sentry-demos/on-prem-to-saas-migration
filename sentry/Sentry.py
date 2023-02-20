from dotenv import load_dotenv
from sentry import utils
from request import request
import dryable
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

    @dryable.Dryable()
    def store_event(self, event):
        store_url = f'{self.saas_options["endpoint"]}{self.saas_options["project_key"]}/store/?sentry_key={self.saas_options["sentry_key"]}'
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
                data = response.json()
                while "id" not in data:
                    time_delta = time.time() - start_time
                    response = request(url, method = "GET")
                    data = response.json()

                    if time_delta > self.request_timeout:
                        failed_event_ids.append(eventID)
                        continue

                if "groupID" in data:
                    issues.append({
                        "issue_id" : data["groupID"],
                        "event_id" : eventID
                    })

        return {
            "issues" : issues,
            "failed_event_ids" : failed_event_ids
        }

    def get_integration_data(self, integration_name, issue_id):
        url = f'{self.on_prem_options["url"]}groups/{issue_id}/integrations/'
        response = request(url, method = "GET")
        if response is not None and response.status_code == 200:
            return self.process_integrations_response(response.json(), integration_name)
        
        raise Exception(f'Could not fetch integrations for issue with ID {issue_id}')
    
    def process_integrations_response(self, integrations, integration_name):
        keys = {
            "domain_name" : None,
            "external_issue" : None
        }
        for integration in integrations:
            if "name" in integration and integration["name"] == integration_name:
                if len(integration["externalIssues"]) > 0:
                    keys["domain_name"] = integration["domainName"] or None
                    keys["external_issue"] = integration["externalIssues"][0]["key"] or None
        return keys

    def get_saas_integration_id(self, integration_name, identifer):
        url = f'{self.saas_options["url"]}organizations/{self.saas_options["org_name"]}/integrations/?includeConfig=0'
        response = request(url, method = "GET")
        if response is not None and response.status_code in [200,201]:
            data = response.json()
            for integration in data:
                if integration["name"] == integration_name and integration[identifer["key"]] == identifer["value"]:
                    return integration["id"] or None

        raise Exception(f'Could not get integration id for {integration_name} in SaaS {self.saas_options["org_name"]}')

    def update_external_issues(self, issue_id, integration_data, integration_id):
        url = f'{self.saas_options["url"]}groups/{issue_id}/integrations/{integration_id}/'
        payload = {
            "externalIssue" : integration_data["external_issue"]
        }
        response = request(url, method = "PUT", payload = payload)
        if response is not None and response.status_code in [200,201]:
            return response.json()

        raise Exception(f'Could not update SaaS issue with ID {issue_id} with external issue with ID {integration_data["external_issue"]}')




        


                

