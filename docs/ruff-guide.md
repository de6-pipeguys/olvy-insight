# GitHub Actions 및 Ruff 린터 가이드

## Ruff란?
[Ruff](https://docs.astral.sh/ruff/)는 Python 코드의 스타일을 검사하고 포맷을 자동화할 수 있는 매우 빠른 린터이자 포매터입니다.  
이 프로젝트에서는 GitHub Actions를 통해 PR 시 자동으로 Ruff 검사를 수행하도록 설정되어 있습니다.

## 설치 방법

로컬 환경에서 Ruff를 수동으로 실행하려면 다음 명령어로 설치할 수 있습니다:

```bash
pip install ruff
```

또는 프로젝트 루트의 `requirements.txt` 파일을 통해 설치 가능합니다:

```bash
pip install -r requirements.txt
```

## 검사 명령어

Ruff를 수동으로 실행하려면 아래 명령어를 프로젝트 루트 디렉토리에서 실행합니다:

```bash
ruff check .
```

특정 파일만 검사하고 싶다면 다음과 같이 사용합니다:

```bash
ruff check 경로/파일명.py
```

## 자동 수정

가능한 항목을 자동으로 수정하고 싶다면 다음 명령어를 실행합니다:

```bash
ruff format .
```

특정 파일만 검사하고 싶다면 다음과 같이 사용합니다:

```bash
ruff format 경로/파일명.py
```

## GitHub Actions와 연동

PR을 생성하거나 커밋을 푸시하면 `.github/workflows/pr-check.yml`에 정의된 GitHub Actions가 실행되어 Ruff 검사를 자동으로 수행합니다.  
검사에 실패하면 PR에서 오류 로그를 확인할 수 있으며, 코드를 수정 후 다시 push하면 자동으로 재검사됩니다.

## 참고 파일

- Ruff 설정 파일: `ruff.toml`
- GitHub Actions 워크플로: `.github/workflows/pr-check.yml`

## 개발 규칙

- PR 전에 반드시 `ruff check .` 명령어로 코드 스타일 검사를 수행해주세요.
- 자동 수정을 사용할 경우 반드시 결과를 확인하고 예상치 못한 수정이 없는지 검토해주세요.

