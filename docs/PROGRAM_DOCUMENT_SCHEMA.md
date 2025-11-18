# 프로그램 테이블 및 문서 관리 스키마

## 개요

프로그램(Program)과 관련된 모든 문서와 데이터를 관리하는 데이터베이스 스키마입니다.

## 테이블 구조

### 1. PROGRAMS (프로그램 마스터)

프로그램의 기본 정보와 상태를 관리하는 메인 테이블입니다.

```sql
PROGRAMS
├── PROGRAM_ID (PK, String(50))          -- 프로그램 고유 ID
├── PROGRAM_NAME (String(255))           -- 프로그램 이름
├── DESCRIPTION (Text)                   -- 프로그램 설명
├── STATUS (String(50))                  -- 상태: preparing, uploading, processing, embedding, completed, failed, indexing_failed
├── ERROR_MESSAGE (Text)                 -- 에러 메시지
├── CREATE_DT (DateTime)                 -- 생성 일시
├── CREATE_USER (String(50))             -- 생성자
├── UPDATE_DT (DateTime)                 -- 수정 일시
├── UPDATE_USER (String(50))             -- 수정자
├── COMPLETED_AT (DateTime)              -- 완료 일시
├── IS_USED (Boolean)                    -- 사용 여부 (deprecated: is_deleted 사용)
├── IS_DELETED (Boolean, index=True)     -- 삭제 여부 (소프트 삭제, false인 것은 사용 중으로 인식)
├── DELETED_AT (DateTime)                -- 삭제 일시
└── DELETED_BY (String(50))              -- 삭제자
```

**상태 값:**
- `preparing`: 준비 중
- `uploading`: 업로드 중
- `processing`: 처리 중
- `embedding`: 임베딩 중
- `completed`: 완료
- `failed`: 실패
- `indexing_failed`: 인덱싱 실패

---

### 2. DOCUMENTS (통합 문서 테이블)

프로그램에 속한 모든 파일을 관리하는 테이블입니다.

```sql
DOCUMENTS
├── DOCUMENT_ID (PK, String(50))         -- 문서 고유 ID
├── DOCUMENT_NAME (String(255))          -- 문서 이름
├── ORIGINAL_FILENAME (String(255))      -- 원본 파일명
├── FILE_KEY (String(255))               -- S3 파일 키
├── FILE_SIZE (Integer)                  -- 파일 크기
├── FILE_TYPE (String(100))              -- MIME 타입
├── FILE_EXTENSION (String(10))          -- 파일 확장자
├── UPLOAD_PATH (String(500))            -- 업로드 경로
├── FILE_HASH (String(64))               -- 파일 해시
├── USER_ID (String(50))                 -- 사용자 ID
├── IS_PUBLIC (Boolean)                  -- 공개 여부
├── DOCUMENT_TYPE (String(20))           -- 문서 타입: common, type1, type2
├── STATUS (String(20))                  -- 전처리 및 벡터 임베딩 상태 (JSON 파일만 사용)
├── TOTAL_PAGES (Integer)                -- 전체 페이지 수
├── PROCESSED_PAGES (Integer)            -- 처리된 페이지 수
├── ERROR_MESSAGE (Text)                 -- 에러 메시지
├── MILVUS_COLLECTION_NAME (String(255)) -- Milvus 컬렉션명
├── VECTOR_COUNT (Integer)               -- 벡터 개수
├── LANGUAGE (String(10))                -- 언어
├── AUTHOR (String(255))                 -- 작성자
├── SUBJECT (String(500))                -- 주제
├── METADATA_JSON (JSON)                 -- 메타데이터
├── PROCESSING_CONFIG (JSON)             -- 처리 설정
├── PERMISSIONS (JSON)                   -- 권한 리스트
├── CREATE_DT (DateTime)                -- 생성 일시
├── UPDATED_AT (DateTime)                -- 수정 일시
├── PROCESSED_AT (DateTime)             -- 처리 일시
├── IS_DELETED (Boolean)                 -- 삭제 여부
│
├── PROGRAM_ID (FK → PROGRAMS.PROGRAM_ID, nullable=True, index=True)
├── DOCUMENT_TYPE (String(50), nullable=True, index=True)  -- 문서 타입 (통합)
├── SOURCE_DOCUMENT_ID (FK → DOCUMENTS.DOCUMENT_ID, nullable=True, index=True)  -- 원본 문서 참조
├── KNOWLEDGE_REFERENCE_ID (FK → KNOWLEDGE_REFERENCES.REFERENCE_ID, nullable=True, index=True)
└── FILE_ID (String(255))                -- 외부 파일 ID
```

