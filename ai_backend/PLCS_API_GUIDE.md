# PLCs API 가이드

PLCs 라우터의 모든 API 엔드포인트 가이드입니다.

## 목차

1. [PLC 단일 조회](#1-plc-단일-조회)
2. [PLC 목록 조회](#2-plc-목록-조회)
3. [PLC-PGM 매핑 저장](#3-plc-pgm-매핑-저장)
4. [PLC Tree 구조 조회](#4-plc-tree-구조-조회)
5. [드롭다운용 마스터 데이터 조회](#5-드롭다운용-마스터-데이터-조회)
6. [매핑 화면용 드롭다운 데이터 조회](#6-매핑-화면용-드롭다운-데이터-조회)
7. [PLC 단일 삭제](#7-plc-단일-삭제)
8. [PLC 일괄 삭제](#8-plc-일괄-삭제)
9. [PLC 일괄 저장](#9-plc-일괄-저장)

---

## 1. PLC 단일 조회

PLC 정보를 조회합니다 (PLC_UUID로).

### 엔드포인트

```
GET /v1/plcs/{plc_uuid}
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `plc_uuid` | string | **예** | PLC의 UUID (Primary Key) |

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

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | PLC UUID (Primary Key) |
| `plc_id` | string | PLC 식별자 |
| `plc_name` | string | PLC 이름 |
| `plant` | string | Plant 이름 |
| `process` | string | 공정 이름 |
| `line` | string | Line 이름 |
| `unit` | string | 호기 |
| `program_id` | string | 매핑된 PGM ID |
| `program_id_changed` | boolean | Program ID 변경 여부 |
| `previous_program_id` | string | 이전 Program ID |

### 주의사항

- `is_active=true`인 경우에만 조회됩니다
- `is_active=false`인 경우 404 Not Found 반환

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

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `plc_uuids` | array[string] | **예** | 매핑할 PLC UUID 리스트 |
| `program_id` | string | **예** | 매핑할 PGM 프로그램 ID |
| `mapping_user` | string | **예** | 매핑을 수행한 사용자 ID |

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

## 4. PLC Tree 구조 조회

채팅 메뉴에서 PLC를 선택하기 위한 Tree 구조를 조회합니다.

### 엔드포인트

```
GET /v1/plcs/tree
```

### Hierarchy 구조

```
Plant → 공정(Process) → Line → PLC명 → 호기(Unit) → PLC ID
```

### 응답 형식

```json
{
  "data": [
    {
      "plant": "BOSK KY1",
      "procList": [
        {
          "proc": "모듈",
          "lineList": [
            {
              "line": "1라인",
              "plcNameList": [
                {
                  "plcName": "01_01_CELL_FABRICATOR",
                  "unitList": [
                    {
                      "unit": "1",
                      "info": [
                        {
                          "plc_id": "M1CFB01000",
                          "plc_uuid": "plc-uuid-001",
                          "create_dt": "2025/10/31 18:39",
                          "user": "admin"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

### 특징

- 활성화된 PLC만 조회 (`is_active=true`)
- 활성화된 Plant, Process, Line만 조회
- 정렬 순서: Plant → Process → Line → PLC명 → 호기

### 사용 예시

```
GET /v1/plcs/tree
```

---

## 5. 드롭다운용 마스터 데이터 조회

PLC 추가 화면에서 사용할 드롭다운 데이터를 전체 조회합니다.

### 엔드포인트

```
GET /v1/plcs/masters/dropdown
```

### 응답 형식

```json
{
  "plants": [
    {"id": "KY1", "code": "KY1", "name": "BOSK KY1"}
  ],
  "processesByPlant": {
    "KY1": [
      {"id": "process_001", "code": "MODULE", "name": "모듈"},
      {"id": "process_002", "code": "ELECTRODE", "name": "전극"}
    ]
  },
  "linesByProcess": {
    "process_001": [
      {"id": "line_001", "code": "LN1", "name": "1라인"},
      {"id": "line_002", "code": "LN2", "name": "2라인"}
    ]
  }
}
```

### 프론트엔드 사용 예시

```javascript
// 1. Plant 드롭다운
const plants = response.plants;

// 2. Plant 선택 시 Process 드롭다운 필터링
const selectedPlantId = "KY1";
const processes = response.processesByPlant[selectedPlantId] || [];

// 3. Process 선택 시 Line 드롭다운 필터링
const selectedProcessId = "process_001";
const lines = response.linesByProcess[selectedProcessId] || [];
```

### 사용 예시

```
GET /v1/plcs/masters/dropdown
```

---

## 6. 매핑 화면용 드롭다운 데이터 조회

PLC-PGM 매핑 화면에서 사용할 드롭다운 데이터를 조회합니다 (권한 기반 공정 필터링 포함).

### 엔드포인트

```
GET /v1/plcs/mapping/dropdown
```

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `user_id` | string | **예** | 사용자 ID (권한 기반 필터링용) |

### 권한 기반 필터링

- 공정은 사용자 권한에 따라 필터링됩니다
  - **super 권한 그룹**: 모든 활성 공정 반환
  - **plc 권한 그룹**: 지정된 공정만 반환
  - **권한이 없으면**: 공정 목록이 비어있음

### 응답 형식

```json
{
  "plants": [
    {"id": "KY1", "code": "KY1", "name": "BOSK KY1"}
  ],
  "processesByPlant": {
    "KY1": [
      {"id": "process_001", "code": "MODULE", "name": "모듈"}
    ]
  },
  "linesByProcess": {
    "process_001": [
      {"id": "line_001", "code": "LN1", "name": "1라인"}
    ]
  }
}
```

### 사용 예시

```
GET /v1/plcs/mapping/dropdown?user_id=user001
```

---

## 7. PLC 단일 삭제

PLC를 삭제합니다 (소프트 삭제).

### 엔드포인트

```
DELETE /v1/plcs/{plc_uuid}
```

### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `plc_uuid` | string | **예** | PLC UUID |

### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `delete_user` | string | **예** | 삭제 사용자 |

### 삭제 방식

- 소프트 삭제: `is_active = False`로 설정
- 매핑된 `program_id` 제거 (None으로 설정)
- 실제 데이터는 삭제되지 않음

### 응답 형식

```json
{
  "success": true,
  "deleted_count": 1,
  "message": "PLC가 성공적으로 삭제되었습니다."
}
```

### 주의사항

- PLC 삭제 시 매핑된 PGM ID도 함께 해제됩니다

### 사용 예시

```
DELETE /v1/plcs/plc-uuid-001?delete_user=admin
```

---

## 8. PLC 일괄 삭제

여러 PLC를 일괄 삭제합니다 (소프트 삭제).

### 엔드포인트

```
DELETE /v1/plcs
```

### 요청 Body

```json
{
  "plc_uuids": ["plc-uuid-001", "plc-uuid-002", "plc-uuid-003"],
  "delete_user": "admin"
}
```

### 요청 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `plc_uuids` | array[string] | **예** | 삭제할 PLC UUID 리스트 |
| `delete_user` | string | **예** | 삭제 사용자 |

### 응답 형식

```json
{
  "success": true,
  "deleted_count": 3,
  "message": "3개의 PLC가 성공적으로 삭제되었습니다."
}
```

### 사용 예시

```bash
curl -X DELETE "http://localhost:8000/v1/plcs" \
  -H "Content-Type: application/json" \
  -d '{
    "plc_uuids": ["plc-uuid-001", "plc-uuid-002"],
    "delete_user": "admin"
  }'
```

---

## 9. PLC 일괄 저장

여러 PLC를 일괄 저장합니다 (생성 및 수정).

### 엔드포인트

```
POST /v1/plcs/batch
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
      "plc_name": "01_01_CELL_FABRICATOR",
      "unit": "1",
      "plc_id": "M1CFB01000",
      "update_user": "admin"
    },
    {
      "plant_id": "KY1",
      "process_id": "process_001",
      "line_id": "line_001",
      "plc_name": "01_02_CELL_FABRICATOR",
      "unit": "2",
      "plc_id": "M1CFB02000",
      "update_user": "admin"
    }
  ]
}
```

### 요청 필드

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `items` | array | **예** | 저장할 PLC 목록 |
| `items[].plc_uuid` | string | 아니오 | PLC UUID (있으면 수정, 없으면 생성) |
| `items[].plant_id` | string | **예** | Plant ID |
| `items[].process_id` | string | **예** | 공정 ID |
| `items[].line_id` | string | **예** | Line ID |
| `items[].plc_name` | string | **예** | PLC명 |
| `items[].unit` | string | 아니오 | 호기 |
| `items[].plc_id` | string | **예** | PLC ID |
| `items[].update_user` | string | **예** | 저장 사용자 |

### 저장 방식

- `plc_uuid`가 없으면: 새로 생성
- `plc_uuid`가 있으면: 기존 PLC 수정

### 응답 형식

#### 성공 시
```json
{
  "success": true,
  "message": "기준 정보가 저장되었습니다.",
  "created_count": 1,
  "updated_count": 1,
  "failed_count": 0,
  "errors": []
}
```

#### 실패 시
```json
{
  "success": false,
  "message": "저장 중 오류가 발생했습니다.",
  "created_count": 0,
  "updated_count": 0,
  "failed_count": 2,
  "errors": [
    "PLC ID M1CFB01000: 존재하지 않는 Plant ID입니다",
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
        "update_user": "admin"
      }
    ]
  }'
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

1. **소프트 삭제**: PLC 삭제는 실제 데이터를 삭제하지 않고 `is_active=False`로 설정합니다.
2. **매핑 해제**: PLC 삭제 시 매핑된 `program_id`도 함께 제거됩니다.
3. **권한 기반 필터링**: 매핑 화면용 드롭다운 API는 `user_id`가 필수이며, 사용자 권한에 따라 공정 목록이 필터링됩니다.
4. **일괄 저장**: `plc_uuid`가 있으면 수정, 없으면 생성됩니다.
5. **페이지네이션**: 기본값은 `page=1`, `page_size=10`입니다.
6. **검색**: `plc_id`, `plc_name`, `program_name`은 부분 일치 검색을 지원합니다.

