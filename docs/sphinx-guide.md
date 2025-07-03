# Sphinx 설치 방법 (pipx 기반)

이 문서는 Python 기반 문서화 도구인 Sphinx를 pipx로 설치하여 시스템에 안전하게 CLI 형태로 사용할 수 있도록 설정하는 절차를 설명합니다.  
pipx는 Python CLI 도구를 격리된 가상환경에 설치하고 전역적으로 실행 가능하게 만들어주는 도구입니다.

---

## 1. pipx 설치

### 1.1 macOS
```bash
brew install pipx
pipx ensurepath
```

터미널을 재시작하거나 다음 명령어로 환경변수가 적용되었는지 확인합니다:
```bash
echo $PATH
```

`~/.zshrc` 또는 `~/.bash_profile`에 다음을 추가해야 할 수도 있습니다:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 1.2 Windows (PowerShell)
```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

PowerShell을 닫았다가 다시 열어 환경 변수가 적용되었는지 확인합니다.

환경변수가 자동으로 설정되지 않은 경우, 아래 경로를 수동으로 추가합니다:
1. 시스템 환경변수 편집 열기
2. 사용자 변수 또는 시스템 변수에서 `Path` 선택 후 편집
3. 다음 경로를 추가:
```
%USERPROFILE%\AppData\Roaming\Python\Python312\Scripts
%USERPROFILE%\.local\bin
```
※ 사용 중인 Python 버전에 따라 `Python312`는 다를 수 있습니다.

또는, PowerShell에서 다음 명령어를 사용하여 일시적으로 환경변수에 경로를 추가할 수 있습니다:
```powershell
$env:Path += ";C:\Users\<사용자명>\AppData\Roaming\Python\Python312\Scripts"
```
※ `<사용자명>` 부분은 본인의 Windows 사용자 이름으로 대체하세요.

설치 확인:
```powershell
pipx --version
```

---

## 2. Sphinx 설치

pipx를 통해 Sphinx를 설치합니다:
```bash
pipx install sphinx
```

설치가 완료되면 다음 명령어들이 전역에서 사용 가능해야 합니다:
```bash
sphinx-quickstart --version
sphinx-apidoc --help
sphinx-build --help
```

---

## 3. 설치 확인

정상적으로 설치되었는지 다음 명령어로 확인합니다:
```bash
pipx list
```

출력 예시:
```makefile
venvs:
  sphinx (executable: sphinx-quickstart)
```

---

### 참고

- pipx는 각 도구별 가상환경을 자동 생성하므로 Python 프로젝트 환경과 충돌하지 않습니다.
- Sphinx를 삭제하고 싶을 경우:
```bash
pipx uninstall sphinx
```

이 문서는 Sphinx 설치 및 실행을 위한 준비 절차만을 다루며, 프로젝트 초기화나 문서 작성은 포함하지 않습니다.

---

## 4. Sphinx 프로젝트 초기화

프로젝트 루트 또는 별도 디렉토리에서 다음 명령어 실행합니다:
```bash
sphinx-quickstart docs
```

---

## 5. conf.py 설정 수정 (필수)
`docs/source/conf.py` 파일에서 다음 항목을 설정합니다.

### 5-1. 프로젝트 루트 경로 추가 (자동 문서화 위해 필요)

```python
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))  # 프로젝트 루트 경로
```

### 5-2. 확장 모듈 설정

```python
extensions = [
    'sphinx.ext.autodoc',     # docstring 기반 API 문서
    'sphinx.ext.napoleon',    # Google/NumPy 스타일 docstring 해석
    'sphinx.ext.viewcode',    # 소스코드 링크 보기
]
```