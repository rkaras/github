import os
from typing import Optional

from piny import PydanticValidator  # type: ignore
from piny import StrictMatcher, YamlLoader
from pydantic import BaseModel, HttpUrl


class GerritConfig(BaseModel):
    url: HttpUrl
    user: str
    password: str


class JiraConfig(BaseModel):
    url: HttpUrl
    user: str
    password: str


class SentryConfig(BaseModel):
    dsn: Optional[str] = None


class Settings(BaseModel):
    gerrit: GerritConfig
    jira: JiraConfig
    sentry: SentryConfig
    ca_certs: str


cfg = YamlLoader(
    os.environ.get("SKYLLA_CONFIG", "skylla.conf"),
    matcher=StrictMatcher,
    validator=PydanticValidator,
    schema=Settings,
    strict=True,
).load()
