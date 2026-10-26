from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    root: Path
    reports_dir: Path
    dist_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "ProjectConfig":
        resolved = root.resolve()
        return cls(resolved, resolved / "reports", resolved / "dist")

    def ensure_dirs(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.dist_dir.mkdir(parents=True, exist_ok=True)
