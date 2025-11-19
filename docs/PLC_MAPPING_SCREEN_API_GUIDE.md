# PLC-PGM 매핑 화면 API 가이드

PLC-PGM 매핑 화면에서 사용하는 API 가이드입니다.

## 목차

1. [드롭다운 데이터 조회](#1-드롭다운-데이터-조회)
2. [PLC 목록 조회](#2-plc-목록-조회)
3. [PLC-PGM 매핑 저장](#3-plc-pgm-매핑-저장)

---

## 1. 드롭다운 데이터 조회

PLC-PGM 매핑 화면에서 사용할 드롭다운 데이터를 조회합니다 (권한 기반 공정 필터링 포함).

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
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>user_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>사용자 ID (권한 기반 필터링용)</td>
</tr>
</tbody>
</table>

### 권한 기반 필터링

- 사용자가 접근 가능한 Plant, Process, Line만 반환
- Process는 사용자 권한에 따라 필터링됩니다
  - **super 권한 그룹**: 모든 활성 Process 반환
  - **plc 권한 그룹**: 지정된 Process만 반환
  - **권한이 없으면**: Process 목록이 비어있음
- 계층 구조 포함 (`processesByPlant`, `linesByProcess`)

### 응답 형식

```json
{
  "plants": [
    {"id": "KY1", "name": "BOSK KY1"}
  ],
  "processesByPlant": {
    "KY1": [
      {"id": "process_001", "name": "모듈"},
      {"id": "process_002", "name": "전극"}
    ]
  },
  "linesByProcess": {
    "process_001": [
      {"id": "line_001", "name": "1라인"},
      {"id": "line_002", "name": "2라인"}
    ],
    "process_002": [
      {"id": "line_001", "name": "1라인"}
    ]
  }
}
```

### 프론트엔드 사용 흐름

1. API 호출: `GET /v1/plcs/mapping/dropdown?user_id=user001`
2. Plant 드롭다운: `response.plants` 사용
3. Plant 선택 시: `response.processesByPlant[selectedPlantId]` 사용
4. Process 선택 시: `response.linesByProcess[selectedProcessId]` 사용
5. Line 선택 후: `GET /v1/plcs?plant_id=xxx&process_id=xxx&line_id=xxx` 호출하여 PLC 목록 조회

### 사용 예시

```
GET /v1/plcs/mapping/dropdown?user_id=user001
```

---

## 2. PLC 목록 조회

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
<td>페이지당 항목 수 (최소: 1, 최대: 10000)</td>
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

### 사용 예시

```
GET /v1/plcs?page=1&page_size=10
GET /v1/plcs?plant_id=KY1&process_id=process001&line_id=line001
GET /v1/plcs?plc_id=M1CFB01000
GET /v1/plcs?program_name=라벨부착
```

---

## 3. PLC-PGM 매핑 저장

여러 PLC에 하나의 PGM 프로그램을 매핑합니다.

### 엔드포인트

```
PUT /v1/plcs/mapping
```

### 요청 Body

```json
{
  "plc_uuids": ["plc-uuid-001", "plc-uuid-002", "plc-uuid-003"],
  "program_id": "PGM_01",
  "mapping_user": "user001"
}
```

### 요청 필드

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>필수</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>plc_uuids</code></td>
<td>array[string]</td>
<td><strong>예</strong></td>
<td>매핑할 PLC UUID 리스트</td>
</tr>
<tr>
<td><code>program_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>매핑할 PGM 프로그램 ID</td>
</tr>
<tr>
<td><code>mapping_user</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>매핑을 수행한 사용자 ID</td>
</tr>
</tbody>
</table>

### 응답 형식

```json
{
  "success": true,
  "mapped_count": 3,
  "failed_count": 0,
  "errors": []
}
```

### 처리 로직

1. 각 PLC의 현재 `program_id`를 `previous_program_id`에 저장
2. 새로운 `program_id`로 업데이트
3. `mapping_user`, `mapping_dt` 업데이트

**참고:** `previous_program_id`는 Program ID 변경 이력을 추적하기 위해 사용됩니다.

### 사용 예시

```bash
curl -X PUT "http://localhost:8000/v1/plcs/mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "plc_uuids": ["plc-uuid-001", "plc-uuid-002"],
    "program_id": "PGM_01",
    "mapping_user": "user001"
  }'
```

---

## 참고사항

1. **권한 기반 필터링**: 드롭다운 API는 `user_id`가 필수이며, 사용자 권한에 따라 공정 목록이 필터링됩니다.
2. **페이지네이션**: 기본값은 `page=1`, `page_size=10`입니다. 모든 데이터를 가져오려면 `page_size=10000`을 사용하세요.
3. **검색**: `plc_id`, `plc_name`, `program_name`은 부분 일치 검색을 지원합니다.
4. **조회 필터링**: 모든 PLC 조회 API는 `is_deleted=false`인 것만 반환합니다.

