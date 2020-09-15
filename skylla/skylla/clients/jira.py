import logging
from typing import Any, Dict, Iterable, Iterator, List, Optional, Type, TypeVar

import jira

from ..settings import cfg

logger = logging.getLogger(__name__)

TJira = TypeVar("TJira", bound="Jira")


def log_error(
    jira_error: jira.JIRAError,
    message: str,
    *args: Iterable[Any],
    level: int = logging.WARNING,
    extra: Dict[str, Any] = None,
) -> None:
    jargs = [jira_error.status_code, jira_error.text]
    jargs.extend(args)
    jextra = dict(extra or {})
    try:
        jextra["jira_response"] = jira_error.response.json()
    except Exception:
        pass
    logger.log(level, f"{ message }: JIRAError %s: %s", *jargs, extra=jextra)


class Jira(jira.JIRA):
    @classmethod
    def from_cfg(cls: Type[TJira]) -> TJira:
        jcfg = cfg["jira"]
        return Jira(server=jcfg["url"], basic_auth=(jcfg["user"], jcfg["password"]))

    def get_issues(
        self,
        issue_ids: Iterable[str],
        extra_jql: Optional[str] = None,
        fields: Optional[Iterable[str]] = None,
    ) -> List[jira.resources.Issue]:
        """Gets multiple issues at once

        note that if any issue id is invalid it will throw JiraError
        """
        jql = "key in ({})".format(", ".join(f'"{i}"' for i in issue_ids))
        if extra_jql:
            jql += " AND " + extra_jql
        return self.search_issues(jql, fields=fields)

    def get_issues_safe(
        self, issue_ids: Iterable[str], fields: Optional[Iterable[str]] = None,
    ) -> Iterator[jira.resources.Issue]:
        """Gets multiple issues at once, ignores missing
        """
        for issue_id in issue_ids:
            try:
                yield self.issue(issue_id, fields=fields)
            except jira.exceptions.JIRAError as err:
                if err.status_code == 404:
                    logger.info("Jira ticket %s does not exist", issue_id)
                    continue
                raise

    async def issues_ready(self, issue_ids: Iterable[str], comment: str) -> None:
        """Zmiana statusów zgłoszeń na 'Ready'

        Zmiana odnacza zgłoszenia gotowe do wdrożenia (status Ready /10102/)
        usuwa właściciela - zgłoszenie trafia do kolejki zespołu utrzymaniowego
        Pomijane są zgłoszenia zamknięte (kategoria statusu Gotowe /3/)
        """
        issues = self.get_issues_safe(issue_ids, fields=["status"])
        for issue in issues:
            self.add_comment(issue.id, comment)
            if not issue.key.startswith("REL-"):
                # na razie zmiany statusu tylko w projekcie Stabilizcja wydania
                continue
            if issue.fields.status.statusCategory.id == 3:
                # zgłoszenie ma status z kategorii Gotowe (Done)
                continue
            if issue.fields.status.id == 10102:
                # status już jest Ready
                continue
            # zmień status na Ready
            self.transition_issue(issue.id, "Ready")
            # usuń przypisaną osobę
            self.assign_issue(issue.id, None)

    async def add_componet(self, issue_ids: Iterable[str], project_name: str) -> None:
        """
        Dodanie komponentu do zgłoszeń typu REL-
        jeżeli jest już dodany inny komponent to zostanie dodany
        do już istniejącego
        """
        issues = self.get_issues_safe(issue_ids, fields=["status"])
        for issueid in issues:
            issue = self.issue(issueid.id)
            component_names = {comp.name for comp in issue.fields.components}
            component_names.add(project_name)

            try:
                issue.update(
                    fields={"components": [{"name": cn} for cn in component_names]}
                )
            except jira.exceptions.JIRAError as err:
                if err.status_code == 400 and err.text.startswith(""):
                    log_error(
                        err,
                        "Issues %s project has no component %s",
                        issueid,
                        project_name,
                    )
                    # TODO: send e-mail
                    continue
                log_error(
                    err, "Error adding component %s to issue %s", project_name, issueid
                )

    async def add_comment_to_ticket(self, issue_ids: Iterable[str], comment: str) -> None:
        """pojedyńcze dodoanie komentarza  """
        issues = self.get_issues_safe(issue_ids, fields=["status"])
        for issue in issues:
            self.add_comment(issue.id, comment)
