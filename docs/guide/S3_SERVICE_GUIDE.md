# S3 서비스 가이드

S3 업로드/다운로드 통합 서비스 사용 가이드입니다.

## 개요

`S3Service`는 프로그램 등록 시 S3 업로드와 프로그램 상세 조회/기준정보 조회 화면에서 파일 다운로드를 위한 통합 서비스입니다.

## 설정

### 환경 변수

`.env` 파일에 다음 설정을 추가하세요:

```bash
# S3 버킷 이름 (필수)
S3_BUCKET_NAME=my-s3-bucket

# AWS 리전 (기본값: ap-northeast-2)
AWS_REGION=ap-northeast-2

# AWS 자격 증명 (선택사항)
# - 환경변수에서 자동으로 찾음 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
# - 또는 ~/.aws/credentials 파일 사용
# - 또는 IAM 역할 사용 (EC2, ECS, Lambda 등)
# AWS_ACCESS_KEY_ID=your-access-key-id
# AWS_SECRET_ACCESS_KEY=your-secret-access-key
```

### 설정 파일

`src/config/simple_settings.py`에 S3 설정이 자동으로 포함됩니다:

- `s3_bucket_name`: S3 버킷 이름 (S3_BUCKET_NAME 환경변수)
- `aws_region`: AWS 리전 (기본값: ap-northeast-2)
- `aws_access_key_id`: AWS Access Key ID (선택사항)
- `aws_secret_access_key`: AWS Secret Access Key (선택사항)

## 사용 방법

### 의존성 주입

FastAPI의 의존성 주입을 통해 사용합니다:

```python
from fastapi import Depends
from src.core.dependencies import get_s3_service
from src.api.services.s3_service import S3Service

@router.post("/upload")
async def upload_file(
    file: UploadFile,
    s3_service: S3Service = Depends(get_s3_service),
):
    # S3 서비스 사용
    pass
```

### 업로드 기능

#### 1. 단일 파일 업로드

```python
# UploadFile 업로드
s3_path = await s3_service.upload_file(
    file=upload_file,
    s3_key="programs/PGM_000001/ladder_logic.zip",
    content_type="application/zip",
)

# 바이트 데이터 업로드
s3_path = await s3_service.upload_bytes(
    content=file_bytes,
    s3_key="programs/PGM_000001/data.bin",
    content_type="application/octet-stream",
)

# 문자열 업로드
s3_path = await s3_service.upload_string(
    content=json_string,
    s3_key="programs/PGM_000001/data.json",
    content_type="application/json",
)
```

#### 2. ZIP 파일 업로드 및 압축 해제

```python
# ZIP 파일을 업로드하고 압축 해제하여 각 파일을 개별적으로 업로드
uploaded_files = await s3_service.upload_zip_and_extract(
    zip_file=ladder_zip,
    s3_prefix="programs/PGM_000001/unzipped/",
)
# 반환: ["programs/PGM_000001/unzipped/file1.csv", ...]
```

#### 3. 프로그램 파일 일괄 업로드

```python
# 프로그램 등록 시 필요한 파일들을 일괄 업로드
s3_paths = await s3_service.upload_program_files(
    ladder_zip=ladder_zip,
    classification_xlsx=classification_xlsx,
    comment_csv=comment_csv,
    program_id="PGM_000001",
)
# 반환:
# {
#     "ladder_zip_path": "s3://bucket/programs/PGM_000001/ladder_logic.zip",
#     "unzipped_base_path": "programs/PGM_000001/unzipped/",
#     "unzipped_files": ["programs/PGM_000001/unzipped/file1.csv", ...],
#     "classification_xlsx_path": "s3://bucket/programs/PGM_000001/classification.xlsx",
#     "comment_csv_path": "s3://bucket/programs/PGM_000001/comment.csv"
# }
```

### 다운로드 기능

#### 1. 단일 파일 다운로드