**DOCUMENT_TYPE 값:**
- **Program 파일:**
  - `ladder_logic_zip`: 원본 ZIP 파일 (ladder logic 파일들)
  - `ladder_logic_json`: 전처리된 JSON 파일 (ZIP에서 압축 해제 후 전처리)
  - `comment`: PLC Ladder Comment 파일 (CSV)
  - `template`: Logic 분류 체계 파일 (XLSX)
- **Knowledge Reference 파일:**
  - `manual`: 미쯔비시 매뉴얼
  - `glossary`: 용어집
  - `plc`: Ladder Logic (프로그램 JSON 파일 벡터)
- **일반 문서:**
  - `common`, `type1`, `type2`

**STATUS 값:**
- **JSON 파일** (`document_type='ladder_logic_json'`):
  - `preprocessed`: 전처리 완료 (임베딩 대기) - 생성 시 기본값
  - `embedding`: 임베딩 진행 중
  - `embedded`: 임베딩 완료
  - `failed`: 전처리 또는 임베딩 실패
- **Knowledge Reference 파일** (`document_type='manual'`, `'glossary'`, `'plc'`):
  - `embedding`: 임베딩 진행 중
  - `embedded`: 임베딩 완료
  - `failed`: 임베딩 실패
  - (전처리 없이 바로 임베딩 대상)

**주의:**
- `status`는 전처리 및 임베딩 대상 파일만 사용
- 다른 파일(`ladder_logic_zip`, `comment`, `template`)은 `status=None`

**관계:**
- `program_id`: 프로그램에 속한 문서
- `source_document_id`: JSON 파일이 생성된 원본 ZIP 파일 참조
  - `document_type='ladder_logic_json'`인 Document는 `source_document_id`로 `document_type='ladder_logic_zip'`인 Document를 참조

---

### 3. TEMPLATES (템플릿 테이블)

프로그램의 템플릿 분류 체계를 관리합니다.

```sql
TEMPLATES
├── TEMPLATE_ID (PK, String(50))         -- 템플릿 고유 ID
├── DOCUMENT_ID (FK → DOCUMENTS.DOCUMENT_ID, nullable=False, index=True)  -- 분류체계 XLSX 파일
├── PROGRAM_ID (FK → PROGRAMS.PROGRAM_ID, nullable=True, index=True)
├── METADATA_JSON (JSON)                -- 메타데이터
├── CREATED_AT (DateTime)               -- 생성 일시
└── CREATED_BY (String(50))              -- 생성자
```

**관계:**
- `document_id`: 분류체계 XLSX 파일 (`document_type="template"`)
- `program_id`: 속한 프로그램

---

### 4. TEMPLATE_DATA (템플릿 데이터 테이블)

템플릿의 각 로직 파일 정보를 관리합니다.

```sql
TEMPLATE_DATA
├── TEMPLATE_DATA_ID (PK, String(50))   -- 템플릿 데이터 고유 ID
├── TEMPLATE_ID (FK → TEMPLATES.TEMPLATE_ID, nullable=False, index=True)
├── FOLDER_ID (String(100), nullable=True, index=True)      -- 폴더 ID
├── FOLDER_NAME (String(200), nullable=True)                 -- 폴더명
├── SUB_FOLDER_NAME (String(200), nullable=True)             -- 하위 폴더명
├── LOGIC_ID (String(100), nullable=False, index=True)       -- 로직 ID (파일명)
├── LOGIC_NAME (String(200), nullable=False)                 -- 로직명
├── DOCUMENT_ID (FK → DOCUMENTS.DOCUMENT_ID, nullable=True, index=True)  -- 전처리된 JSON 파일
├── ROW_INDEX (Integer, nullable=False) -- 엑셀 행 인덱스
├── METADATA_JSON (JSON)                -- 메타데이터
└── CREATED_AT (DateTime)               -- 생성 일시
```

