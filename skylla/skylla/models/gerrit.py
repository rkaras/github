from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Union

from pydantic import UUID4, BaseModel, HttpUrl

from ..settings import cfg
from .git import GitUrl

GERRIT_URL = cfg["gerrit"]["url"].rstrip("/")

nstr = Optional[str]
nint = Optional[int]
nbool = Optional[bool]
ndatetime = Optional[datetime]
NHttpUrl = Optional[HttpUrl]


class ActionInfoMethod(str, Enum):
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class ActionInfo(BaseModel):
    method: Optional[ActionInfoMethod] = None
    label: nstr = None
    title: nstr = None
    enabled: bool = False


class AvatarInfo(BaseModel):
    url: HttpUrl
    height: int
    width: nint = None


class AccountInfo(BaseModel):
    id: int
    name: nstr = None
    display_name: nstr = None
    email: nstr = None
    secondary_emails: Optional[List[str]] = None
    username: nstr = None
    avatars: Optional[List[AvatarInfo]] = None
    more_accounts: bool = False
    status: nstr = None
    inactive: bool = False

    class Config:
        fields = {
            "id": "_account_id",
            "more_accounts": "_more_accounts",
        }

    def __repr__(self) -> str:
        return f"<AccountInfo: {self.id} {self.username}>"


NAccountInfo = Optional[AccountInfo]


class VotingRangeInfo(BaseModel):
    min: str
    max: str


class ApprovalInfo(BaseModel):
    value: nstr = None
    permitted_voting_range: Optional[VotingRangeInfo] = None
    date: datetime
    tag: nstr = None
    post_submit: bool = False


class ChangeMessageInfo(BaseModel):
    id: str
    author: NAccountInfo = None
    real_author: NAccountInfo = None
    date: datetime
    message: str
    tag: nstr = None
    revision_number: nint = None

    class Config:
        fields = {
            "revision_number": "_revision_number",
        }


class LabelInfo(BaseModel):
    optional: bool = False
    approved: NAccountInfo = None
    rejected: NAccountInfo = None
    recommended: NAccountInfo = None
    disliked: NAccountInfo = None
    blocking: bool = False
    value: nstr = None
    default_value: nstr = None


class FetchInfo(BaseModel):
    url: GitUrl
    ref: str
    commands: Optional[Dict[str, str]] = None


class GitPersonInfo(BaseModel):
    name: str
    email: str
    date: datetime
    tz: str


class WebLinkInfo(BaseModel):
    name: str
    url: str
    image_url: nstr = None


WebLinkInfoList = List[WebLinkInfo]
NWebLinkInfoList = Optional[WebLinkInfoList]


class FileInfoStatus(str, Enum):
    added = "A"
    deleted = "D"
    renamed = "R"
    copied = "C"
    rewritten = "W"
    modified = None


class FileInfo(BaseModel):
    status: FileInfoStatus = FileInfoStatus.modified
    binary: bool = False
    old_path: nstr = None
    lines_inserted: nint = None
    lines_deleted: nint = None
    size_delta: int
    size: int


class TrackingIdInfo(BaseModel):
    system: str
    id: str


class CommitInfo(BaseModel):
    commit: nstr = None
    parents: Optional[List["CommitInfo"]] = None
    author: Optional[GitPersonInfo] = None
    committer: Optional[GitPersonInfo] = None
    subject: str
    message: nstr = None
    web_links: NWebLinkInfoList = None

    @property
    def url(self) -> Optional[str]:
        paths = [wl.url for wl in self.web_links or () if wl.name == "browse"]
        if paths:
            return f"{GERRIT_URL}{paths[0]}"
        return None


CommitInfo.update_forward_refs()


class IncludedInInfo(BaseModel):
    branches: Set[str]
    tags: Set[str]
    external: Optional[Dict[str, List[str]]]


class DetailedLabelInfo(BaseModel):
    optional: bool = False
    all: List[ApprovalInfo]
    values: List[str]


AnyLabelInfo = Union[DetailedLabelInfo, LabelInfo]


class GpgKeyStatus(str, Enum):
    BAD = "BAD"
    OK = "OK"
    TRUSTED = "TRUSTED"


class GpgKeyInfo(BaseModel):
    id: nstr = None
    fingerprint: nstr = None
    user_ids: nstr = None
    key: nstr = None
    status: Optional[GpgKeyStatus] = None
    problems: Optional[List[str]] = None


class RequirementStatus(str, Enum):
    OK = "OK"
    NOT_READY = "NOT_READY"
    RULE_ERROR = "RULE_ERROR"


class Requirement(BaseModel):
    status: RequirementStatus
    fallback_text: str
    type: str


class ProblemStatus(str, Enum):
    FIXED = "FIXED"
    FIX_FAILED = "FIX_FAILED"


class ProblemInfo(BaseModel):
    message: str
    status: Optional[ProblemStatus] = None
    outcome: nstr = None


class PushCertificateInfo(BaseModel):
    certificate: str
    key: GpgKeyInfo


class ReviewerUpdateState(str, Enum):
    REVIEWER = "REVIEWER"
    CC = "CC"
    REMOVED = "REMOVED"


class ReviewerUpdateInfo(BaseModel):
    updated: datetime
    updated_by: AccountInfo
    reviewer: AccountInfo
    state: ReviewerUpdateState


class RevisionKind(str, Enum):
    REWORK = "REWORK"
    TRIVIAL_REBASE = "TRIVIAL_REBASE"
    MERGE_FIRST_PARENT_UPDATE = "MERGE_FIRST_PARENT_UPDATE"
    NO_CODE_CHANGE = "NO_CODE_CHANGE"
    NO_CHANGE = "NO_CHANGE"


