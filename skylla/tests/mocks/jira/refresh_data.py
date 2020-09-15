#!/usr/bin/env python

import argparse
import getpass
import json
import sys

import jira

from idtree import IdTree

MOCK_URL = "https+mock://jira/rest/api/2/"


def fetch_config(jh, out_fd):
    original_url = jh._get_url("")
    data = IdTree()

    def updself(dct):
        path = dct["self"].replace(original_url, "")
        assert not path.startswith("http")
        dct["self"] = MOCK_URL + path
        return dct

    data.add_collection("field", jh.fields())
    data["serverInfo"] = jh.server_info()
    data["serverInfo"]["baseUrl"] = "https+mock://jira"
    statuses = []
    for status in jh.statuses():
        updself(status.raw)
        updself(status.raw["statusCategory"])
        statuses.append(status.raw)
    data.add_collection("status", statuses)
    data.add_collection("issuetype", [updself(itype.raw) for itype in jh.issue_types()])
    # this one is a big hack
    data.path_set("_methods/REL/transitions", jh._get_json("issue/REL-100/transitions"))
    data.add_collection(
        "user", jh._get_json("user/search?username=jira_tech_gerrit"), id_key="key"
    )
    json.dump(data, out_fd, indent=1, ensure_ascii=False, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(description="Fetch Fake JIRA configuration")
    parser.add_argument(
        "-a", "--address", dest="address", required=True, help="JIRA address"
    )
    parser.add_argument("-u", "--username", dest="username", help="JIRA username")
    parser.add_argument("-p", "--password", dest="password", help="JIRA password")
    parser.add_argument(
        "-o",
        "--out",
        dest="out",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="output path, default is stdout",
    )
    args = parser.parse_args()
    basic_auth = None
    if args.username:
        while not args.password:
            args.password = getpass.getpass("JIRA password:")
        basic_auth = (args.username, args.password)
    jh = jira.JIRA(server=args.address, basic_auth=basic_auth)
    fetch_config(jh, args.out)


if __name__ == "__main__":
    main()