**관계:**
- `template_id`: 속한 템플릿
- `document_id`: 전처리된 JSON 파일 (`document_type="ladder_logic_json"`)
  - 전처리 완료 후 각 로직 파일에 해당하는 JSON Document와 연결

---

### 5. PROCESSING_FAILURES (처리 실패 정보)

프로그램 처리 중 발생한 실패 정보를 관리합니다.

```sql
PROCESSING_FAILURES
├── FAILURE_ID (PK, String(50))         -- 실패 고유 ID
├── SOURCE_TYPE (String(50), nullable=False, index=True)     -- 참조 엔티티 타입: 'program', 'knowledge_reference'
├── SOURCE_ID (String(50), nullable=False, index=True)       -- 참조 엔티티 ID (program_id 등)
├── FAILURE_TYPE (String(50), nullable=False, index=True)   -- 실패 타입: preprocessing, document_storage, vector_indexing
├── FILE_PATH (String(500))             -- 파일 경로
├── FILE_INDEX (Integer)                -- 파일 인덱스
├── FILENAME (String(255))                -- 파일명
├── S3_PATH (String(500))               -- S3 경로
├── S3_KEY (String(500))                -- S3 키
├── ERROR_MESSAGE (Text, nullable=False) -- 에러 메시지
├── ERROR_DETAILS (JSON)                -- 에러 상세 정보
├── RETRY_COUNT (Integer)              -- 재시도 횟수
├── MAX_RETRY_COUNT (Integer)           -- 최대 재시도 횟수
├── STATUS (String(50))                 -- 상태: pending, retrying, resolved, failed
├── RESOLVED_AT (DateTime)              -- 해결 일시
├── LAST_RETRY_AT (DateTime)            -- 마지막 재시도 일시
├── RESOLVED_BY (String(50))            -- 해결자
├── METADATA_JSON (JSON)                -- 메타데이터
├── CREATED_AT (DateTime)               -- 생성 일시
└── UPDATED_AT (DateTime)               -- 수정 일시
```

**SOURCE_TYPE 값:**
- `program`: 프로그램 관련 실패
- `knowledge_reference`: 지식 참조 관련 실패

**FAILURE_TYPE 값:**
- `preprocessing`: 전처리 실패
- `document_storage`: 문서 저장 실패
- `vector_indexing`: 벡터 인덱싱 실패

**관계:**
- `source_type="program"`이고 `source_id=program_id`인 경우 프로그램 관련 실패

---

### 6. PROGRAM_LLM_DATA_CHUNKS (프로그램 LLM 데이터 청크)

프로그램의 LLM 데이터 청크를 관리합니다.

```sql
PROGRAM_LLM_DATA_CHUNKS
├── CHUNK_ID (PK, String(50))           -- 청크 고유 ID
├── PROGRAM_ID (FK → PROGRAMS.PROGRAM_ID, nullable=False, index=True)
├── DATA_TYPE (String(50), nullable=False, index=True)        -- 데이터 타입
├── DATA_VERSION (String(50), nullable=True, index=True)      -- 데이터 버전
├── CHUNK_INDEX (Integer, nullable=False)                     -- 청크 인덱스
├── TOTAL_CHUNKS (Integer, nullable=False)                    -- 전체 청크 수
├── CHUNK_SIZE (Integer, nullable=False)                      -- 청크 크기
├── TOTAL_SIZE (Integer)                -- 전체 크기
├── S3_BUCKET (String(255))             -- S3 버킷
├── S3_KEY (String(500), nullable=False) -- S3 키
├── S3_URL (String(1000))               -- S3 URL
├── FILE_HASH (String(64))               -- 파일 해시
├── CHECKSUM (String(64))                -- 체크섬
├── DESCRIPTION (Text)                  -- 설명
├── METADATA_JSON (JSON)                -- 메타데이터
├── STARTED_AT (DateTime)               -- 시작 일시
├── COMPLETED_AT (DateTime)             -- 완료 일시
└── UPDATED_AT (DateTime)               -- 수정 일시
```

**관계:**
- `program_id`: 속한 프로그램

---

## 테이블 간 관계도