```python
# S3 키로 직접 다운로드
file_content, filename, content_type = s3_service.download_file(
    s3_key="programs/PGM_000001/ladder_logic.zip",
    filename="ladder_logic.zip",  # 선택사항
)
```

#### 2. 프로그램 파일 다운로드

```python
# file_type + program_id 방식
file_content, filename, content_type = s3_service.download_program_file(
    file_type="program_classification",  # 또는 "program_logic", "program_comment"
    program_id="PGM_000001",
    db_session=db,
)
```

#### 3. Document ID로 다운로드

```python
# Document ID로 직접 다운로드
file_content, filename, content_type = s3_service.download_file_by_document_id(
    document_id="doc_001",
    db_session=db,
)
```

### 삭제 기능

#### 1. 단일 파일 삭제

```python
success = await s3_service.delete_file(
    s3_key="programs/PGM_000001/ladder_logic.zip",
)
```

#### 2. Prefix로 일괄 삭제

```python
# 특정 prefix를 가진 모든 파일 삭제
deleted_count = await s3_service.delete_files_by_prefix(
    prefix="programs/PGM_000001/",
)
```

## 프로그램 등록 API에서 사용 예시

```python
from src.core.dependencies import get_s3_service
from src.api.services.s3_service import S3Service

@router.post("/register")
async def register_program(
    ladder_zip: UploadFile,
    classification_xlsx: UploadFile,
    comment_csv: UploadFile,
    s3_service: S3Service = Depends(get_s3_service),
):
    # 프로그램 파일 업로드
    s3_paths = await s3_service.upload_program_files(
        ladder_zip=ladder_zip,
        classification_xlsx=classification_xlsx,
        comment_csv=comment_csv,
        program_id="PGM_000001",
    )
    
    # s3_paths를 사용하여 DB에 저장
    # ...
```

## 프로그램 상세 조회/기준정보 조회에서 사용 예시

```python
from fastapi.responses import StreamingResponse
from src.core.dependencies import get_s3_service
from src.api.services.s3_service import S3Service

@router.get("/files/download")
async def download_file(
    file_type: str,
    program_id: str,
    s3_service: S3Service = Depends(get_s3_service),
    db: Session = Depends(get_db),
):
    # 파일 다운로드
    file_content, filename, content_type = s3_service.download_program_file(
        file_type=file_type,
        program_id=program_id,
        db_session=db,
    )
    
    # StreamingResponse로 반환
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

## 에러 처리

S3 서비스는 다음과 같은 예외를 발생시킬 수 있습니다:

- `ValueError`: S3 클라이언트가 초기화되지 않은 경우
- `FileNotFoundError`: 파일을 찾을 수 없는 경우
- `Exception`: 기타 S3 작업 실패 시

```python
try:
    s3_path = await s3_service.upload_file(file, s3_key)
except ValueError as e:
    # S3 클라이언트 초기화 실패
    logger.error(f"S3 서비스 사용 불가: {e}")
except FileNotFoundError as e:
    # 파일을 찾을 수 없음
    logger.error(f"파일 없음: {e}")
except Exception as e:
    # 기타 오류
    logger.error(f"S3 작업 실패: {e}")
```

## 서비스 사용 가능 여부 확인

```python
if s3_service.is_available():
    # S3 서비스 사용 가능
    s3_path = await s3_service.upload_file(file, s3_key)
else:
    # S3 서비스 사용 불가 (로컬 개발 환경 등)
    logger.warning("S3 서비스가 비활성화되어 있습니다.")
```

## 주의사항

1. **환경 변수 설정**: S3 버킷 이름이 설정되지 않으면 S3 기능이 비활성화됩니다.
2. **자격 증명**: AWS 자격 증명은 환경 변수, 자격 증명 파일, IAM 역할 순서로 자동으로 찾습니다.
3. **비동기 처리**: 업로드/삭제 메서드는 `async`이지만, 다운로드 메서드는 동기입니다.
4. **에러 처리**: S3 작업 실패 시 적절한 예외 처리를 해야 합니다.

