# Windows File Toolkit

Windows에서 반복적인 파일 작업을 한 번에 처리하기 위한 데스크톱 유틸리티입니다.

파일 압축, 이름 변경, 자동 분류, 날짜 변경, 이미지 회전, 이미지 비율 분류, PDF 도구, 파일 내용 검색을 한 프로그램에서 사용할 수 있습니다.

[최신 버전 다운로드](https://github.com/HyeChang/windows-file-toolkit/releases/latest)

## 빠른 시작

1. [Releases](https://github.com/HyeChang/windows-file-toolkit/releases/latest)에서 실행 파일을 다운로드합니다.
2. 필요한 버전을 선택합니다.
3. 프로그램을 실행한 뒤 파일이나 폴더를 추가해 작업을 진행합니다.

## 어떤 파일을 받으면 되나요?

| 파일 | 추천 대상 | 설명 |
| --- | --- | --- |
| `FileCompressor.exe` | 일반 사용자 | 기본 실행 파일입니다. 대부분의 파일 작업, 이미지 도구, PDF 도구를 사용할 수 있습니다. |
| `FileCompressor-OCR.zip` | OCR 검색이 필요한 사용자 | OCR 런타임이 포함된 배포본입니다. 압축을 푼 뒤 `FileCompressor.exe`를 실행합니다. |
| `SHA256SUMS.txt` | 무결성 확인이 필요한 사용자 | 다운로드한 EXE/ZIP 파일이 정상인지 확인할 때 사용하는 체크섬 파일입니다. 필수 다운로드 파일은 아닙니다. |

직접 다운로드:

- [FileCompressor.exe](https://github.com/HyeChang/windows-file-toolkit/releases/latest/download/FileCompressor.exe)
- [FileCompressor-OCR.zip](https://github.com/HyeChang/windows-file-toolkit/releases/latest/download/FileCompressor-OCR.zip)

## 주요 기능

| 기능 | 설명 |
| --- | --- |
| 파일 압축 | Office 문서, PDF, HWPX 등 파일 크기를 줄입니다. |
| 파일 이름 변경 | 여러 파일의 이름을 규칙에 맞게 일괄 변경합니다. |
| 파일 자동 분류 | 파일명이나 조건을 기준으로 폴더별 자동 분류를 수행합니다. |
| 파일 날짜 변경 | 파일 생성일과 수정일을 변경합니다. |
| 이미지 회전 | 여러 이미지 파일을 한 번에 회전합니다. |
| 이미지 비율 분류 | 가로/세로 비율 조건에 맞는 이미지만 골라 이동하거나 복사합니다. |
| 기준 이미지 기반 분류 | 기준 이미지의 비율을 바탕으로 유사한 비율 조건을 계산합니다. |
| PDF 도구 | PDF 병합, 페이지 작업 등 PDF 관련 작업을 지원합니다. |
| 파일 내용 검색 | 문서, 이미지, PDF에서 텍스트를 검색합니다. OCR 기반 검색도 지원합니다. |

## 작업 방식

- 파일 또는 폴더를 추가합니다.
- 작업 옵션을 선택합니다.
- 미리보기로 처리 대상을 확인합니다.
- 적용 버튼으로 실제 작업을 실행합니다.

일부 작업은 이동과 복사를 선택할 수 있습니다. 이동은 원본 위치가 바뀌고, 복사는 원본을 유지합니다.

## 지원 환경

| 항목 | 내용 |
| --- | --- |
| 운영체제 | Windows |
| 개발 언어 | Python 3.11 이상 |
| UI | PySide6 |
| 이미지 처리 | Pillow |
| PDF 처리 | pypdf, Ghostscript 선택 지원 |
| 문서 처리 | python-docx, openpyxl, HWPX 처리 |

일부 기능은 외부 프로그램 설치 여부에 따라 지원 범위가 달라질 수 있습니다.

| 기능 | 추가 요구 사항 |
| --- | --- |
| PDF 압축 | Ghostscript 설치 필요 |
| HWP 처리 | 한컴오피스 설치 필요 |
| 일부 Office 자동화 | Microsoft Office 설치 필요 |
| OCR 검색 | OCR 포함 ZIP 또는 별도 Tesseract 설치 필요 |

## 사용 시 주의사항

- 대량 파일 처리 전에는 중요한 파일을 백업하는 것을 권장합니다.
- 이동 작업은 원본 파일의 위치가 변경됩니다.
- 복사 작업은 원본 파일을 유지합니다.
- 같은 이름의 파일이 이미 있으면 자동으로 번호를 붙여 충돌을 방지합니다.
- 외부 프로그램이 필요한 기능은 해당 프로그램이 없으면 제한되거나 건너뛸 수 있습니다.
- 배포 EXE는 코드 서명이 되어 있지 않을 수 있어 Windows 보안 경고가 표시될 수 있습니다.

## 개발 환경에서 실행

```bash
pip install -e ".[dev]"
python -m file_compressor_app.main
```

또는 설치된 스크립트를 사용할 수 있습니다.

```bash
file-compressor
```

## 빌드

Windows 실행 파일은 PyInstaller로 빌드합니다.

```bash
pyinstaller file-compressor.spec
```

또는 제공된 스크립트를 사용할 수 있습니다.

```powershell
.\scripts\build_exe.ps1
```

빌드 결과물은 로컬 `dist/` 폴더에 생성됩니다. `dist/`는 Git에는 포함하지 않고 GitHub Releases에 첨부하는 방식으로 배포합니다.

## 프로젝트 구조

```text
src/
  file_compressor/       핵심 파일 처리 로직
  file_compressor_app/   PySide6 기반 데스크톱 UI

tests/                   테스트 코드
scripts/                 빌드 및 배포 보조 스크립트
tools/                   번들 도구
docs/                    설계 및 구현 문서
```

## 라이선스

이 프로젝트는 MIT License를 사용합니다.