```
PROGRAMS (1)
    │
    ├──→ DOCUMENTS (N)
    │       ├── program_id (FK)
    │       ├── document_type
    │       │   ├── "ladder_logic_zip" (원본 ZIP)
    │       │   ├── "ladder_logic_json" (전처리된 JSON) ──→ source_document_id ──→ DOCUMENTS (ladder_logic_zip)
    │       │   ├── "comment" (CSV)
    │       │   └── "template" (XLSX)
    │       └── source_document_id (FK → DOCUMENTS.DOCUMENT_ID)
    │
    ├──→ TEMPLATES (1)
    │       ├── program_id (FK)
    │       ├── document_id (FK → DOCUMENTS) ──→ template 파일
    │       │
    │       └──→ TEMPLATE_DATA (N)
    │               ├── template_id (FK)
    │               └── document_id (FK → DOCUMENTS) ──→ ladder_logic_json 파일
    │
    ├──→ PROCESSING_FAILURES (N)
    │       ├── source_type = "program"
    │       └── source_id = program_id
    │
    └──→ PROGRAM_LLM_DATA_CHUNKS (N)
            └── program_id (FK)
```

---

## 파일 타입별 Document 관리

### 1. 원본 ZIP 파일 (ladder_logic_zip)
```python
{
    "program_id": "program_001",
    "document_type": "ladder_logic_zip",
    "file_extension": "zip",
    "file_type": "application/zip",
    "source_document_id": None  # 원본이므로 없음
}
```

### 2. 전처리된 JSON 파일 (ladder_logic_json)
```python
{
    "program_id": "program_001",
    "document_type": "ladder_logic_json",
    "file_extension": "json",
    "file_type": "application/json",
    "source_document_id": "doc_zip_001",  # 원본 ZIP 파일 참조
    "metadata_json": {
        "processing_stage": "preprocessed",
        "logic_id": "logic_001.csv",
        "source_file_path": "s3://bucket/programs/program_001/unzipped/logic_001.csv"
    }
}
```

### 3. Comment 파일 (comment)
```python
{
    "program_id": "program_001",
    "document_type": "comment",
    "file_extension": "csv",
    "file_type": "text/csv",
    "source_document_id": None
}
```

### 4. Template 파일 (template)
```python
{
    "program_id": "program_001",
    "document_type": "template",
    "file_extension": "xlsx",
    "file_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "source_document_id": None
}
```

---

## 데이터 흐름

### 프로그램 등록 시 생성되는 Document

1. **등록 단계 (동기)**
   - `ladder_logic_zip` Document 생성 (상태: processing)
   - `comment` Document 생성 (상태: processing)
   - `template` Document 생성 (상태: processing)

2. **S3 업로드 후 (비동기)**
   - 각 Document의 `file_key`, `upload_path` 업데이트
   - ZIP 파일 압축 해제 → `unzipped_files` 목록 생성

3. **전처리 단계 (비동기)**
   - 각 unzipped 파일마다:
     - 전처리 수행 → JSON 생성
     - S3에 JSON 업로드
     - `ladder_logic_json` Document 생성
       - `source_document_id` = 원본 ZIP Document ID
       - `document_type` = "ladder_logic_json"
     - `TEMPLATE_DATA.document_id` 업데이트 (해당 JSON Document ID)

4. **임베딩 단계 (비동기)**
   - 각 `ladder_logic_json` Document에 대해:
     - Vector DB 인덱싱 요청
     - `is_embedded`, `vector_count` 업데이트

---

## 주요 쿼리 패턴

### 1. 프로그램의 모든 원본 파일 조회
```sql
SELECT * FROM DOCUMENTS
WHERE program_id = 'program_001'
  AND document_type IN ('ladder_logic_zip', 'comment', 'template')
  AND is_deleted = false;
```

### 2. 프로그램의 전처리된 JSON 파일 조회
```sql
SELECT * FROM DOCUMENTS
WHERE program_id = 'program_001'
  AND document_type = 'ladder_logic_json'
  AND is_deleted = false;
```

### 3. 특정 ZIP 파일에서 생성된 JSON 파일들 조회
```sql
SELECT * FROM DOCUMENTS
WHERE source_document_id = 'doc_zip_001'
  AND document_type = 'ladder_logic_json'
  AND is_deleted = false;
```

