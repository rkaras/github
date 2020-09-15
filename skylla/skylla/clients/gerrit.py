import json
import logging
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus

import httpx

from ..models.gerrit import ChangeInfo, CommitInfo, IncludedInInfo, ProjectInfo
from ..settings import cfg

logger = logging.getLogger(__name__)


class GerritError(Exception):
    pass


class NotFound(GerritError):
    pass


default_change_opts = frozenset(
    (
        # 'LABELS',
        # 'DETAILED_LABELS',
        "CURRENT_REVISION",
        # 'ALL_REVISIONS',
        # 'DOWNLOAD_COMMANDS',
        "CURRENT_COMMIT",
        # 'ALL_COMMITS',
        # 'CURRENT_FILES',
        # 'ALL_FILES',
        "DETAILED_ACCOUNTS",
        # 'REVIEWER_UPDATES',
        # 'MESSAGES',
        # 'CURRENT_ACTIONS',
        # 'CHANGE_ACTIONS',
        # 'REVIEWED',
        # 'SKIP_DIFFSTAT',
        # 'SUBMITTABLE',
        "WEB_LINKS",
        # 'CHECK',
        # 'COMMIT_FOOTERS',
        # 'PUSH_CERTIFICATES',
        # 'TRACKING_IDS',
    )
)


class GerritClient:
    def __init__(self) -> None:
        gcfg = cfg["gerrit"]
        self.client = httpx.AsyncClient(
            auth=(gcfg["user"], gcfg["password"]), verify=cfg["ca_certs"]
        )
        self.base_addr = gcfg["url"].rstrip("/") + "/a"

    async def raw_get(self, *parts: str, **params: Any) -> bytes:
        url = "/".join((self.base_addr,) + parts)
        logging.info("Gerrit GET %s", url)
        resp = await self.client.get(url, **params)
        if resp.status_code == 404:
            raise NotFound(resp.reason_phrase)
        elif resp.status_code != 200:
            raise GerritError(resp.status_code, resp.reason_phrase)
        return resp.content[5:]

    async def get(self, *parts: str, **params: Any) -> Dict[str, Any]:
        raw_data = await self.raw_get(*parts, **params)
        return json.loads(raw_data)

    async def get_change(
        self, change_id: str, options: Iterable[str] = default_change_opts
    ) -> ChangeInfo:
        data = await self.raw_get("changes", change_id, params={"o": tuple(options)})
        return ChangeInfo.parse_raw(data)

    async def get_commit(self, project_name: str, ref: str) -> CommitInfo:
        data = await self.raw_get("projects", quote_plus(project_name), "commits", ref)
        return CommitInfo.parse_raw(data)

    async def get_commit_branches(self, project_name: str, ref: str) -> IncludedInInfo:
        data = await self.raw_get(
            "projects", quote_plus(project_name), "commits", ref, "in"
        )
        return IncludedInInfo.parse_raw(data)

    async def get_project(self, project_name: str) -> ProjectInfo:
        data = await self.raw_get("projects", quote_plus(project_name))
        return ProjectInfo.parse_raw(data)

    async def list_projects(
        self,
        *,
        branch: Optional[str] = None,
        prefix: Optional[str] = None,
        regex: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, ProjectInfo]:
        params = {}
        if branch:
            params["b"] = branch
        if prefix:
            params["p"] = prefix
        if regex:
            params["r"] = regex
        if limit:
            params["n"] = str(limit)
        if offset:
            params["S"] = str(offset)
        jdata = await self.get("projects/", params=params)
        return {name: ProjectInfo.parse_obj(proj_js) for name, proj_js in jdata.items()}

    async def change_commits(self, change_id: str) -> List[CommitInfo]:
        """Get list of commits in a change

        Returns list of CommitInfo objects for a merge change, or list with
        just one commit for regulara commit"""
        _opts = {"ALL_COMMITS", "CURRENT_COMMIT", "CURRENT_REVISION"}
        chg_nfo = await self.get_change(change_id, options=_opts)
        if not (chg_nfo.current_rev and chg_nfo.current_rev.commit):
            return []
        assert chg_nfo.current_revision
        if len(chg_nfo.current_rev.commit.parents or ()) == 1:
            return [chg_nfo.current_rev.commit]
        j_commits = await self.get(
            "changes", change_id, "revisions", chg_nfo.current_revision, "mergelist"
        )
        return [CommitInfo.parse_obj(j_com) for j_com in j_commits]
