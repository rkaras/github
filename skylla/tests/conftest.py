import os
import pytest
import pydantic


@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    monkeypatch.setenv("SKYLLA_CONFIG", os.path.join(os.path.dirname(__file__), 'skylla-test.conf'))
    monkeypatch.setattr(pydantic, 'HttpUrl', pydantic.AnyUrl)
