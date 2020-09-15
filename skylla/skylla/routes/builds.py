import logging
import re
from typing import List, Optional

from fastapi import APIRouter

from ..clients.gerrit import GerritClient, NotFound
from ..clients.jira import Jira
from ..lib.j2tmpl import j2_env
from ..models.builds import BuildInfo, GitUrl, PatchInfo
from ..models.gerrit import ChangeInfo

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/completed")
async def build_completed(binfo: BuildInfo) -> None:
    """Akcje po zbudowaniu paczki przez system CI

    Jeśli w komentarzu commitu znajdują się odniesienia do zgłoszeń w Jirze,
    to do zgłoszenia zostanie dodany komentarz z informacją o paczce.
    Dla określonych projektów (na razie tylko REL) zmieniony zostanie również
    status zgłoszenia na Ready i usunięty bieżący właściel, aby zgłoszenie
    trafiło do właściwej kolejki

    Brane są pod uwagę tylko zmiany w gałęzi develop
    """
    logger.info("request: %r", binfo)
    # get info from Gerrit (even if there is no matching change)
    ger = GerritClient()
    change: Optional[ChangeInfo]
    branches = set()
    project_name = project_from_url(binfo.repo)
    try:
        change = await ger.get_change(binfo.ref)
        branches.add(change.branch)
        commits = await ger.change_commits(binfo.ref)
      #  logging.info("change_commits %s", commits)
    except NotFound:
        change = None
        if not binfo.repo:
            logger.warning("Missing change and repo")
            return
        try:
       #     logging.info("get_commit %s", binfo.ref)
            commits = [await ger.get_commit(project_name, binfo.ref)]
        except NotFound:
            logger.warning("No change nor commit found for %s", binfo.ref)
            return
        incl_nfo = await ger.get_commit_branches(project_name, binfo.ref)
        branches = incl_nfo.branches

    if "develop" not in branches:
        return


        """
    #breakpoint()
    jira_ids = set()
    for commit in commits:
        if not commit.message:
            continue
        for issue_id in find_jira_issues(commit.message):
            jira_ids.add(issue_id)

        commits_p = await ger.change_commits(commit.parents[0].commit)
        for commit_p in commits_p:
            if not commit_p.message:
                continue
            logger.warning(commit_p)
            #breakpoint()
            for issue_id_p in find_jira_issues(commit_p.message):
                jira_ids.add(issue_id_p)

        logger.warning(commits_p)
    breakpoint()
    


        """
   # breakpoint()
    jira_ids = set()
    for commit in commits:
        if not commit.message:
            continue
        for issue_id in find_jira_issues(commit.message):
            jira_ids.add(issue_id)

    btmpl = j2_env.get_template("jira_build_comment.j2")
    comment = btmpl.render(commit=commits[0], change=change, build=binfo)
    jira = Jira.from_cfg()
    logger.info("found issues %s", ", ".join(jira_ids))
    await jira.issues_ready(jira_ids, comment)

    for issue_id in jira_ids:
        if not issue_id.startswith("REL-"):
            continue
        # dodanie komponentu tylko w projekcie Stabilizcja wydania
        await jira.add_componet(jira_ids, project_name)


def project_from_url(url: GitUrl) -> str:
    """Finds Gerrit project name in repository URL

    HTTP access method is usually used with authentication, so we take parts
    after "/a/". In other case we assume this is ssh:// and take whole path.
    This could have problems with anonymous HTTP and path with prefix.
    """
    assert url.path
    path = url.path.rstrip("/")
    path_parts = re.split("/a/", path, maxsplit=1)
    if len(path_parts) == 1:
        return path
    return path_parts[-1]


def find_jira_issues(msg: str) -> List[str]:
    re_issue = re.compile(r"([A-Z]{2,8}-\d+)")
    return re_issue.findall(msg)

@router.post("/patch")
async def build_patched(binfo: PatchInfo) -> None:
    logger.info("request: %r", binfo)
    ger = GerritClient()
    change: Optional[ChangeInfo]
    branches = set()
    jira = Jira.from_cfg()

    try:
        change = await ger.get_change(binfo.ref)
        branches.add(change.branch)
        commits = await ger.change_commits(binfo.ref)
    except NotFound:
        change = None
        if not binfo.repo:
            logger.warning("Missing change and repo")
            return
    if "develop" not in branches:
        return    
    jira_ids = set()
    for commit in commits:
        if not commit.message:
            continue
        for issue_id in find_jira_issues(commit.message):
            jira_ids.add(issue_id)
        
        commits_p = await ger.change_commits(commit.parents[0].commit)
        for commit_p in commits_p:
            if not commit_p.message:
                continue
            for issue_id_p in find_jira_issues(commit_p.message):
                jira_ids.add(issue_id_p)
            logger.info("found issues %s", ", ".join(jira_ids))

    if binfo.environment =='PRE':
        comment = "wdrożone na $PreProdukcyjne"
        for issue_id in jira_ids:
            if not issue_id.startswith("REL-"):
                continue
            await jira.add_comment_to_ticket(jira_ids, comment)
    
    if binfo.environment =='PROD':
        comment = "wdrożone na $Produkcyjne"
        for issue_id in jira_ids:
            if not issue_id.startswith("REL-"):
                continue
        await jira.issues_ready(jira_ids, comment)





    # po wywołaniu posta w jenkins należy znależć w gerrit paczke 
    
    #  
    # ostani krok zmiana stausu ticketu 
   # await jira.issues_ready(jira_ids, comment)
