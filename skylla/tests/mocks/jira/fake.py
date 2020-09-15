import datetime
import json
import logging
import os
import re
from urllib.parse import urlparse

import jira
import pytz
import requests

from .idtree import IdTree

logger = logging.getLogger(__name__)


def jurl(path):
    return f"https+mock://jira/rest/api/2/{path}"


def wawnow(tz=pytz.timezone("Europe/Warsaw")):
    return datetime.datetime.now(tz)


def dict_select(elements, select):
    pairs = tuple(select.items())
    for ele in elements:
        for key, val in pairs:
            if ele.get(key) != val:
                break
        else:
            yield ele


class FakeJiraAdapter(requests.adapters.BaseAdapter):

    re_api_prefix = re.compile("^/rest/api/(2|latest)/")

    def __init__(self, jira_data):
        self.jira_data = jira_data

    def send(
        self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None
    ):
        response = requests.models.Response()
        logger.debug("%s %s", request.method, request.path_url)
        try:
            method = getattr(self, f"handle_{request.method.lower()}")
        except AttributeError:
            response.status_code = 405
            response.reason = f"Not Implemented: {request.method}"
            return response
        request.urlobj = urlparse(request.url)
        request.jira_path = self.re_api_prefix.sub("", request.urlobj.path)
        status_code, content = method(request)
        response.status_code = status_code
        response._content = content.encode("utf-8")
        return response

    def issue_resource_get(self, issue, resource):
        try:
            issue_data = self.jira_data.recursive_get(["issue", issue])
        except KeyError:
            return (404, f"Not Found: {issue}")
        try:
            res = issue_data["fields"][resource]
        except KeyError:
            return (404, f"Not Found: {issue}/{resource}")
        return (200, json.dumps(res))

    def handle_get(self, request):
        if re.match("issue/.*/transitions", request.jira_path):
            data = self.jira_data.path_get("_methods/REL/transitions")
            return (200, json.dumps(data))
        if (m := re.match("issue/(.*)/(.*)", request.jira_path)) :
            return self.issue_resource_get(m.group(1), m.group(2))
        try:
            data = self.jira_data.path_get(request.jira_path)
            return (200, json.dumps(data))
        except KeyError:
            return (404, f"Not Found: {request.jira_path}")

    def handle_post(self, request):
        if (m := re.match("issue/(.*)/transitions", request.jira_path)) :
            return self.transition_issue(m.group(1), request)
        elif (m := re.match("issue/(.*)/comment", request.jira_path)) :
            issue = m.group(1)
            iss_dct = self.jira_data.path_get(f"issue/{issue}")
            iss_dct["fields"]["comment"]["comments"].append(json.loads(request.body))
            return (201, "")
        else:
            return (404, f"Not Found: {request.jira_path}")

    def handle_put(self, request):
        if (m := re.match("issue/(.*)/assignee", request.jira_path)) :
            return self.assign_issue(m.group(1), request)
        try:
            iss_dct = self.jira_data.path_get(request.jira_path)
        except KeyError:
            return (404, f"Not Found: {request.jira_path}")
        indata = json.loads(request.body)
        iss_dct['fields'].update(indata['fields'])
        return (204, "")

    def assign_issue(self, issue, request):
        iss_dct = self.jira_data.path_get(f"issue/{issue}")
        if not iss_dct:
            return (404, "Issue missing")
        indata = json.loads(request.body)
        if indata == {"name": None}:
            iss_dct["fields"]["assignee"] = None
        else:
            users = self.jira_data.path_get("user")
            selected = list(dict_select(users, indata))
            if not selected:
                return (400, "User not found")
            assert len(selected) == 1
            iss_dct["fields"]["assignee"] = selected[0]
        return (204, "")

    def transition_issue(self, issue, request):
        trans = self.jira_data.path_get("_methods/REL/transitions")["transitions"]
        indata = json.loads(request.body)
        selected = list(dict_select(trans, indata["transition"]))
        if not selected:
            return (400, "No transition")
        assert len(selected) == 1
        new_status = selected[0]["to"]
        iss_dct = self.jira_data.path_get(f"issue/{issue}")
        if not iss_dct:
            return (404, "Issue missing")
        iss_dct["fields"]["status"] = new_status
        return (204, "")


class FakeJira(jira.JIRA):

    _kw_defaults = {"server": "https+mock://jira", "basic_auth": ("nobody", "deadbeef")}

    def __init__(self, *args, **kw):
        nkw = dict(self._kw_defaults)
        nkw.update(kw)
        self.data = IdTree()
        self.read_fixtures("test_data.json")
        super().__init__(*args, **nkw)

    def read_fixtures(self, path):
        full_path = os.path.join(os.path.dirname(__file__), path)
        with open(full_path) as jfd:
            self.data.update(json.load(jfd))

    def _create_http_basic_session(self, username, password, timeout=None):
        self._session = requests.Session()
        self._session.mount("https+mock://", FakeJiraAdapter(self.data))

    def fake_user(self, name, email=None, display_name=None):
        item = {
            "name": name,
            "key": name,
            "self": jurl(f"user?username={name}"),
            "emailAddress": (email or f"{name}@pekao.com.pl"),
            "displayName": (display_name or name),
            "active": True,
            "timeZone": "Europe/Warsaw",
            "locale": "pl_PL",
        }
        self.data.new_element("user", item)
        return item

    def fake_project(self, key, name=None, ptype='software'):
        item = {
            "key": key,
            "self": jurl("issue/{JID}"),
            "name": (name or f"Project {key}"),
            "projectTypeKey": ptype,
            "projectCategory": {
                "id": "10001",
                "name": "Project",
                "description": "",
            }
        }
        self.data.new_element("project", item, key="key")
        return item

    def fake_issue(
        self,
        key,
        status_id="Do zrobienia",
        issuetype="Błąd",
        assignee=None,
    ):
        issue_type = self.data.path_get(f"issuetype/{issuetype}")
        project_key = key.split('-')[0]
        try:
            project = self.data.path_get(f"project/{project_key}")
        except KeyError:
            project = self.fake_project(project_key)
        status = self.data.path_get(f"status/{status_id}")
        if assignee:
            assignee = self.data.path_get(f"user/{assignee}")
        item = {
            "key": key,
            "self": jurl("issue/{JID}"),
            "fields": {
                "issuetype": issue_type,
                "project": project,
                "assignee": assignee,
                "created": wawnow().isoformat(),
                "updated": wawnow().isoformat(),
                "status": status,
                "priority": {"name": "High", "id": "2",},
                "components": [],
                "comment": {"comments": [],},
            },
        }
        self.data.new_element("issue", item, key="key")
        return item


def get_fake_jira_client():
    from skylla.clients.jira import Jira

    Jira.__bases__ = (FakeJira,)
    fj = Jira.from_cfg()
    return fj


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    fj = FakeJira()
    fj.fake_issue("REL-100", assignee="jira_tech_gerrit")
    rel100 = fj.issue("REL-100")
    fj.add_comment("REL-100", "ble ble ble")
    fj.transition_issue("REL-100", "Ready")
    fj.assign_issue("REL-100", None)
    rel100.update(fields={"components": ['foo', 'bar']})
