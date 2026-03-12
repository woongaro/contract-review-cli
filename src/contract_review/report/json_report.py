"""JSON 형식 리포트 저장."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def save_json(data: BaseModel | dict[str, Any], output_path: str | Path) -> Path:
    """Pydantic 모델 또는 dict를 JSON 파일로 저장합니다."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, BaseModel):
        json_str = json.dumps(data.model_dump(mode="json"), indent=2, ensure_ascii=False)
    else:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

    output_path.write_text(json_str, encoding="utf-8")
    return output_path
