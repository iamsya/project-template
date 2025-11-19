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

<table>
<thead>
<tr>
<th>파라미터</th>
<th>타입</th>
<th>필수</th>
<th>기본값</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>user_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>-</td>
<td>사용자 ID (권한 기반 필터링용)</td>
</tr>
</tbody>
</table>

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

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>plants</code></td>
<td>array</td>
<td>Plant 목록 (첫 번째 드롭다운)</td>
</tr>
<tr>
<td><code>plants[].id</code></td>
<td>string</td>
<td>Plant ID (Primary Key)</td>
</tr>
<tr>
<td><code>plants[].code</code></td>
<td>string</td>
<td>Plant 코드</td>
</tr>
<tr>
<td><code>plants[].name</code></td>
<td>string</td>
<td>Plant 이름</td>
</tr>
<tr>
<td><code>processesByPlant</code></td>
<td>object</td>
<td>Plant ID를 키로 하는 Process 목록 맵 (두 번째 드롭다운)</td>
</tr>
<tr>
<td><code>processesByPlant[plantId]</code></td>
<td>array</td>
<td>해당 Plant의 공정 목록</td>
</tr>
<tr>
<td><code>processesByPlant[plantId][].id</code></td>
<td>string</td>
<td>공정 ID (Primary Key)</td>
</tr>
<tr>
<td><code>processesByPlant[plantId][].code</code></td>
<td>string</td>
<td>공정 코드</td>
</tr>
<tr>
<td><code>processesByPlant[plantId][].name</code></td>
<td>string</td>
<td>공정 이름</td>
</tr>
<tr>
<td><code>linesByProcess</code></td>
<td>object</td>
<td>Process ID를 키로 하는 Line 목록 맵 (세 번째 드롭다운, 모든 Process에 동일한 Line 목록)</td>
</tr>
<tr>
<td><code>linesByProcess[processId]</code></td>
<td>array</td>
<td>Line 목록 (모든 Process에 동일)</td>
</tr>
<tr>
<td><code>linesByProcess[processId][].id</code></td>
<td>string</td>
<td>Line ID (Primary Key)</td>
</tr>
<tr>
<td><code>linesByProcess[processId][].name</code></td>
<td>string</td>
<td>Line 이름</td>
</tr>
</tbody>
</table>

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

<table>
<thead>
<tr>
<th>파라미터</th>
<th>타입</th>
<th>필수</th>
<th>기본값</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>plant_id</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>Plant ID로 필터링</td>
</tr>
<tr>
<td><code>process_id</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>공정 ID로 필터링</td>
</tr>
<tr>
<td><code>line_id</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>Line ID로 필터링</td>
</tr>
<tr>
<td><code>plc_id</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>PLC ID로 검색 (부분 일치)</td>
</tr>
<tr>
<td><code>plc_name</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>PLC 명으로 검색 (부분 일치)</td>
</tr>
<tr>
<td><code>program_name</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>PGM명으로 필터링 (부분 일치)</td>
</tr>
<tr>
<td><code>page</code></td>
<td>integer</td>
<td>아니오</td>
<td>1</td>
<td>페이지 번호 (최소: 1)</td>
</tr>
<tr>
<td><code>page_size</code></td>
<td>integer</td>
<td>아니오</td>
<td>10</td>
<td>페이지당 항목 수 (최소: 1, 최대: 100)</td>
</tr>
<tr>
<td><code>sort_by</code></td>
<td>string</td>
<td>아니오</td>
<td><code>plc_id</code></td>
<td>정렬 기준 (<code>plc_id</code>, <code>plc_name</code>, <code>create_dt</code>)</td>
</tr>
<tr>
<td><code>sort_order</code></td>
<td>string</td>
<td>아니오</td>
<td><code>asc</code></td>
<td>정렬 순서 (<code>asc</code>, <code>desc</code>)</td>
</tr>
</tbody>
</table>

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

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>items</code></td>
<td>array</td>
<td>PLC 목록</td>
</tr>
<tr>
<td><code>items[].id</code></td>
<td>string</td>
<td>PLC UUID (Primary Key)</td>
</tr>
<tr>
<td><code>items[].plc_id</code></td>
<td>string</td>
<td>PLC 식별자</td>
</tr>
<tr>
<td><code>items[].plc_name</code></td>
<td>string</td>
<td>PLC 이름</td>
</tr>
<tr>
<td><code>items[].plant</code></td>
<td>string</td>
<td>Plant 이름</td>
</tr>
<tr>
<td><code>items[].process</code></td>
<td>string</td>
<td>공정 이름</td>
</tr>
<tr>
<td><code>items[].line</code></td>
<td>string</td>
<td>Line 이름</td>
</tr>
<tr>
<td><code>items[].unit</code></td>
<td>string</td>
<td>호기</td>
</tr>
<tr>
<td><code>items[].program_id</code></td>
<td>string</td>
<td>매핑된 PGM ID</td>
</tr>
<tr>
<td><code>items[].mapping_user</code></td>
<td>string</td>
<td>매핑 등록자</td>
</tr>
<tr>
<td><code>items[].mapping_dt</code></td>
<td>datetime</td>
<td>매핑 일시</td>
</tr>
<tr>
<td><code>total_count</code></td>
<td>integer</td>
<td>전체 개수</td>
</tr>
<tr>
<td><code>page</code></td>
<td>integer</td>
<td>현재 페이지</td>
</tr>
<tr>
<td><code>page_size</code></td>
<td>integer</td>
<td>페이지당 항목 수</td>
</tr>
<tr>
<td><code>total_pages</code></td>
<td>integer</td>
<td>전체 페이지 수</td>
</tr>
</tbody>
</table>

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

