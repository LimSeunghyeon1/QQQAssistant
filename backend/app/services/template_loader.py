from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from app.models.domain import SalesChannelTemplate


@dataclass
class TemplateColumn:
    header: str
    field: str
    required: bool = False


@dataclass
class ChannelTemplate:
    channel: str
    template_type: str
    columns: List[TemplateColumn]
    locale: str | None = None

    @classmethod
    def from_dict(
        cls, data: dict, *, channel: str, template_type: str
    ) -> "ChannelTemplate":
        if not isinstance(data, dict):
            raise ValueError(
                f"Template {channel}/{template_type} must be a mapping of settings"
            )

        columns_data = data.get("columns")
        if not columns_data or not isinstance(columns_data, Iterable):
            raise ValueError(
                f"Template {channel}/{template_type} must define a non-empty 'columns' list"
            )

        columns: List[TemplateColumn] = []
        for idx, col in enumerate(columns_data, start=1):
            if not isinstance(col, dict):
                raise ValueError(
                    f"Template {channel}/{template_type} column #{idx} must be an object"
                )
            header = col.get("header")
            field = col.get("field")
            if not header or not isinstance(header, str):
                raise ValueError(
                    f"Template {channel}/{template_type} column #{idx} is missing a 'header'"
                )
            if not field or not isinstance(field, str):
                raise ValueError(
                    f"Template {channel}/{template_type} column '{header}' is missing a 'field'"
                )
            required = bool(col.get("required", False))
            columns.append(TemplateColumn(header=header, field=field, required=required))

        locale = data.get("locale") if isinstance(data.get("locale"), str) else None
        return cls(channel=channel, template_type=template_type, columns=columns, locale=locale)


class ChannelTemplateLoader:
    def __init__(self, base_path: Optional[Path] = None) -> None:
        self.base_path = base_path or Path(__file__).resolve().parents[2] / "config" / "channel_formats"

    def load(self, channel: str, template_type: str, session: Optional[Session] = None) -> ChannelTemplate:
        channel = channel.lower()
        template_type = template_type.lower()

        file_template = self._load_from_files(channel, template_type)
        if file_template:
            return file_template

        if session is not None:
            db_template = self._load_from_database(channel, template_type, session)
            if db_template:
                return db_template

        raise ValueError(f"Template {channel}/{template_type} not found")

    def _load_from_files(self, channel: str, template_type: str) -> ChannelTemplate | None:
        base_name = f"{channel}_{template_type}"
        candidates = [
            self.base_path / f"{base_name}.yaml",
            self.base_path / f"{base_name}.yml",
            self.base_path / f"{base_name}.json",
        ]

        for candidate in candidates:
            if candidate.exists():
                return self._parse_file(candidate, channel, template_type)
        return None

    def _parse_file(self, file_path: Path, channel: str, template_type: str) -> ChannelTemplate:
        try:
            if file_path.suffix.lower() in {".yaml", ".yml"}:
                try:
                    import yaml  # type: ignore
                except ImportError as exc:  # pragma: no cover - defensive
                    raise ValueError(
                        f"PyYAML is required to read template {file_path.name}. Install pyyaml to continue"
                    ) from exc
                with file_path.open("r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle)
            else:
                with file_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError(
                f"Template {channel}/{template_type} could not be parsed: {exc}"
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected IO errors
            raise ValueError(f"Failed to load template {channel}/{template_type}") from exc

        return ChannelTemplate.from_dict(data, channel=channel, template_type=template_type)

    def _load_from_database(
        self, channel: str, template_type: str, session: Session
    ) -> ChannelTemplate | None:
        template_row: SalesChannelTemplate | None = (
            session.query(SalesChannelTemplate)
            .filter(
                SalesChannelTemplate.channel_name == channel,
                SalesChannelTemplate.template_type == template_type,
            )
            .first()
        )
        if not template_row:
            return None
        try:
            data = json.loads(template_row.config_json)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Template {channel}/{template_type} in database is invalid JSON: {exc}"
            ) from exc
        return ChannelTemplate.from_dict(data, channel=channel, template_type=template_type)
