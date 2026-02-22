from dataclasses import dataclass
from typing import Optional, Dict, Any

import yaml

from .errors import QueueError


@dataclass
class Job:
    job_id: str
    user: str
    project_path: str
    compose_file: str
    created_at: str
    description: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

    # -------------------------
    # Deserialization
    # -------------------------

    @classmethod
    def from_dict(cls, job_id: str, data: Dict[str, Any]) -> "Job":
        try:
            return cls(
                job_id=job_id,
                user=data["user"],
                project_path=data["project_path"],
                compose_file=data.get("compose_file", "docker-compose.yml"),
                created_at=data["created_at"],
                description=data.get("description", ""),
                started_at=data.get("started_at"),
                finished_at=data.get("finished_at"),
            )
        except KeyError as e:
            raise QueueError(
                f"Invalid job format for {job_id}, missing field: {e}"
            ) from e

    @classmethod
    def from_yaml(cls, job_id: str, yaml_content: str) -> "Job":
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise QueueError(
                f"Invalid YAML content for job {job_id}: {e}"
            ) from e

        if not isinstance(data, dict):
            raise QueueError(
                f"Invalid YAML structure for job {job_id}: expected mapping"
            )

        return cls.from_dict(job_id, data)

    # -------------------------
    # Serialization
    # -------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user": self.user,
            "project_path": self.project_path,
            "compose_file": self.compose_file,
            "created_at": self.created_at,
            "description": self.description,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.to_dict(),
            sort_keys=False,
            default_flow_style=False,
        )

    # -------------------------
    # State helpers
    # -------------------------

    def mark_started(self, timestamp: str) -> None:
        self.started_at = timestamp

    def mark_finished(self, timestamp: str) -> None:
        self.finished_at = timestamp