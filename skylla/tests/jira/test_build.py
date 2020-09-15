import json

import jira.exceptions
import pytest

from tests.mocks.jira.fake import get_fake_jira_client


def test_get_issues_safe():
    fj = get_fake_jira_client()
    fj.fake_issue('REL-123')
    issues = fj.get_issues_safe(["REL-123", "REL-1234"])
    issues_list = list(issues)
    assert len(issues_list) == 1
    assert issues_list[0].key == "REL-123"


@pytest.mark.asyncio
async def test_issues_ready():
    fj = get_fake_jira_client()
    fj.fake_issue('REL-900', status_id="Do zrobienia", assignee="jira_tech_gerrit")
    await fj.issues_ready(['REL-900'], comment="a ku ku")
    rel900 = fj.issue('REL-900')

    assert rel900.fields.comment.comments
    assert rel900.fields.comment.comments[0].body == "a ku ku"
    assert not rel900.fields.assignee
    assert rel900.fields.status.id == '10102'
    assert rel900.fields.status.name == 'Gotowe'


@pytest.mark.asyncio
async def test_issues_ready_nonrel():
    fj = get_fake_jira_client()
    fj.fake_issue('ABC-123', status_id="Do zrobienia", assignee="jira_tech_gerrit")
    await fj.issues_ready(['ABC-123'], comment="a ku ku")
    abc123 = fj.issue('ABC-123')

    assert abc123.fields.comment.comments[0].body == "a ku ku"
    assert abc123.fields.assignee.name == "jira_tech_gerrit"
    assert abc123.fields.status.name == "Do zrobienia"


@pytest.mark.asyncio
async def test_issues_ready_ignore_closed():
    fj = get_fake_jira_client()
    fj.fake_issue('REL-100', status_id="Wykonane", assignee="jira_tech_gerrit")
    await fj.issues_ready(['REL-100'], comment="a ku ku")
    rel100 = fj.issue('REL-100')

    assert rel100.fields.comment.comments[0].body == "a ku ku"
    assert rel100.fields.assignee.name == "jira_tech_gerrit"
    assert rel100.fields.status.name == "Wykonane"
