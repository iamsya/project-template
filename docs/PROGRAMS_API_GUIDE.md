# Programs API 가이드

Programs 라우터의 모든 API 엔드포인트 가이드입니다.

## 목차

1. [프로그램 등록](#1-프로그램-등록)
2. [프로그램 목록 조회](#2-프로그램-목록-조회)
3. [프로그램 상세 조회](#3-프로그램-상세-조회)
4. [접근 가능한 공정 목록 조회](#4-접근-가능한-공정-목록-조회)
5. [프로그램 파일 다운로드](#5-프로그램-파일-다운로드)
6. [매핑용 프로그램 목록 조회](#6-매핑용-프로그램-목록-조회)
7. [사용자별 프로그램 목록 조회](#7-사용자별-프로그램-목록-조회)
8. [실패 파일 재시도](#8-실패-파일-재시도)
9. [실패 정보 조회](#9-실패-정보-조회)
10. [Knowledge 상태 동기화](#10-knowledge-상태-동기화)
11. [Knowledge 상태 조회](#11-knowledge-상태-조회)
12. [프로그램 일괄 삭제](#12-프로그램-일괄-삭제)

---

## 1. 프로그램 등록

PLC 프로그램을 등록하고 처리합니다.

### 엔드포인트

```
POST /v1/programs/register
```

### Content-Type

```
multipart/form-data
```

### 요청 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `ladder_zip` | File | **예** | PLC ladder logic 파일들이 포함된 ZIP 압축 파일 |
| `classification_xlsx` | File | **예** | 템플릿 분류체계 데이터 XLSX 파일 |
| `comment_csv` | File | **예** | PLC Ladder Comment CSV 파일 |
| `program_title` | string | **예** | PGM Name (프로그램 제목) |
| `process_id` | string | 아니오 | 공정 ID (드롭다운 선택, 선택사항) |
| `program_description` | string | 아니오 | 프로그램 설명 |
| `user_id` | string | 아니오 | 사용자 ID (기본값: "user") |

### 처리 단계

1. **유효성 검사** (동기): 파일 형식, 내용 검증
2. **즉시 응답 반환**: 유효성 검사 결과 반환
3. **백그라운드 처리** (비동기):
   - S3에 파일 업로드 및 ZIP 압축 해제
   - 템플릿 및 템플릿 데이터 생성
   - 데이터 전처리 및 Document 생성
   - Vector DB 인덱싱 요청

### 파일 형식 요구사항

#### `ladder_zip` (ZIP 파일)
- Logic 파일 (Program CSV 파일)을 ZIP으로 압축
- 압축 해제 후 각 로직 파일이 분리됨

#### `classification_xlsx` (XLSX 파일)
- 컬럼: `FOLDER_ID`, `FOLDER_NAME`, `SUB_FOLDER_NAME`, `LOGIC_ID`, `LOGIC_NAME`
- 로직 파일명과 매칭되어 템플릿 데이터 생성

#### `comment_csv` (CSV 파일)
- Ladder 로직의 device에 대한 코멘트 정보

### 응답 형식

#### 성공 시
```json
{
  "status": "success",
  "message": "파일 유효성 검사 성공",
  "data": {
    "program_id": "PGM_000001",
    "program_title": "공정1 PLC 프로그램",
    "status": "uploading",
    ...
  },
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": []
  }
}
```

#### 실패 시
```json
{
  "status": "validation_failed",
  "message": "유효성 검사 실패",
  "data": null,
  "validation_result": {
    "is_valid": false,
    "errors": ["에러 메시지 1", "에러 메시지 2"],
    "error_sections": {
      "분류체계 데이터 유효성 검사": ["에러 1", "에러 2"],
      "PLC Ladder 파일 유효성 검사": ["에러 3"]
    },
    "warnings": []
  }
}
```

### 사용 예시

```bash
curl -X POST "http://localhost:8000/v1/programs/register" \
  -F "ladder_zip=@ladder_files.zip" \
  -F "classification_xlsx=@classification.xlsx" \
  -F "comment_csv=@comment.csv" \
  -F "program_title=공정1 PLC 프로그램" \
  -F "process_id=process_001" \
  -F "user_id=user001"
```

---

## 2. 프로그램 목록 조회

프로그램 목록을 검색, 필터링, 페이지네이션, 정렬 기능으로 조회합니다.

### 엔드포인트

```
GET /v1/programs
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `user_id` | string | **예** | - | 사용자 ID (권한 기반 필터링용) |
| `program_id` | string | 아니오 | - | PGM ID로 검색 (정확한 일치) |
| `program_name` | string | 아니오 | - | 제목으로 검색 (부분 일치) |
| `process_id` | string | 아니오 | - | 공정 ID로 필터링 |
| `status` | string | 아니오 | - | 등록 상태로 필터링 |
| `create_user` | string | 아니오 | - | 작성자로 필터링 |
| `page` | integer | 아니오 | 1 | 페이지 번호 (최소: 1) |
| `page_size` | integer | 아니오 | 10 | 페이지당 항목 수 (최소: 1, 최대: 100) |
| `sort_by` | string | 아니오 | `create_dt` | 정렬 기준 (`create_dt`, `program_id`, `program_name`, `status`) |
| `sort_order` | string | 아니오 | `desc` | 정렬 순서 (`asc`, `desc`) |

### 등록 상태 (`status`)

- `preparing`: 준비 중
- `uploading`: 업로드 중
- `processing`: 처리 중
- `embedding`: 임베딩 중
- `completed`: 성공
- `failed`: 실패
- `indexing_failed`: 인덱싱 실패

### 권한 기반 필터링

- `user_id`는 필수 파라미터입니다
- 사용자의 권한 그룹에 따라 접근 가능한 공정의 PGM만 조회됩니다
  - **super 권한 그룹**: 모든 공정의 PGM 조회 가능
  - **plc 권한 그룹**: 지정된 공정의 PGM만 조회 가능

### 응답 형식

```json
{
  "items": [
    {
      "program_id": "PGM_000001",
      "program_name": "라벨부착 공정 PLC",
      "process_name": "모듈",
      "ladder_file_count": 645,
      "comment_file_count": 1,
      "status": "completed",
      "status_display": "완료",
      "processing_time": "10 min",
      "create_user": "정윤석",
      "create_dt": "2025-10-22T13:00:00"
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

### 사용 예시

```
GET /v1/programs?user_id=user001&page=1&page_size=10
GET /v1/programs?user_id=user001&process_id=process001&status=completed
GET /v1/programs?user_id=user001&program_name=라벨부착&sort_by=create_dt&sort_order=desc
```

---

## 3. 프로그램 상세 조회

프로그램의 상세 정보를 조회합니다 (팝업 상세 조회용).

### 엔드포인트

```
GET /v1/programs/{program_id}
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `program_id` | string | **예** | 프로그램 ID (PGM ID) |

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `user_id` | string | 아니오 | "user" | 사용자 ID (권한 검증용) |

### 응답 형식

```json
{
  "program_id": "PGM_000001",
  "program_title": "라벨부착 공정 PLC",
  "program_description": "공정1 라인용 PLC 프로그램",
  "process_id": "process_001",
  "process_name": "모듈",
  "user_id": "user001",
  "status": "completed",
  "error_message": null,
  "create_dt": "2025-10-22T13:00:00",
  "update_dt": "2025-10-22T14:00:00",
  "completed_at": "2025-10-22T14:10:00",
  "files": [
    {
      "file_type": "program_classification",
      "original_filename": "classification.xlsx",
      "file_size": 102400,
      "file_extension": ".xlsx",
      "download_file_type": "program_classification"
    },
    {
      "file_type": "program_logic",
      "original_filename": "ladder_files.zip",
      "file_size": 2048000,
      "file_extension": ".zip",
      "download_file_type": "program_logic"
    },
    {
      "file_type": "program_comment",
      "original_filename": "comment.csv",
      "file_size": 51200,
      "file_extension": ".csv",
      "download_file_type": "program_comment"
    }
  ],
  "ladder_file_count": 645,
  "comment_file_count": 1
}
```

### 파일 다운로드

응답의 `files` 배열에서 각 파일 정보를 확인하고, `download_file_type`과 `program_id`를 사용하여 다운로드 링크를 생성합니다:

```
GET /v1/programs/files/download?file_type={download_file_type}&program_id={program_id}&user_id={user_id}
```

### 사용 예시

```
GET /v1/programs/PGM_000001?user_id=user001
```

---

## 4. 접근 가능한 공정 목록 조회

사용자 권한에 따라 접근 가능한 공정 목록을 조회합니다 (드롭다운용).

### 엔드포인트

```
GET /v1/programs/processes
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `user_id` | string | **예** | 사용자 ID (권한 기반 필터링용) |

### 권한 기반 필터링

- **super 권한 그룹**: 모든 활성 공정 반환
- **plc 권한 그룹**: 지정된 공정만 반환
- **권한이 없으면**: 빈 배열 반환

### 응답 형식

```json
{
  "processes": [
    {
      "process_id": "process_001",
      "process_name": "모듈",
      "process_code": "MODULE"
    },
    {
      "process_id": "process_002",
      "process_name": "전극",
      "process_code": "ELECTRODE"
    }
  ]
}
```

### 사용 예시

```
GET /v1/programs/processes?user_id=user001
```

---

## 5. 프로그램 파일 다운로드

S3에 저장된 프로그램 관련 파일을 다운로드합니다.

### 엔드포인트

```
GET /v1/programs/files/download
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `file_type` | string | **예** | 파일 타입 (`program_classification`, `program_logic`, `program_comment`) |
| `program_id` | string | **예** | Program ID |
| `user_id` | string | **예** | 사용자 ID (권한 검증용) |

### 파일 타입

- `program_classification`: Program 분류 체계 엑셀 파일 (XLSX)
- `program_logic`: Program Logic 파일 (ZIP - Program CSV 파일 압축)
- `program_comment`: Program Comment 파일 (CSV)

### 응답

- 파일 다운로드 스트림 (Content-Disposition 헤더 포함)
- 원본 파일명으로 다운로드됨

### 사용 예시

```
GET /v1/programs/files/download?file_type=program_classification&program_id=PGM_000001&user_id=user001
GET /v1/programs/files/download?file_type=program_logic&program_id=PGM_000001&user_id=user001
GET /v1/programs/files/download?file_type=program_comment&program_id=PGM_000001&user_id=user001
```

---

## 6. 매핑용 프로그램 목록 조회

PLC-PGM 매핑 화면에서 사용할 프로그램 목록을 조회합니다.

### 엔드포인트

```
GET /v1/programs/mapping
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `program_id` | string | 아니오 | - | PGM ID로 검색 |
| `program_name` | string | 아니오 | - | 제목으로 검색 |
| `page` | integer | 아니오 | 1 | 페이지 번호 |
| `page_size` | integer | 아니오 | 10 | 페이지당 항목 수 |

### 응답 형식

```json
{
  "items": [
    {
      "program_id": "PGM_000001",
      "program_name": "라벨부착 공정 PLC",
      "ladder_file_count": 645,
      "comment_file_count": 1,
      "create_user": "정윤석",
      "create_dt": "2025-10-22T13:00:00"
    }
  ],
  "total_count": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

### 사용 예시

```
GET /v1/programs/mapping?page=1&page_size=10
GET /v1/programs/mapping?program_name=라벨부착
```

---

## 7. 사용자별 프로그램 목록 조회

특정 사용자가 생성한 프로그램 목록을 조회합니다.

### 엔드포인트

```
GET /v1/programs/user/{user_id}
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `user_id` | string | **예** | 사용자 ID |

### 응답 형식

```json
[
  {
    "program_id": "PGM_000001",
    "program_title": "라벨부착 공정 PLC",
    "status": "completed",
    ...
  }
]
```

### 사용 예시

```
GET /v1/programs/user/user001
```

---

## 8. 실패 파일 재시도

실패한 파일의 전처리 또는 Document 저장을 재시도합니다.

### 엔드포인트

```
POST /v1/programs/{program_id}/retry
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `program_id` | string | **예** | 프로그램 ID |

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `user_id` | string | 아니오 | "user" | 사용자 ID |
| `retry_type` | string | 아니오 | "all" | 재시도 타입 (`preprocessing`, `document`, `all`) |

### 재시도 타입

- `preprocessing`: 전처리 실패 파일만 재시도
- `document`: Document 저장 실패 파일만 재시도
- `all`: 모든 실패 파일 재시도

### 응답 형식

```json
{
  "program_id": "PGM_000001",
  "retry_type": "all",
  "retried_count": 5,
  "message": "재시도 완료"
}
```

### 사용 예시

```
POST /v1/programs/PGM_000001/retry?user_id=user001&retry_type=all
```

---

## 9. 실패 정보 조회

프로그램의 실패 정보 목록을 조회합니다.

### 엔드포인트

```
GET /v1/programs/{program_id}/failures
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `program_id` | string | **예** | 프로그램 ID |

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `user_id` | string | 아니오 | "user" | 사용자 ID |
| `failure_type` | string | 아니오 | - | 실패 타입 필터 (`preprocessing`, `document_storage`, `vector_indexing`) |

### 응답 형식

```json
{
  "program_id": "PGM_000001",
  "failures": [
    {
      "failure_id": "fail_001",
      "failure_type": "preprocessing",
      "error_message": "파일 파싱 실패",
      "source_type": "template_data",
      "source_id": "template_data_001",
      "create_dt": "2025-10-22T13:00:00"
    }
  ],
  "count": 1
}
```

### 사용 예시

```
GET /v1/programs/PGM_000001/failures?user_id=user001
GET /v1/programs/PGM_000001/failures?user_id=user001&failure_type=preprocessing
```

---

## 10. Knowledge 상태 동기화

Program의 Knowledge 상태를 외부 Knowledge API와 동기화합니다.

### 엔드포인트

```
POST /v1/programs/{program_id}/knowledge-status/sync
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `program_id` | string | **예** | 프로그램 ID |

### 응답 형식

```json
{
  "program_id": "PGM_000001",
  "synced_count": 10,
  "message": "동기화 완료"
}
```

### 사용 예시

```
POST /v1/programs/PGM_000001/knowledge-status/sync
```

---

## 11. Knowledge 상태 조회

Program의 Knowledge 상태를 조회합니다.

### 엔드포인트

```
GET /v1/programs/{program_id}/knowledge-status
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `program_id` | string | **예** | 프로그램 ID |

### 응답 형식

```json
{
  "program_id": "PGM_000001",
  "knowledge_references": [
    {
      "reference_id": "ref_001",
      "reference_type": "plc",
      "name": "Program Knowledge",
      "repo_id": "repo_001",
      "documents": [
        {
          "document_id": "doc_001",
          "status": "success",
          "name": "document1.json"
        }
      ],
      "document_count": 10
    }
  ],
  "total_references": 1
}
```

### 사용 예시

```
GET /v1/programs/PGM_000001/knowledge-status
```

---

## 12. 프로그램 일괄 삭제

여러 프로그램을 일괄 삭제합니다.

### 엔드포인트

```
DELETE /v1/programs
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `program_ids` | array[string] | **예** | 삭제할 프로그램 ID 리스트 |
| `user_id` | string | 아니오 | 사용자 ID (권한 확인용) |

### 응답 형식

```json
{
  "message": "3개의 프로그램이 삭제되었습니다.",
  "deleted_count": 3,
  "failed_count": 0,
  "results": [
    {
      "program_id": "PGM_000001",
      "success": true
    }
  ],
  "errors": [],
  "requested_ids": ["PGM_000001", "PGM_000002", "PGM_000003"]
}
```

### 사용 예시

```
DELETE /v1/programs?program_ids=PGM_000001&program_ids=PGM_000002&program_ids=PGM_000003&user_id=user001
```

---

## 에러 응답

모든 API는 다음과 같은 에러 응답 형식을 사용합니다:

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "에러 메시지",
  "detail": "상세 에러 정보"
}
```

### 주요 에러 코드

- `PROGRAM_NOT_FOUND`: 프로그램을 찾을 수 없음
- `PROGRAM_REGISTRATION_ERROR`: 등록 처리 중 오류
- `PERMISSION_DENIED`: 권한 없음
- `DATABASE_QUERY_ERROR`: 데이터베이스 쿼리 오류
- `VALIDATION_ERROR`: 입력값 검증 오류

---

## 참고사항

1. **권한 기반 필터링**: 목록 조회 API는 `user_id`가 필수이며, 사용자 권한에 따라 결과가 필터링됩니다.
2. **페이지네이션**: 기본값은 `page=1`, `page_size=10`입니다.
3. **검색**: `program_id`, `program_name`은 부분 일치 검색을 지원합니다.
4. **정렬**: 정렬 기준과 정렬 순서를 조합하여 사용할 수 있습니다.
5. **파일 다운로드**: 상세 조회 API에서 `files` 배열의 `download_file_type`을 사용하여 다운로드 링크를 생성합니다.