### 4. TemplateData와 연결된 JSON 파일 조회
```sql
SELECT td.*, d.*
FROM TEMPLATE_DATA td
JOIN DOCUMENTS d ON td.document_id = d.document_id
WHERE td.template_id IN (
    SELECT template_id FROM TEMPLATES WHERE program_id = 'program_001'
)
AND d.program_file_type = 'ladder_logic_json';
```

### 5. 프로그램의 실패 정보 조회
```sql
SELECT * FROM PROCESSING_FAILURES
WHERE source_type = 'program'
  AND source_id = 'program_001'
  AND status != 'resolved';
```

---

## 삭제 전략

### 프로그램 삭제 시

1. **PROGRAMS 테이블**
   - `is_deleted = true` (소프트 삭제)
   - `deleted_at = 현재 시간`
   - `deleted_by = 삭제자 ID`
   - `is_used`는 deprecated (호환성 유지용, 실제로는 사용하지 않음)

2. **DOCUMENTS 테이블**
   - 관련 모든 Document의 `is_deleted = true` (소프트 삭제)
   - JSON 파일의 경우 Vector DB에서 삭제된 경우 `status = 'failed'` (또는 별도 상태 관리)

3. **Vector DB 삭제**
   - 프로그램 삭제 시 관련 Document들을 Vector DB에서도 삭제
   - 삭제 완료 후 JSON 파일의 `status` 업데이트 (필요시)

4. **기타 테이블**
   - `PROCESSING_FAILURES`: 유지 (이력 관리)
   - `PROGRAM_LLM_DATA_CHUNKS`: 삭제 또는 유지 (정책에 따라)
   - `TEMPLATE_DATA`, `TEMPLATES`: 유지 (참조 무결성)

### 전처리 및 임베딩 상태 관리

**단일 상태 컬럼 (`status`)로 관리:**

**JSON 파일** (`document_type='ladder_logic_json'`):
- `preprocessed`: 전처리 완료 (임베딩 대기) - 생성 시 기본값
- `embedding`: 임베딩 진행 중
- `embedded`: 임베딩 완료
- `failed`: 전처리 또는 임베딩 실패

**Knowledge Reference 파일** (`knowledge_reference_id`가 있음):
- `embedding`: 임베딩 진행 중
- `embedded`: 임베딩 완료
- `failed`: 임베딩 실패
- (전처리 없이 바로 임베딩 대상)

**장점:**
- 전처리와 임베딩 상태를 하나의 컬럼으로 통합 관리
- 상태가 명확하고 직관적
- 확장 가능 (나중에 다른 상태 추가 가능)
- 쿼리가 간단해짐 (`WHERE status = 'embedded'`)

**상태 변경 시:**
- JSON 파일: 생성 시 `status = 'preprocessed'` → 임베딩 시작 시 `status = 'embedding'` → 임베딩 완료 시 `status = 'embedded'`
- Knowledge Reference 파일: 임베딩 시작 시 `status = 'embedding'` → 임베딩 완료 시 `status = 'embedded'`
- 실패 시: `status = 'failed'`

---

## Document 생성 및 Status 업데이트 가이드

### Document 생성

#### 1. CRUD 레이어 사용 (권장)

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document
from src.utils.uuid_gen import gen

# CRUD 인스턴스 생성
document_crud = DocumentCRUD(db)

# Document 생성
document_id = gen()
document_crud.create_document(
    document_id=document_id,
    document_name="프로그램명_template",
    original_filename="template.xlsx",
    file_key="programs/program_001/template.xlsx",
    file_size=1024,
    file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    file_extension="xlsx",
    user_id="user001",
    upload_path="s3://bucket/programs/program_001/template.xlsx",
    status=None,  # template 파일은 status 사용 안 함
    document_type=Document.TYPE_TEMPLATE,  # 상수 사용
    program_id="program_001",
    metadata_json={
        "program_id": "program_001",
        "program_title": "프로그램명",
    },
)
```

#### 2. JSON 파일 생성 (전처리 완료 상태)

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document
from src.utils.uuid_gen import gen

document_crud = DocumentCRUD(db)

# 전처리된 JSON 파일 생성
document_id = gen()
document_crud.create_document(
    document_id=document_id,
    document_name="프로그램명_processed_0",
    original_filename="processed_program_001_0.json",
    file_key="programs/program_001/processed/processed_program_001_0.json",
    file_size=2048,
    file_type="application/json",
    file_extension="json",
    user_id="user001",
    upload_path="s3://bucket/programs/program_001/processed/processed_program_001_0.json",
    status=Document.STATUS_PREPROCESSED,  # 전처리 완료 (임베딩 대기)
    document_type=Document.TYPE_LADDER_LOGIC_JSON,  # 상수 사용
    program_id="program_001",
    source_document_id="doc_zip_001",  # 원본 ZIP 파일 참조
    metadata_json={
        "program_id": "program_001",
        "processing_stage": "preprocessed",
        "logic_id": "logic_001.csv",
        "source_file_path": "s3://bucket/programs/program_001/unzipped/logic_001.csv",
    },
)
```