class RevisionInfo(BaseModel):
    kind: RevisionKind
    number: int
    created: datetime
    uploader: AccountInfo
    ref: str
    fetch: Dict[str, FetchInfo]
    commit: Optional[CommitInfo] = None
    files: Optional[Dict[str, FileInfo]] = None
    actions: Optional[Dict[str, ActionInfo]] = None
    reviewed: nbool = None
    commit_with_footers: nbool = None
    push_certificate: Optional[PushCertificateInfo] = None
    description: nstr = None

    class Config:
        fields = {
            "number": "_number",
        }


class ChangeStatus(str, Enum):
    NEW = "NEW"
    MERGED = "MERGED"
    ABANDONED = "ABANDONED"


class ChangeInfo(BaseModel):
    id: str
    project: str
    branch: str
    topic: nstr = None
    assignee: NAccountInfo = None
    hashtags: Optional[List[str]] = None
    change_id: str
    subject: str
    status: ChangeStatus
    created: datetime
    updated: datetime
    submitted: ndatetime = None
    submitter: NAccountInfo = None
    starred: bool = False
    stars: Optional[List[str]] = None
    reviewed: bool = False
    submit_type: nstr = None
    mergeable: nbool = None
    submittable: nbool = None
    insertions: int
    deletions: int
    total_comment_count: nint = None
    unresolved_comment_count: nint = None
    number: int
    owner: AccountInfo
    actions: Optional[List[ActionInfo]] = None
    requirements: Optional[List[Requirement]] = None
    labels: Optional[Dict[str, AnyLabelInfo]] = None
    permitted_labels: Optional[Dict[str, List[str]]] = None
    removable_reviewers: Optional[List[AccountInfo]] = None
    reviewers: Optional[Dict[str, List[AccountInfo]]] = None
    pending_reviewers: Optional[Dict[str, List[AccountInfo]]] = None
    reviewer_updates: Optional[List[ReviewerUpdateInfo]] = None
    messages: Optional[List[ChangeMessageInfo]] = None
    current_revision: nstr = None
    revisions: Optional[Dict[str, RevisionInfo]] = None
    tracking_ids: Optional[List[TrackingIdInfo]] = None
    more_changes: bool = False
    problems: Optional[List[ProblemInfo]] = None
    is_private: bool = False
    work_in_progress: bool = False
    has_review_started: bool = False
    revert_of: nstr = None
    submission_id: nstr = None
    cherry_pick_of_change: nstr = None
    cherry_pick_of_patch_set: nstr = None
    contains_git_conflicts: bool = False

    @property
    def current_rev(self) -> Optional[RevisionInfo]:
        if self.current_revision and self.revisions:
            return self.revisions[self.current_revision]
        return None

    @property
    def full_number(self) -> str:
        rev = self.current_rev
        if rev:
            return f"{self.number}/{rev.number}"
        return str(self.number)

    @property
    def url(self) -> str:
        if self.project:
            return f"{GERRIT_URL}/c/{self.project}/+/{self.full_number}"
        else:
            return f"{GERRIT_URL}/c/{self.full_number}"

    class Config:
        fields = {
            "number": "_number",
            "more_changes": "_more_changes",
        }

    def __repr__(self) -> str:
        return f"<ChangeInfo: {self.id}>"


class LabelTypeInfo(BaseModel):
    values: Dict[str, str]
    default_value: str


class ProjectState(str, Enum):
    ACTIVE = "ACTIVE"
    READ_ONLY = "READ_ONLY"
    HIDDEN = "HIDDEN"


class ProjectInfo(BaseModel):
    id: str
    name: nstr = None
    parent: nstr = None
    description: nstr = None
    state: Optional[ProjectState] = None
    branches: Optional[Dict[str, str]] = None
    labels: Optional[Dict[str, LabelTypeInfo]] = None
    web_links: Optional[List[WebLinkInfo]] = None

    def __repr__(self) -> str:
        return f"<ProjectInfo: {self.id}>"


class BranchInfo(BaseModel):
    ref: str
    revision: str
    can_delete: bool = False
    web_links: NWebLinkInfoList = None


class TagInfo(BaseModel):
    ref: str
    revision: str
    object: nstr = None
    message: nstr = None
    tagger: Optional[GitPersonInfo] = None
    created: ndatetime = None
    can_delete: bool = False
    web_links: NWebLinkInfoList = None


class CheckState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    FAILED = "FAILED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    SUCCESSFUL = "SUCCESSFUL"
    NOT_RELEVANT = "NOT_RELEVANT"


class BlockingCondition(str, Enum):
    STATE_NOT_PASSING = "STATE_NOT_PASSING"


class CheckInfo(BaseModel):
    repository: str
    change_number: int
    patch_set_id: int
    checker_uuid: UUID4
    state: CheckState
    message: nstr = None
    url: NHttpUrl = None
    started: ndatetime = None
    finished: ndatetime = None
    created: datetime
    updated: datetime
    checker_name: nstr = None
    checker_status: Optional[CheckState] = None
    blocking: List[BlockingCondition]
    checker_description: nstr = None


class CheckerStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class CheckerInfo(BaseModel):
    uuid: UUID4
    name: str
    description: nstr = None
    url: NHttpUrl = None
    repository: str
    status: CheckerStatus
    blocking: List[BlockingCondition]
    query: nstr = None
    created: datetime
    updated: datetime
