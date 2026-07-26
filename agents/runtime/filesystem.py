from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from deepagents import FilesystemPermission
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import (
    BackendProtocol,
    EditResult,
    FileDownloadResponse,
    FileUploadResponse,
    GlobResult,
    GrepResult,
    LsResult,
    ReadResult,
    WriteResult,
)

from backend.config.settings import Settings, get_settings


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_runtime_path(value: str, *, base: Path | None = None) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return ((base or repository_root()) / path).resolve()


@dataclass(frozen=True)
class RuntimePaths:
    evidence_root: Path
    model_repo_checkout: Path
    skills_root: Path

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> RuntimePaths:
        settings = settings or get_settings()
        root = repository_root()
        return cls(
            evidence_root=resolve_runtime_path(settings.evidence_root, base=root),
            model_repo_checkout=resolve_runtime_path(settings.model_repo_checkout, base=root),
            skills_root=root / "agents" / "skills",
        )

    @property
    def systems_root(self) -> Path:
        return self.model_repo_checkout / "systems"


class ReadOnlyBackend(BackendProtocol):
    def __init__(self, inner: BackendProtocol, *, label: str) -> None:
        self.inner = inner
        self.label = label

    def ls(self, path: str) -> LsResult:
        return self.inner.ls(path)

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        return self.inner.read(file_path, offset=offset, limit=limit)

    def grep(self, pattern: str, path: str | None = None, glob: str | None = None) -> GrepResult:
        return self.inner.grep(pattern, path=path, glob=glob)

    def glob(self, pattern: str, path: str | None = None) -> GlobResult:
        return self.inner.glob(pattern, path=path)

    def write(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error=f"Writes are not allowed under {self.label}: {file_path}")

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(error=f"Edits are not allowed under {self.label}: {file_path}")

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        return [
            FileUploadResponse(path=path, error=f"Uploads are not allowed under {self.label}")
            for path, _content in files
        ]

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        return self.inner.download_files(paths)


def local_filesystem_backend(root_dir: Path) -> FilesystemBackend:
    return FilesystemBackend(root_dir=root_dir, virtual_mode=True)


def build_runtime_backend(paths: RuntimePaths | None = None) -> CompositeBackend:
    paths = paths or RuntimePaths.from_settings()
    return CompositeBackend(
        default=StateBackend(),
        routes={
            "/evidence/": ReadOnlyBackend(
                local_filesystem_backend(paths.evidence_root),
                label="/evidence/",
            ),
            "/systems/": local_filesystem_backend(paths.systems_root),
            "/skills/": ReadOnlyBackend(
                local_filesystem_backend(paths.skills_root),
                label="/skills/",
            ),
        },
    )


def filesystem_permissions() -> list[FilesystemPermission]:
    return [
        FilesystemPermission(
            operations=["write"],
            paths=["/evidence/**", "/skills/**"],
            mode="deny",
        )
    ]


def ensure_runtime_directories(paths: RuntimePaths | None = None) -> None:
    paths = paths or RuntimePaths.from_settings()
    for directory in _writable_runtime_directories(paths):
        directory.mkdir(parents=True, exist_ok=True)


def _writable_runtime_directories(paths: RuntimePaths) -> Iterable[Path]:
    yield paths.evidence_root
    yield paths.systems_root
