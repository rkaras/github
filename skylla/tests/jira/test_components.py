import json

import jira.exceptions
import pytest

from tests.mocks.jira.fake import get_fake_jira_client


@pytest.mark.asyncio
async def test_add_component():
    fj = get_fake_jira_client()
    fj.fake_issue('REL-900')
    await fj.add_componet(['REL-900'], 'infra/skylla')
    rel100 = fj.issue('REL-900')
    assert rel100.fields.components
    cnames = tuple(c.name for c in rel100.fields.components)
    assert cnames == ('infra/skylla',)


@pytest.mark.asyncio
async def test_append_component():
    fj = get_fake_jira_client()
    fj.fake_issue('REL-900')
    await fj.add_componet(['REL-900'], 'infra/skylla')
    await fj.add_componet(['REL-900'], 'infra/zuul/zuul')
    rel100 = fj.issue('REL-900')
    cnames = tuple(c.name for c in rel100.fields.components)
    assert 'infra/skylla' in cnames
    assert 'infra/zuul/zuul' in cnames
