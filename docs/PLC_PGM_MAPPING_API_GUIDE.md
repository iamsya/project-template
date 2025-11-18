# PLC-PGM 매핑 API 가이드

PLC-PGM 매핑 화면에서 사용하는 API 가이드입니다.

## 목차

1. [드롭다운 데이터 조회](#1-드롭다운-데이터-조회)
2. [PLC 기준 정보 조회](#2-plc-기준-정보-조회)
3. [PGM 프로그램 조회](#3-pgm-프로그램-조회)

---

## 1. 드롭다운 데이터 조회

PLC-PGM 매핑 화면에서 사용할 Plant, 공정, Line 드롭다운 데이터를 조회합니다.

### 엔드포인트

```
GET /v1/plcs/mapping/dropdown
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `user_id` | string | **예** | - | 사용자 ID (권한 기반 필터링용) |

### 권한 기반 필터링

- `user_id`는 필수 파라미터입니다.
- 공정은 사용자 권한에 따라 필터링됩니다:
  - **super 권한 그룹**: 모든 활성 공정 반환
  - **plc 권한 그룹**: 지정된 공정만 반환
  - **권한이 없으면**: 공정 목록이 비어있음

### 응답 형식

```json
{
  "plants": [
    {
      "id": "KY1",
      "code": "KY1",
      "name": "KY1"
    },
    {
      "id": "KY2",
      "code": "KY2",
      "name": "KY2"
    }
  ],
  "processesByPlant": {
    "KY1": [
      {
        "id": "process_001",
        "code": "MODULE",
        "name": "모듈"
      },
      {
        "id": "process_002",
        "code": "ELECTRODE",
        "name": "전극"
      }
    ],
    "KY2": [
      {
        "id": "process_003",
        "code": "ASSEMBLY",
        "name": "조립"
      }
    ]
  },
  "linesByProcess": {
    "process_001": [
      {
        "id": "line_001",
        "name": "1라인"
      },
      {
        "id": "line_002",
        "name": "2라인"
      }
    ],
    "process_002": [
      {
        "id": "line_001",
        "name": "1라인"
      },
      {
        "id": "line_002",
        "name": "2라인"
      }
    ]
  }
}
```

### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `plants` | array | Plant 목록 (첫 번째 드롭다운) |
| `plants[].id` | string | Plant ID (Primary Key) |
| `plants[].code` | string | Plant 코드 |
| `plants[].name` | string | Plant 이름 |
| `processesByPlant` | object | Plant ID를 키로 하는 Process 목록 맵 (두 번째 드롭다운) |
| `processesByPlant[plantId]` | array | 해당 Plant의 공정 목록 |
| `processesByPlant[plantId][].id` | string | 공정 ID (Primary Key) |
| `processesByPlant[plantId][].code` | string | 공정 코드 |
| `processesByPlant[plantId][].name` | string | 공정 이름 |
| `linesByProcess` | object | Process ID를 키로 하는 Line 목록 맵 (세 번째 드롭다운, 모든 Process에 동일한 Line 목록) |
| `linesByProcess[processId]` | array | Line 목록 (모든 Process에 동일) |
| `linesByProcess[processId][].id` | string | Line ID (Primary Key) |
| `linesByProcess[processId][].name` | string | Line 이름 |

### 프론트엔드 사용 흐름

1. **API 호출**: `GET /v1/plcs/mapping/dropdown?user_id=user001`
2. **Plant 드롭다운**: `response.plants` 사용
3. **Plant 선택 시**: `response.processesByPlant[selectedPlantId]` 사용하여 공정 목록 필터링
4. **Process 선택 시**: `response.linesByProcess[selectedProcessId]` 사용하여 Line 목록 조회 (모든 Process에 동일한 Line 목록)
5. **Line 선택 후**: `GET /v1/plcs?plant_id=xxx&process_id=xxx&line_id=xxx` 호출하여 PLC 목록 조회

### 사용 예시

#### 드롭다운 데이터 조회
```
GET /v1/plcs/mapping/dropdown?user_id=user001
```

### JavaScript 사용 예시

```javascript
// 1. 드롭다운 데이터 조회
const response = await fetch('/v1/plcs/mapping/dropdown?user_id=user001');
const data = await response.json();

// 2. Plant 드롭다운 초기화
const plants = data.plants; // [{id: "KY1", code: "KY1", name: "KY1"}, ...]

// 3. Plant 선택 시 공정 드롭다운 필터링
const selectedPlantId = "KY1";
const processes = data.processesByPlant[selectedPlantId] || [];
// [{id: "process_001", code: "MODULE", name: "모듈"}, ...]

// 4. Process 선택 시 Line 드롭다운 (모든 Process에 동일한 Line 목록)
const selectedProcessId = "process_001";
const lines = data.linesByProcess[selectedProcessId] || [];
// [{id: "line_001", name: "1라인"}, ...] (모든 Process에 동일한 Line 목록)

// 5. Line 선택 후 PLC 목록 조회
const selectedLineId = "line_001";
const plcList = await fetch(
  `/v1/plcs?plant_id=${selectedPlantId}&process_id=${selectedProcessId}&line_id=${selectedLineId}`
);
```

---

## 2. PLC 기준 정보 조회

PLC 기준 정보 목록을 검색, 필터링, 페이지네이션, 정렬 기능으로 조회합니다.

### 엔드포인트

```
GET /v1/plcs
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `plant_id` | string | 아니오 | - | Plant ID로 필터링 |
| `process_id` | string | 아니오 | - | 공정 ID로 필터링 |
| `line_id` | string | 아니오 | - | Line ID로 필터링 |
| `plc_id` | string | 아니오 | - | PLC ID로 검색 (부분 일치) |
| `plc_name` | string | 아니오 | - | PLC 명으로 검색 (부분 일치) |
| `program_name` | string | 아니오 | - | PGM명으로 필터링 (부분 일치) |
| `page` | integer | 아니오 | 1 | 페이지 번호 (최소: 1) |
| `page_size` | integer | 아니오 | 10 | 페이지당 항목 수 (최소: 1, 최대: 100) |
| `sort_by` | string | 아니오 | `plc_id` | 정렬 기준 (`plc_id`, `plc_name`, `create_dt`) |
| `sort_order` | string | 아니오 | `asc` | 정렬 순서 (`asc`, `desc`) |

### 정렬 기준 (`sort_by`)

- `plc_id`: PLC ID
- `plc_name`: PLC 명
- `create_dt`: 생성일시

### 정렬 순서 (`sort_order`)

- `asc`: 오름차순
- `desc`: 내림차순

### 응답 형식

```json
{
  "items": [
    {
      "id": "plc_uuid_001",
      "plc_id": "M1CFB01000",
      "plc_name": "01_01_CELL_FABRICATOR",
      "plant": "KY1",
      "process": "모듈",
      "line": "1라인",
      "unit": "1",
      "program_id": "PGM_01",
      "mapping_user": "정윤석",
      "mapping_dt": "2025-10-22T13:00:00"
    }
  ],
  "total_count": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `items` | array | PLC 목록 |
| `items[].id` | string | PLC UUID (Primary Key) |
| `items[].plc_id` | string | PLC 식별자 |
| `items[].plc_name` | string | PLC 이름 |
| `items[].plant` | string | Plant 이름 |
| `items[].process` | string | 공정 이름 |
| `items[].line` | string | Line 이름 |
| `items[].unit` | string | 호기 |
| `items[].program_id` | string | 매핑된 PGM ID |
| `items[].mapping_user` | string | 매핑 등록자 |
| `items[].mapping_dt` | datetime | 매핑 일시 |
| `total_count` | integer | 전체 개수 |
| `page` | integer | 현재 페이지 |
| `page_size` | integer | 페이지당 항목 수 |
| `total_pages` | integer | 전체 페이지 수 |

### 사용 예시

#### 전체 목록 조회
```
GET /v1/plcs?page=1&page_size=10
```

#### 계층별 필터링
```
GET /v1/plcs?plant_id=KY1&process_id=process001&line_id=line001
```

#### PLC ID 검색
```
GET /v1/plcs?plc_id=M1CFB01000
```

#### PLC 명 검색
```
GET /v1/plcs?plc_name=CELL_FABRICATOR
```

#### PGM명으로 필터링
```
GET /v1/plcs?program_name=라벨부착
```

#### 복합 검색 및 정렬
```
GET /v1/plcs?plant_id=KY1&process_id=process001&program_name=라벨부착&sort_by=plc_id&sort_order=desc&page=1&page_size=20
```

---

## 3. PGM 프로그램 조회

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
| `process_id` | string | 아니오 | - | 공정 ID로 필터링 (드롭다운 선택) |
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

### 정렬 기준 (`sort_by`)

- `create_dt`: 등록일시
- `program_id`: PGM ID
- `program_name`: 제목
- `status`: 상태

### 정렬 순서 (`sort_order`)

- `asc`: 오름차순
- `desc`: 내림차순

### 권한 기반 필터링

- `user_id`는 필수 파라미터입니다.
- 사용자의 권한 그룹에 따라 접근 가능한 공정의 PGM만 조회됩니다.
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

### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `items` | array | 프로그램 목록 |
| `items[].program_id` | string | 프로그램 ID (PGM ID) |
| `items[].program_name` | string | 프로그램 제목 |
| `items[].process_name` | string | 공정명 |
| `items[].ladder_file_count` | integer | Ladder 파일 개수 |
| `items[].comment_file_count` | integer | Comment 파일 개수 |
| `items[].status` | string | 등록 상태 |
| `items[].status_display` | string | 등록 상태 표시명 |
| `items[].processing_time` | string | 등록 소요시간 (예: "10 min", "-") |
| `items[].create_user` | string | 작성자 |
| `items[].create_dt` | datetime | 등록일시 |
| `total_count` | integer | 전체 개수 |
| `page` | integer | 현재 페이지 |
| `page_size` | integer | 페이지당 항목 수 |
| `total_pages` | integer | 전체 페이지 수 |

### 사용 예시

#### 전체 목록 조회
```
GET /v1/programs?user_id=user001&page=1&page_size=10
```

#### 공정별 필터링
```
GET /v1/programs?user_id=user001&process_id=process001
```

#### PGM ID 검색
```
GET /v1/programs?user_id=user001&program_id=PGM_000001
```

#### PGM Name 검색
```
GET /v1/programs?user_id=user001&program_name=라벨부착
```

#### 상태별 필터링
```
GET /v1/programs?user_id=user001&status=completed
```

#### 복합 검색 및 정렬
```
GET /v1/programs?user_id=user001&process_id=process001&program_name=라벨부착&status=completed&sort_by=create_dt&sort_order=desc&page=1&page_size=20
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

- `DATABASE_QUERY_ERROR`: 데이터베이스 쿼리 오류
- `VALIDATION_ERROR`: 입력값 검증 오류
- `PERMISSION_DENIED`: 권한 없음
- `NOT_FOUND`: 리소스를 찾을 수 없음

---

## 참고사항

1. **드롭다운 데이터**: 매핑 화면 진입 시 먼저 드롭다운 API를 호출하여 Plant, 공정, Line 데이터를 조회합니다. 이후 클라이언트 사이드에서 연쇄 필터링을 수행합니다.
2. **권한 기반 필터링**: 드롭다운 API와 PGM 조회 API는 `user_id`가 필수이며, 사용자 권한에 따라 공정 목록이 필터링됩니다.
3. **페이지네이션**: 기본값은 `page=1`, `page_size=10`입니다.
4. **검색**: `plc_id`, `plc_name`, `program_name`은 부분 일치 검색을 지원합니다.
5. **필터링**: 여러 필터를 동시에 사용할 수 있으며, AND 조건으로 적용됩니다.
6. **정렬**: 정렬 기준과 정렬 순서를 조합하여 사용할 수 있습니다.
7. **사용 흐름**: 드롭다운 데이터 조회 → Plant/공정/Line 선택 → PLC 목록 조회 → PGM 선택 → 매핑 저장

