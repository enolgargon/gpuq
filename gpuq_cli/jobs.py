from dataclasses import dataclass
from typing import Optional, Dict, Any
import yaml

from .errors import JobValidationError
from .utils import validate_iso8601

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
    state: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate()

    # -------------------------
    # Validation
    # -------------------------

    def _validate(self) -> None:
        if not self.job_id:
            raise JobValidationError("job_id cannot be empty")

        if not self.user:
            raise JobValidationError("user cannot be empty")

        if not self.project_path:
            raise JobValidationError("project_path cannot be empty")

        if not self.compose_file:
            raise JobValidationError("compose_file cannot be empty")

        if not self.created_at:
            raise JobValidationError("created_at cannot be empty")

        try:
            validate_iso8601(self.created_at, "created_at")
            validate_iso8601(self.started_at, "started_at")
            validate_iso8601(self.finished_at, "finished_at")
        except ValueError as e:
            raise JobValidationError(str(e)) from e

    # -------------------------
    # Serialization
    # -------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "user": self.user,
            "description": self.description,
            "project_path": self.project_path,
            "compose_file": self.compose_file,
            "created_at": self.created_at,
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
    # Deserialization
    # -------------------------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        required_fields = [
            "job_id",
            "user",
            "project_path",
            "compose_file",
            "created_at",
        ]

        for field_name in required_fields:
            if field_name not in data:
                raise JobValidationError(
                    f"Missing required field '{field_name}'"
                )

        return cls(
            job_id=data["job_id"],
            user=data["user"],
            project_path=data["project_path"],
            compose_file=data["compose_file"],
            created_at=data["created_at"],
            description=data.get("description", ""),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
        )

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "Job":
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise JobValidationError(f"Invalid YAML content: {e}")

        if not isinstance(data, dict):
            raise JobValidationError("YAML content must define a mapping")

        return cls.from_dict(data)

    # -------------------------
    # Helpers
    # -------------------------

    def mark_started(self, timestamp: str) -> None:
        try:
            validate_iso8601(timestamp, "started_at")
        except ValueError as e:
            raise JobValidationError(str(e)) from e
        self.started_at = timestamp

    def mark_finished(self, timestamp: str) -> None:
        try:
            validate_iso8601(timestamp, "finished_at")
        except ValueError as e:
            raise JobValidationError(str(e)) from e
        self.finished_at = timestamp