# contract-review

한국 법령(근로기준법, 민법, 주택임대차보호법 등)에 기반한 **계약서 자동 검토 CLI 도구**입니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| `review` | 계약서를 조항별로 검토하고 법적 위험을 분석합니다 |
| `diff` | 두 버전의 계약서를 비교하여 변경 사항과 위험도를 평가합니다 |
| `suggest` | 특정 조항의 개선 문구를 한국 법령에 맞게 제안합니다 |
| `parse` | 계약서를 조항 단위로 파싱하여 구조화합니다 |

## 지원 계약서 유형 및 적용 법령

| 유형 | 적용 법령 |
|------|-----------|
| 근로계약 | 근로기준법, 최저임금법, 남녀고용평등법 |
| 용역/도급 | 민법, 하도급법 |
| 임대차 | 주택임대차보호법, 상가임대차보호법 |
| 비밀유지(NDA) | 영업비밀보호법, 부정경쟁방지법 |
| 기타 | 민법 일반 원칙 |

## 설치

### 요구 사항

- Python 3.11 이상
- [uv](https://github.com/astral-sh/uv) (권장) 또는 pip

### uv로 설치 (권장)

```bash
git clone https://github.com/yourusername/contract-review.git
cd contract-review

# 가상환경 생성 및 의존성 설치
uv sync --all-extras

# 개발 모드 설치
uv pip install -e .
```

### pip으로 설치

```bash
pip install -e .
```

## 사전 준비 — LLM CLI 설치

**API 키 설정이 필요 없습니다.** 각 LLM CLI 도구가 인증을 자체 처리합니다.

| 백엔드 | CLI 도구 | 설치 |
|--------|----------|------|
| `claude` (기본값) | Claude Code | https://claude.ai/code |
| `gemini` | Gemini CLI | https://ai.google.dev/gemini-api/docs/gemini-cli |
| `openai` | OpenAI Codex CLI | https://github.com/openai/codex |

사용할 CLI가 PATH에 등록되어 있어야 합니다:
```bash
which claude   # Claude Code
which gemini   # Gemini CLI
which codex    # OpenAI Codex CLI
```

## 사용법

### 계약서 검토

```bash
# 기본 (Claude 사용, 결과를 터미널에 출력)
contract-review review contract.pdf

# Markdown 리포트 저장
contract-review review contract.pdf --output report.md

# JSON 형식 저장
contract-review review contract.pdf --output report.json

# Gemini 사용
contract-review review contract.pdf --llm gemini

# 계약서 유형 강제 지정 (자동 감지 대신)
contract-review review contract.pdf --type employment
```

### 두 계약서 비교

```bash
contract-review diff old_contract.pdf new_contract.pdf

# 리포트 저장
contract-review diff old.pdf new.pdf --output diff_report.md
```

### 조항 개선 제안

```bash
# 조항 ID로 지정 (예: 제3조, 1.2)
contract-review suggest contract.pdf --clause "제3조"

# JSON으로 저장
contract-review suggest contract.pdf --clause "제3조" --output suggestion.json
```

### 조항 파싱

```bash
# 파싱 결과를 JSON으로 저장
contract-review parse contract.pdf --output clauses.json
```

## LLM 백엔드 선택

`--llm` 옵션으로 LLM 백엔드를 선택합니다 (API 키 불필요):

| 값 | 사용 CLI | 설명 |
|----|----------|------|
| `claude` (기본값) | `claude --print` | Claude Code CLI |
| `gemini` | `gemini` | Gemini CLI |
| `openai` | `codex --quiet` | OpenAI Codex CLI |

## 개발

### 테스트 실행

```bash
# uv
uv run pytest

# pip
pytest
```

### 코드 품질 검사

```bash
uv run ruff check src/
uv run mypy src/
```

## 프로젝트 구조

```
contract-review/
├── src/contract_review/
│   ├── cli.py              # Typer CLI 진입점
│   ├── models/             # Pydantic 데이터 모델
│   ├── parser/             # PDF/텍스트 파서
│   ├── analyzer/           # 검토·비교·제안 분석기
│   ├── llm/                # LLM 백엔드 (Claude, Gemini, OpenAI)
│   ├── prompts/            # 한국 법령 기반 프롬프트
│   └── report/             # JSON/Markdown 리포트 생성
└── tests/
```

## 주의 사항

> **이 도구는 AI가 생성한 참고 자료를 제공합니다.**
> 실제 법률 문제는 반드시 변호사와 상담하십시오.
> AI의 분석은 법률 자문을 대체하지 않습니다.

## 라이선스

MIT License