### Document Status 업데이트

#### 방법 1: `DocumentCRUD.update_document_status()` (권장)

가장 직접적이고 간단한 방법입니다.

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document

# CRUD 인스턴스 생성
document_crud = DocumentCRUD(db)

# Status 업데이트
success = document_crud.update_document_status(
    document_id="doc_001",
    status=Document.STATUS_EMBEDDED,  # 상수 사용
    error_message=None  # 선택사항
)

# 실패 시 에러 메시지 포함
success = document_crud.update_document_status(
    document_id="doc_001",
    status=Document.STATUS_FAILED,
    error_message="임베딩 중 오류 발생: Connection timeout"
)
```

**함수 시그니처:**
```python
def update_document_status(
    self, 
    document_id: str, 
    status: str, 
    error_message: str = None
) -> bool:
    """
    문서 상태 업데이트
    
    Args:
        document_id: 문서 ID
        status: 상태 값 (Document.STATUS_* 상수 사용 권장)
        error_message: 에러 메시지 (선택사항)
        
    Returns:
        bool: 업데이트 성공 여부
        
    Note:
        - status가 'completed'인 경우 processed_at도 자동 업데이트
        - updated_at은 항상 자동 업데이트
    """
```

#### 방법 2: `DocumentService.update_document_processing_status()` (서비스 레이어)

권한 체크가 필요하거나 추가 처리 정보를 함께 업데이트할 때 사용합니다.

```python
from src.api.services.document_service import DocumentService
from shared_core.models import Document

# 서비스 인스턴스 생성
document_service = DocumentService(db)

# Status 및 추가 처리 정보 업데이트
success = document_service.update_document_processing_status(
    document_id="doc_001",
    status=Document.STATUS_EMBEDDED,
    user_id="user001",  # 권한 체크용
    vector_count=100,  # 추가 정보 (선택사항)
    milvus_collection_name="collection_001",  # 추가 정보 (선택사항)
    total_pages=10,  # 추가 정보 (선택사항)
    processed_pages=10,  # 추가 정보 (선택사항)
)
```

**함수 시그니처:**
```python
def update_document_processing_status(
    self,
    document_id: str,
    status: str,
    user_id: str = None,
    **processing_info
) -> bool:
    """
    문서 처리 상태 및 정보 업데이트
    
    Args:
        document_id: 문서 ID
        status: 상태 값 (Document.STATUS_* 상수 사용 권장)
        user_id: 사용자 ID (권한 체크용, 선택사항)
        **processing_info: 추가 처리 정보 (vector_count, milvus_collection_name 등)
        
    Returns:
        bool: 업데이트 성공 여부
        
    Raises:
        PermissionError: 권한이 없는 경우
    """
```

#### 방법 3: `DocumentCRUD.update_document()` (일반 업데이트)

여러 필드를 함께 업데이트할 때 사용합니다.

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document

document_crud = DocumentCRUD(db)

# Status와 다른 필드 함께 업데이트
success = document_crud.update_document(
    document_id="doc_001",
    status=Document.STATUS_EMBEDDED,
    vector_count=100,
    milvus_collection_name="collection_001",
    error_message=None
)
```

### Status 상수 사용

모든 status 값은 `Document` 모델의 상수를 사용하는 것을 권장합니다:

