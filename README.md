# Windows File Toolkit

파일 압축, 이름 변경, 자동 분류, 날짜 변경, 이미지 처리, PDF 도구, 파일 내용 검색을 지원하는 Windows 데스크톱 유틸리티입니다.

대량의 파일을 한 번에 처리할 수 있도록 설계되었으며, 원본 파일을 최대한 안전하게 보존하면서 복사/이동/분류 작업을 수행합니다.

## 주요 기능

- 파일 압축
  - Office 문서, PDF, HWPX 등 파일 크기 최적화
- 파일 이름 변경
  - 여러 파일의 이름을 일괄 변경
- 파일 자동 분류
  - 조건에 따라 파일을 폴더별로 자동 분류
- 파일 날짜 변경
  - 파일 생성일/수정일 변경
- 이미지 회전
  - 이미지 파일을 일괄 회전
- 이미지 비율 분류
  - 가로/세로 비율 조건에 맞는 이미지만 분류
  - 기준 이미지 기반 비율 조건 지원
- PDF 도구
  - PDF 관련 작업 지원
- 파일 내용 검색
  - 문서, 이미지, PDF 등에서 텍스트 검색
  - OCR 기반 검색 지원

## 실행 환경

- Windows
- Python 3.11 이상
- PySide6
- Pillow
- pypdf
- python-docx
- openpyxl

일부 기능은 외부 프로그램 설치 여부에 따라 지원 범위가 달라질 수 있습니다.

- PDF 압축: Ghostscript 필요
- HWP 처리: 한컴오피스 필요
- 일부 Office 자동화 기능: Microsoft Office 필요

## 설치 및 실행

개발 환경에서 실행하려면 다음 명령어를 사용합니다.

```bash
pip install -e ".[dev]"
python -m file_compressor_app.main
```

또는 설치된 스크립트를 사용할 수 있습니다.

```bash
file-compressor
```

## 빌드

Windows 실행 파일은 PyInstaller를 사용해 빌드할 수 있습니다.

```bash
pyinstaller file-compressor.spec
```

빌드 결과물은 `dist` 폴더에 생성됩니다.

## 사용 시 주의사항

- 대량 파일 처리 전에는 중요한 파일을 백업하는 것을 권장합니다.
- 이동 작업은 원본 파일 위치가 변경될 수 있습니다.
- 복사 작업은 원본 파일을 유지합니다.
- 같은 이름의 파일이 이미 존재하는 경우 자동으로 번호를 붙여 충돌을 방지합니다.
- 외부 프로그램이 필요한 기능은 해당 프로그램이 설치되어 있지 않으면 제한될 수 있습니다.

## 프로젝트 구조

```text
src/
  file_compressor/       핵심 파일 처리 로직
  file_compressor_app/   PySide6 기반 데스크톱 UI

tests/                   테스트 코드
docs/                    설계 및 구현 문서
dist/                    빌드 결과물
```

## 라이선스

라이선스는 아직 별도 지정하지 않았습니다.
