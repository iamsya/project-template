# PLC 등록 화면 API 가이드

PLC 등록/관리 화면에서 사용하는 API 가이드입니다.

## 목차

1. [드롭다운 데이터 조회](#1-드롭다운-데이터-조회)
2. [PLC 다건 저장](#2-plc-다건-저장)
3. [PLC 다건 수정](#3-plc-다건-수정)
4. [PLC 삭제](#4-plc-삭제)

---

## 1. 드롭다운 데이터 조회

PLC 추가 화면에서 사용할 드롭다운 데이터를 전체 조회합니다.

### 엔드포인트

```
GET /v1/plcs/masters/dropdown
```

### 응답 형식

```json
{
  "plants": [
    {"id": "KY1", "name": "BOSK KY1"}
  ],
  "processes": [
    {"id": "process_001", "name": "모듈"},
    {"id": "process_002", "name": "전극"}
  ],
  "lines": [
    {"id": "line_001", "name": "1라인"},
    {"id": "line_002", "name": "2라인"}
  ]
}
```

### 특징

- 마스터 테이블에서 활성화된 데이터만 조회 (`is_active=true`)
- 계층 구조 없이 단순 리스트로 반환
- 정렬 순서: 이름 순서

### 프론트엔드 사용 예시

```javascript
// 단순 리스트로 반환 (계층 구조 없음)
const plants = response.plants;
const processes = response.processes;
const lines = response.lines;
```

### 사용 예시

```
GET /v1/plcs/masters/dropdown
```

---

## 2. PLC 다건 저장

여러 PLC를 일괄 생성합니다.

### 엔드포인트

```
POST /v1/plcs/batch
```

### 요청 Body

```json
{
  "items": [
    {
      "plant_id": "KY1",
      "process_id": "process_001",
      "line_id": "line_001",
      "plc_name": "01_01_CELL_FABRICATOR",
      "unit": "1",
      "plc_id": "M1CFB01000",
      "create_user": "admin"
    },
    {
      "plant_id": "KY1",
      "process_id": "process_001",
      "line_id": "line_001",
      "plc_name": "01_02_CELL_FABRICATOR",
      "unit": "2",
      "plc_id": "M1CFB02000",
      "create_user": "admin"
    }
  ]
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
<td><code>items</code></td>
<td>array</td>
<td><strong>예</strong></td>
<td>생성할 PLC 목록</td>
</tr>
<tr>
<td><code>items[].plant_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>Plant ID</td>
</tr>
<tr>
<td><code>items[].process_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>공정 ID</td>
</tr>
<tr>
<td><code>items[].line_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>Line ID</td>
</tr>
<tr>
<td><code>items[].plc_name</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>PLC명</td>
</tr>
<tr>
<td><code>items[].unit</code></td>
<td>string</td>
<td>아니오</td>
<td>호기</td>
</tr>
<tr>
<td><code>items[].plc_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>PLC ID</td>
</tr>
<tr>
<td><code>items[].create_user</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>생성 사용자</td>
</tr>
</tbody>
</table>

### 응답 형식

#### 성공 시
```json
{
  "success": true,
  "message": "2개의 PLC가 생성되었습니다.",
  "created_count": 2,
  "failed_count": 0,
  "errors": []
}
```

#### 실패 시
```json
{
  "success": false,
  "message": "일부 항목 생성 중 오류가 발생했습니다.",
  "created_count": 1,
  "failed_count": 1,
  "errors": [
    "PLC ID M1CFB02000: 중복된 PLC ID입니다"
  ]
}
```

### 사용 예시

```bash
curl -X POST "http://localhost:8000/v1/plcs/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plant_id": "KY1",
        "process_id": "process_001",
        "line_id": "line_001",
        "plc_name": "01_01_CELL_FABRICATOR",
        "unit": "1",
        "plc_id": "M1CFB01000",
        "create_user": "admin"
      }
    ]
  }'
```

---

## 3. PLC 다건 수정

여러 PLC를 일괄 수정합니다.

### 엔드포인트

```
PUT /v1/plcs/batch
```

### 요청 Body

```json
{
  "items": [
    {
      "plc_uuid": "plc-uuid-001",
      "plant_id": "KY1",
      "process_id": "process_001",
      "line_id": "line_001",
      "plc_name": "01_01_CELL_FABRICATOR_UPDATED",
      "unit": "1",
      "plc_id": "M1CFB01000",
      "update_user": "admin"
    },
    {
      "plc_uuid": "plc-uuid-002",
      "plant_id": "KY1",
      "process_id": "process_002",
      "line_id": "line_002",
      "plc_name": "01_02_CELL_FABRICATOR_UPDATED",
      "unit": "2",
      "plc_id": "M1CFB02000",
      "update_user": "admin"
    }
  ]
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
<td><code>items</code></td>
<td>array</td>
<td><strong>예</strong></td>
<td>수정할 PLC 목록</td>
</tr>
<tr>
<td><code>items[].plc_uuid</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>PLC UUID (필수)</td>
</tr>
<tr>
<td><code>items[].plant_id</code></td>
<td>string</td>
<td>아니오</td>
<td>Plant ID (변경 시)</td>
</tr>
<tr>
<td><code>items[].process_id</code></td>
<td>string</td>
<td>아니오</td>
<td>공정 ID (변경 시)</td>
</tr>
<tr>
<td><code>items[].line_id</code></td>
<td>string</td>
<td>아니오</td>
<td>Line ID (변경 시)</td>
</tr>
<tr>
<td><code>items[].plc_name</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>PLC명</td>
</tr>
<tr>
<td><code>items[].unit</code></td>
<td>string</td>
<td>아니오</td>
<td>호기</td>
</tr>
<tr>
<td><code>items[].plc_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>PLC ID</td>
</tr>
<tr>
<td><code>items[].update_user</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>수정 사용자</td>
</tr>
</tbody>
</table>

### 응답 형식

#### 성공 시
```json
{
  "success": true,
  "message": "2개의 PLC가 수정되었습니다.",
  "updated_count": 2,
  "failed_count": 0,
  "errors": []
}
```

#### 실패 시
```json
{
  "success": false,
  "message": "일부 항목 수정 중 오류가 발생했습니다.",
  "updated_count": 1,
  "failed_count": 1,
  "errors": [
    "PLC UUID plc-uuid-002: PLC를 찾을 수 없습니다"
  ]
}
```

### 사용 예시

```bash
curl -X PUT "http://localhost:8000/v1/plcs/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plc_uuid": "plc-uuid-001",
        "plant_id": "KY1",
        "process_id": "process_001",
        "line_id": "line_001",
        "plc_name": "01_01_CELL_FABRICATOR_UPDATED",
        "unit": "1",
        "plc_id": "M1CFB01000",
        "update_user": "admin"
      }
    ]
  }'
```

---

## 4. PLC 삭제

PLC를 삭제합니다 (소프트 삭제). 단일 또는 여러 PLC를 일괄 삭제할 수 있습니다.

### 엔드포인트

```
DELETE /v1/plcs
```

### 요청 Body

#### 단일 삭제 예시
```json
{
  "plc_uuids": ["plc-uuid-001"],
  "delete_user": "admin"
}
```

#### 일괄 삭제 예시
```json
{
  "plc_uuids": ["plc-uuid-001", "plc-uuid-002", "plc-uuid-003"],
  "delete_user": "admin"
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
<td>삭제할 PLC UUID 리스트 (1개 이상)</td>
</tr>
<tr>
<td><code>delete_user</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>삭제 사용자</td>
</tr>
</tbody>
</table>

### 삭제 방식

- 소프트 삭제: `is_deleted = True`로 설정
- `deleted_at`에 삭제 일시 저장
- `deleted_by`에 삭제자 저장
- 매핑된 `program_id` 제거 (None으로 설정)
- 실제 데이터는 삭제되지 않음

### 응답 형식

#### 단일 삭제 응답
```json
{
  "success": true,
  "deleted_count": 1,
  "message": "1개의 PLC가 성공적으로 삭제되었습니다."
}
```

#### 일괄 삭제 응답
```json
{
  "success": true,
  "deleted_count": 3,
  "message": "3개의 PLC가 성공적으로 삭제되었습니다."
}
```

### 주의사항

- PLC 삭제 시 매핑된 PGM ID도 함께 해제됩니다
- `plc_uuids` 배열에 1개만 넣으면 단일 삭제, 여러 개를 넣으면 일괄 삭제

### 사용 예시

#### 단일 삭제
```bash
curl -X DELETE "http://localhost:8000/v1/plcs" \
  -H "Content-Type: application/json" \
  -d '{
    "plc_uuids": ["plc-uuid-001"],
    "delete_user": "admin"
  }'
```

#### 일괄 삭제
```bash
curl -X DELETE "http://localhost:8000/v1/plcs" \
  -H "Content-Type: application/json" \
  -d '{
    "plc_uuids": ["plc-uuid-001", "plc-uuid-002"],
    "delete_user": "admin"
  }'
```

---

## 참고사항

1. **소프트 삭제**: PLC 삭제는 실제 데이터를 삭제하지 않고 `is_deleted=True`로 설정합니다. `is_deleted=false`인 것은 사용 중으로 인식됩니다.
2. **매핑 해제**: PLC 삭제 시 매핑된 `program_id`도 함께 제거됩니다.
3. **다건 저장/수정**: 저장과 수정은 별도의 API로 분리되어 있습니다. `POST /v1/plcs/batch`는 생성만, `PUT /v1/plcs/batch`는 수정만 처리합니다.
4. **단일/일괄 삭제**: 삭제 API는 `plc_uuids` 배열에 1개만 넣으면 단일 삭제, 여러 개를 넣으면 일괄 삭제로 동작합니다.