```python
from shared_core.models import Document

# Status 상수
Document.STATUS_PREPROCESSED  # 전처리 완료 (JSON 파일 전용)
Document.STATUS_EMBEDDING     # 임베딩 진행 중
Document.STATUS_EMBEDDED     # 임베딩 완료
Document.STATUS_FAILED        # 실패
Document.STATUS_COMPLETED     # 완료 (Knowledge Reference 파일 전용)

# Document Type 상수
Document.TYPE_LADDER_LOGIC_ZIP   # 원본 ZIP 파일
Document.TYPE_LADDER_LOGIC_JSON  # 전처리된 JSON 파일
Document.TYPE_COMMENT            # 코멘트 CSV 파일
Document.TYPE_TEMPLATE           # 템플릿 XLSX 파일
Document.TYPE_MANUAL             # 매뉴얼 파일
Document.TYPE_GLOSSARY           # 용어집 파일
Document.TYPE_PLC                # PLC 레포 파일
```

### 사용 예시

#### 예시 1: 전처리 완료 후 Status 설정

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document

document_crud = DocumentCRUD(db)

# 전처리 완료 후 Document 생성
document_id = gen()
document_crud.create_document(
    document_id=document_id,
    document_name="프로그램명_processed_0",
    original_filename="processed_program_001_0.json",
    file_key="programs/program_001/processed/processed_program_001_0.json",
    file_size=2048,
    file_type="application/json",
    file_extension="json",
    user_id="user001",
    upload_path="s3://bucket/programs/program_001/processed/processed_program_001_0.json",
    status=Document.STATUS_PREPROCESSED,  # 전처리 완료
    document_type=Document.TYPE_LADDER_LOGIC_JSON,
    program_id="program_001",
    source_document_id="doc_zip_001",
)
```

#### 예시 2: 임베딩 시작 시 Status 업데이트

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document

document_crud = DocumentCRUD(db)

# 임베딩 시작 시 status 업데이트
document_crud.update_document_status(
    document_id="doc_001",
    status=Document.STATUS_EMBEDDING
)
```

#### 예시 3: 임베딩 완료 시 Status 업데이트

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document

document_crud = DocumentCRUD(db)

# 임베딩 완료 시 status 및 벡터 정보 업데이트
document_crud.update_document(
    document_id="doc_001",
    status=Document.STATUS_EMBEDDED,
    vector_count=100,
    milvus_collection_name="collection_001"
)
```

#### 예시 4: 임베딩 실패 시 Status 업데이트

```python
from src.database.crud.document_crud import DocumentCRUD
from shared_core.models import Document

document_crud = DocumentCRUD(db)

# 임베딩 실패 시 status 및 에러 메시지 업데이트
document_crud.update_document_status(
    document_id="doc_001",
    status=Document.STATUS_FAILED,
    error_message="임베딩 중 오류 발생: Vector DB connection timeout"
)
```

### Status 흐름

#### JSON 파일 (`document_type='ladder_logic_json'`)

```
생성 시: STATUS_PREPROCESSED
    ↓
임베딩 시작: STATUS_EMBEDDING
    ↓
임베딩 완료: STATUS_EMBEDDED ✅
    ↓
실패 시: STATUS_FAILED ❌
```

#### Knowledge Reference 파일 (`document_type='manual'`, `'glossary'`, `'plc'`)

```
임베딩 시작: STATUS_EMBEDDING
    ↓
임베딩 완료: STATUS_EMBEDDED ✅
    ↓
완료: STATUS_COMPLETED ✅
    ↓
실패 시: STATUS_FAILED ❌
```

### 주의사항

1. **Status는 전처리 및 임베딩 대상 파일만 사용**
   - `ladder_logic_zip`, `comment`, `template` 파일은 `status=None`
   - `ladder_logic_json` 및 Knowledge Reference 파일만 status 사용

2. **상수 사용 권장**
   - 하드코딩된 문자열 대신 `Document.STATUS_*` 상수 사용
   - 오타 방지 및 타입 안정성 향상

3. **에러 메시지**
   - 실패 시 `error_message` 파라미터에 상세한 에러 정보 저장
   - 디버깅 및 문제 추적에 유용

4. **트랜잭션 관리**
   - `update_document_status()`는 자동으로 commit 처리
   - 여러 Document를 업데이트할 때는 트랜잭션 관리 필요

