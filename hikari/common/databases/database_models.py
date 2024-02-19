from pydantic import BaseModel

from hikari.common.filetype import DownloadableFileType


class DBTaskModel(BaseModel):
    id: int
    content: str
    complete: int
    fail: int
    reason: str | None


class DBDHistoryModel(BaseModel):
    id: int
    source: str
    url: str
    local_path: str
    complete: int
    task_id: int
    author_id: int
    filetype: DownloadableFileType
