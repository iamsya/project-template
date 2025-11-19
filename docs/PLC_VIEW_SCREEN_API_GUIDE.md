# PLC 조회 화면 API 가이드

PLC 조회 화면에서 사용하는 API 가이드입니다.

## 목차

1. [PLC 단일 조회](#1-plc-단일-조회)
2. [PLC 목록 조회](#2-plc-목록-조회)

---

## 1. PLC 단일 조회

PLC 정보를 조회합니다 (PLC_UUID로).

### 엔드포인트

```
GET /v1/plcs/{plc_uuid}
```

### 경로 파라미터

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
<td><code>plc_uuid</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>PLC의 UUID (Primary Key)</td>
</tr>
</tbody>
</table>

### 응답 형식

```json
{
  "id": "plc-uuid-001",
  "plc_id": "M1CFB01000",
  "plc_name": "01_01_CELL_FABRICATOR",
  "plant": "KY1",
  "process": "모듈",
  "line": "1라인",
  "unit": "1",
  "program_id": "PGM_01",
  "program_id_changed": false,
  "previous_program_id": null
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
<td><code>id</code></td>
<td>string</td>
<td>PLC UUID (Primary Key)</td>
</tr>
<tr>
<td><code>plc_id</code></td>
<td>string</td>
<td>PLC 식별자</td>
</tr>
<tr>
<td><code>plc_name</code></td>
<td>string</td>
<td>PLC 이름</td>
</tr>
<tr>
<td><code>plant</code></td>
<td>string</td>
<td>Plant 이름</td>
</tr>
<tr>
<td><code>process</code></td>
<td>string</td>
<td>공정 이름</td>
</tr>
<tr>
<td><code>line</code></td>
<td>string</td>
<td>Line 이름</td>
</tr>
<tr>
<td><code>unit</code></td>
<td>string</td>
<td>호기</td>
</tr>
<tr>
<td><code>program_id</code></td>
<td>string</td>
<td>매핑된 PGM ID</td>
</tr>
<tr>
<td><code>program_id_changed</code></td>
<td>boolean</td>
<td>Program ID 변경 여부</td>
</tr>
<tr>
<td><code>previous_program_id</code></td>
<td>string</td>
<td>이전 Program ID</td>
</tr>
</tbody>
</table>

### 주의사항

- `is_deleted=false`인 경우에만 조회됩니다 (사용 중으로 인식)
- `is_deleted=true`이거나 PLC를 찾을 수 없는 경우 `null`을 반환합니다 (200 OK)

### 사용 예시

```
GET /v1/plcs/plc-uuid-001
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
GET /v1/plcs?plc_name=CELL_FABRICATOR
GET /v1/plcs?program_name=라벨부착
GET /v1/plcs?plant_id=KY1&process_id=process001&program_name=라벨부착&sort_by=plc_id&sort_order=desc&page=1&page_size=20
```

---

## 참고사항

1. **조회 필터링**: 모든 PLC 조회 API는 `is_deleted=false`인 것만 반환합니다.
2. **페이지네이션**: 기본값은 `page=1`, `page_size=10`입니다. 모든 데이터를 가져오려면 `page_size=10000`을 사용하세요.
3. **검색**: `plc_id`, `plc_name`, `program_name`은 부분 일치 검색을 지원합니다.
4. **응답 형식**: 단일 조회 API는 PLC를 찾을 수 없거나 삭제된 경우 `null`을 반환합니다 (200 OK).

