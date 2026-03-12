# contract-review-cli

한국 법령(근로기준법, 민법, 주택임대차보호법 등)에 기반한 **계약서 자동 검토 CLI 도구**입니다.


<img width="1024" height="559" alt="image" src="https://github.com/user-attachments/assets/fa4b1335-e21e-462b-8846-f1e714fe35d9" />


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

# 비대화형/자동화 환경에서는 위험고지 확인 옵션 필요
contract-review review contract.pdf --ack-risk --output report.md

# 직접 식별자를 1차 마스킹한 뒤 검토
contract-review review contract.pdf --ack-risk --redact --output report.md

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

# 비대화형/자동화 환경 예시
contract-review diff old.pdf new.pdf --ack-risk --output diff_report.md

# 직접 식별자를 1차 마스킹한 뒤 비교
contract-review diff old.pdf new.pdf --ack-risk --redact --output diff_report.md
```

### 조항 개선 제안

```bash
# 조항 ID로 지정 (예: 제3조, 1.2)
contract-review suggest contract.pdf --clause "제3조"

# JSON으로 저장
contract-review suggest contract.pdf --clause "제3조" --output suggestion.json

# 비대화형/자동화 환경 예시
contract-review suggest contract.pdf --clause "제3조" --ack-risk --output suggestion.json

# 직접 식별자를 1차 마스킹한 뒤 조항 제안 생성
contract-review suggest contract.pdf --clause "제3조" --ack-risk --redact --output suggestion.json
```

- `suggest --clause`는 정규화된 조항 ID로 조회합니다.
  - 예: 파싱 결과가 `제3조 (용역 범위)`로 보여도 `--clause "제3조"`로 조회할 수 있습니다.
  - 중첩 항/호/목이 많은 계약서는 먼저 `parse`로 실제 조항 ID를 확인한 뒤 사용하는 것을 권장합니다.

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

프롬프트 본문은 명령행 인자가 아니라 `stdin`으로 전달합니다. Windows의 명령행 길이 제한과
프로세스 인자 노출 위험을 줄이기 위한 동작입니다.

민감한 계약서는 선택한 LLM CLI 백엔드로 전송될 수 있으므로, 사내 정책 또는 고객 계약상 외부 전송이
허용되는 문서에만 사용하십시오.

`review`, `diff`, `suggest`는 실행 시점에 위험고지를 출력합니다. 대화형 터미널에서는 확인 프롬프트가 나오고,
비대화형 환경(CI, 스크립트, 파이프라인 등)에서는 `--ack-risk`를 명시해야 실행됩니다.

`--redact`를 사용하면 LLM 전송 전에 이메일, 전화번호, 주민등록번호 형식, 사업자등록번호 형식,
UUID 같은 직접 식별자를 정규식으로 1차 마스킹합니다. 다만 이름, 주소, 자유서술 맥락까지 완전히 익명화하지는 않습니다.

기본 백엔드는 환경 변수로 바꿀 수 있습니다.

```bash
# 예시
DEFAULT_LLM=gemini
```

LLM 응답을 JSON으로 파싱하지 못한 경우에도 원본 응답 전문은 결과에 다시 출력하지 않습니다.
계약 내용이 에러 메시지에 재노출되는 것을 줄이기 위한 동작입니다.

## 입력 파일 및 인코딩

- `parse`, `review`, `suggest`는 PDF와 텍스트 파일을 처리할 수 있습니다.
- 텍스트 파일은 `utf-8`, `utf-8-sig`, `cp949`, `euc-kr` 인코딩을 순서대로 시도합니다.
- `review`는 파싱된 전체 조항을 기준으로 검토하며, 많은 조항이 있어도 조용히 잘라내지 않습니다.

## 보안/운영 권장사항

- 실계약 원문, 추출 텍스트, JSON 산출물은 자동 삭제되지 않습니다. 검토 후 보관 정책에 따라 수동 정리하십시오.
- 외부 전송이 금지된 계약서는 이 도구로 직접 검토하지 말고, 사내 승인된 폐쇄형 환경이나 로컬 전용 대안을 사용하십시오.
- `--redact`는 직접 식별자 일부만 마스킹하는 보조 장치이며, 완전한 비식별화나 법적 익명화 요구사항 충족을 보장하지 않습니다.
- 생성된 결과는 법률 자문이 아니라 초안/검토 보조 자료로 사용하고, 최종 판단은 변호사 또는 담당자 검토를 거치십시오.

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

> **위험고지: 이 도구는 AI가 생성한 참고 자료를 제공합니다.**
> 실제 법률 문제는 반드시 변호사와 상담하십시오.
> AI의 분석은 법률 자문을 대체하지 않습니다.
> 선택한 LLM CLI 백엔드로 계약 텍스트가 전송될 수 있으므로, 외부 전송이 금지된 문서에는 사용하지 마십시오.
> `--redact`는 일부 직접 식별자만 마스킹하며 완전한 익명화를 보장하지 않습니다.
> 실계약 원문, 추출 텍스트, JSON 산출물은 자동 삭제되지 않으므로 검토 후 보관 정책에 따라 수동 정리하십시오.

## 라이선스

MIT License