<table>
<thead>
<tr>
<th>파라미터</th>
<th>타입</th>
<th>필수</th>
<th>기본값</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>user_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>-</td>
<td>사용자 ID (권한 기반 필터링용)</td>
</tr>
<tr>
<td><code>program_id</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>PGM ID로 검색 (정확한 일치)</td>
</tr>
<tr>
<td><code>program_name</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>제목으로 검색 (부분 일치)</td>
</tr>
<tr>
<td><code>process_id</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>공정 ID로 필터링 (드롭다운 선택)</td>
</tr>
<tr>
<td><code>status</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>등록 상태로 필터링</td>
</tr>
<tr>
<td><code>create_user</code></td>
<td>string</td>
<td>아니오</td>
<td>-</td>
<td>작성자로 필터링</td>
</tr>
<tr>
<td><code>page</code></td>
<td>integer</td>
<td>아니오</td>
<td>1</td>
<td>페이지 번호 (최소: 1)</td>
</tr>
<tr>
<td><code>page_size</code></td>
<td>integer</td>
<td>아니오</td>
<td>10</td>
<td>페이지당 항목 수 (최소: 1, 최대: 100)</td>
</tr>
<tr>
<td><code>sort_by</code></td>
<td>string</td>
<td>아니오</td>
<td><code>create_dt</code></td>
<td>정렬 기준 (<code>create_dt</code>, <code>program_id</code>, <code>program_name</code>, <code>status</code>)</td>
</tr>
<tr>
<td><code>sort_order</code></td>
<td>string</td>
<td>아니오</td>
<td><code>desc</code></td>
<td>정렬 순서 (<code>asc</code>, <code>desc</code>)</td>
</tr>
</tbody>
</table>

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

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>items</code></td>
<td>array</td>
<td>프로그램 목록</td>
</tr>
<tr>
<td><code>items[].program_id</code></td>
<td>string</td>
<td>프로그램 ID (PGM ID)</td>
</tr>
<tr>
<td><code>items[].program_name</code></td>
<td>string</td>
<td>프로그램 제목</td>
</tr>
<tr>
<td><code>items[].process_name</code></td>
<td>string</td>
<td>공정명</td>
</tr>
<tr>
<td><code>items[].ladder_file_count</code></td>
<td>integer</td>
<td>Ladder 파일 개수</td>
</tr>
<tr>
<td><code>items[].comment_file_count</code></td>
<td>integer</td>
<td>Comment 파일 개수</td>
</tr>
<tr>
<td><code>items[].status</code></td>
<td>string</td>
<td>등록 상태</td>
</tr>
<tr>
<td><code>items[].status_display</code></td>
<td>string</td>
<td>등록 상태 표시명</td>
</tr>
<tr>
<td><code>items[].processing_time</code></td>
<td>string</td>
<td>등록 소요시간 (예: "10 min", "-")</td>
</tr>
<tr>
<td><code>items[].create_user</code></td>
<td>string</td>
<td>작성자</td>
</tr>
<tr>
<td><code>items[].create_dt</code></td>
<td>datetime</td>
<td>등록일시</td>
</tr>
<tr>
<td><code>total_count</code></td>
<td>integer</td>
<td>전체 개수</td>
</tr>
<tr>
<td><code>page</code></td>
<td>integer</td>
<td>현재 페이지</td>
</tr>
<tr>
<td><code>page_size</code></td>
<td>integer</td>
<td>페이지당 항목 수</td>
</tr>
<tr>
<td><code>total_pages</code></td>
<td>integer</td>
<td>전체 페이지 수</td>
</tr>
</tbody>
</table>

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

