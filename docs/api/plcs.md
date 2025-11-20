# PLCs API 가이드

PLCs 라우터의 모든 API 엔드포인트 가이드입니다.

## 목차

1. [PLC 단일 조회](#1-plc-단일-조회)
2. [PLC 목록 조회](#2-plc-목록-조회)
3. [PLC-PGM 매핑 저장](#3-plc-pgm-매핑-저장)
4. [PLC Tree 구조 조회](#4-plc-tree-구조-조회)
5. [드롭다운용 마스터 데이터 조회](#5-드롭다운용-마스터-데이터-조회)
6. [매핑 화면용 드롭다운 데이터 조회](#6-매핑-화면용-드롭다운-데이터-조회)
7. [PLC 삭제](#7-plc-삭제)
8. [PLC 다건 저장](#8-plc-다건-저장)
9. [PLC 다건 수정](#9-plc-다건-수정)

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
- `is_deleted=true`인 경우 404 Not Found 반환

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
<td>페이지당 항목 수 (최소: 1, 최대: 10000, 페이지네이션 없이 모든 데이터를 가져오려면 10000 사용)</td>
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
      "plc_uuid": "plc_uuid_001",
      "plc_id": "M1CFB01000",
      "plc_name": "01_01_CELL_FABRICATOR",
      "plant": "KY1",
      "plant_id": "KY1",
      "process": "모듈",
      "process_id": "process_001",
      "line": "1라인",
      "line_id": "line_001",
      "unit": "1",
      "program_id": "PGM_01",
      "mapping_user": "user",
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
<td><code>items[].plc_uuid</code></td>
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
<td><code>items[].plant_id</code></td>
<td>string</td>
<td>Plant ID</td>
</tr>
<tr>
<td><code>items[].process</code></td>
<td>string</td>
<td>공정 이름</td>
</tr>
<tr>
<td><code>items[].process_id</code></td>
<td>string</td>
<td>공정 ID</td>
</tr>
<tr>
<td><code>items[].line</code></td>
<td>string</td>
<td>Line 이름</td>
</tr>
<tr>
<td><code>items[].line_id</code></td>
<td>string</td>
<td>Line ID</td>
</tr>
<tr>
<td><code>items[].unit</code></td>
<td>string</td>
<td>호기</td>
</tr>
<tr>
<td><code>items[].program_id</code></td>
<td>string</td>
<td>매핑된 PGM ID (매핑되지 않은 경우 null)</td>
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

### 페이지네이션 비활성화 (모든 데이터 조회)

페이지네이션 없이 모든 데이터를 한 번에 가져오려면 `page_size=10000`을 사용하세요:

```
GET /v1/plcs?page=1&page_size=10000
```

**주의사항:**
- `page_size`의 최대값은 10000입니다
- 데이터가 10000개를 초과하는 경우 여러 번 호출해야 합니다
- 성능을 고려하여 필요한 경우에만 사용하세요

### 사용 예시

#### 페이지네이션 사용 (기본)
```
GET /v1/plcs?page=1&page_size=10
GET /v1/plcs?page=2&page_size=20
```

#### 페이지네이션 없이 모든 데이터 조회
```
GET /v1/plcs?page=1&page_size=10000
GET /v1/plcs?plant_id=KY1&page=1&page_size=10000
```

#### 필터링 및 검색
```
GET /v1/plcs?plant_id=KY1&process_id=process001&line_id=line001
GET /v1/plcs?plc_id=M1CFB01000
GET /v1/plcs?program_name=라벨부착
```

---

## 3. PLC-PGM 매핑 저장

여러 PLC에 각각 다른 PGM 프로그램을 매핑합니다. 여러 매핑 항목을 한 번에 처리할 수 있습니다.

### 엔드포인트

```
PUT /v1/plcs/mapping
```

### 요청 Body

```json
{
  "items": [
    {
      "plc_uuids": ["plc-uuid-001", "plc-uuid-002"],
      "program_id": "PGM_01"
    },
    {
      "plc_uuids": ["plc-uuid-003"],
      "program_id": "PGM_02"
    },
    {
      "plc_uuids": ["plc-uuid-004"],
      "program_id": ""
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
<td>PLC-PGM 매핑 항목 리스트 (최소 1개 이상)</td>
</tr>
<tr>
<td><code>items[].plc_uuids</code></td>
<td>array[string]</td>
<td><strong>예</strong></td>
<td>매핑할 PLC UUID 리스트 (최소 1개 이상)</td>
</tr>
<tr>
<td><code>items[].program_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>매핑할 PGM 프로그램 ID (빈 문자열("")이면 매핑 해제)</td>
</tr>
</tbody>
</table>

### Program ID 처리 규칙

- **Program 매핑**: `program_id`에 실제 Program ID 값을 전달
- **매핑 해제**: `program_id`에 빈 문자열(`""`)을 전달하면 자동으로 `null`로 변환되어 매핑이 해제됩니다
- **외래키 제약**: 빈 문자열은 자동으로 `null`로 변환되므로 외래키 제약 위반 없이 안전하게 처리됩니다

### 응답 형식

```json
{
  "success": true,
  "mapped_count": 3,
  "failed_count": 0,
  "errors": []
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
<td><code>success</code></td>
<td>boolean</td>
<td>전체 성공 여부 (모든 PLC가 성공적으로 매핑된 경우 true)</td>
</tr>
<tr>
<td><code>mapped_count</code></td>
<td>integer</td>
<td>성공적으로 매핑된 PLC 개수</td>
</tr>
<tr>
<td><code>failed_count</code></td>
<td>integer</td>
<td>매핑 실패한 PLC 개수</td>
</tr>
<tr>
<td><code>errors</code></td>
<td>array[string]</td>
<td>실패한 PLC의 오류 정보 리스트</td>
</tr>
</tbody>
</table>

### 처리 로직

1. 각 매핑 항목을 순회하며 처리
2. 각 PLC의 현재 `program_id`를 `metadata_json.previous_program_id`에 저장 (변경 이력 관리)
3. 새로운 `program_id`로 업데이트 (빈 문자열이면 `null`로 변환)
4. `mapping_dt` 업데이트
5. `mapping_user`는 내부에서 임시로 "user"로 설정 (나중에 헤더 토큰으로 처리 예정)

**참고:** 
- `previous_program_id`는 `METADATA_JSON` 필드 내에 저장되며, Program ID 변경 이력을 추적하기 위해 사용됩니다.
- `mapping_user` 파라미터는 제거되었으며, 현재는 내부에서 임시로 "user"로 설정됩니다. 향후 헤더의 인증 토큰에서 사용자 정보를 추출하여 처리할 예정입니다.

### 사용 예시

#### 여러 PLC에 각각 다른 Program 매핑
```bash
curl -X PUT "http://localhost:8000/v1/plcs/mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plc_uuids": ["plc-uuid-001", "plc-uuid-002"],
        "program_id": "PGM_01"
      },
      {
        "plc_uuids": ["plc-uuid-003"],
        "program_id": "PGM_02"
      }
    ]
  }'
```

#### Program 매핑 해제
```bash
curl -X PUT "http://localhost:8000/v1/plcs/mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plc_uuids": ["plc-uuid-001"],
        "program_id": ""
      }
    ]
  }'
```

#### 복합 매핑 (매핑 + 해제)
```bash
curl -X PUT "http://localhost:8000/v1/plcs/mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plc_uuids": ["plc-uuid-001", "plc-uuid-002"],
        "program_id": "PGM_01"
      },
      {
        "plc_uuids": ["plc-uuid-003"],
        "program_id": ""
      }
    ]
  }'
```

### 예외 상황

- **PLC를 찾을 수 없는 경우**: 해당 PLC는 실패 처리되고 `errors` 배열에 오류 메시지가 추가됩니다
- **PGM 프로그램을 찾을 수 없는 경우**: 해당 PLC는 실패 처리되고 `errors` 배열에 오류 메시지가 추가됩니다
- **일부 실패**: 일부 PLC만 실패한 경우 `success=false`, `failed_count`에 실패 개수, `errors`에 오류 목록이 반환됩니다

### 특징

1. **다중 매핑 지원**: 여러 매핑 항목을 한 번에 처리할 수 있습니다
2. **유연한 매핑**: 각 항목마다 서로 다른 Program ID를 매핑할 수 있습니다
3. **매핑 해제**: 빈 문자열을 전달하면 자동으로 `null`로 변환되어 매핑이 해제됩니다
4. **부분 실패 허용**: 일부 PLC만 실패해도 나머지는 정상 처리됩니다

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

- 삭제되지 않은 PLC만 조회 (`is_deleted=false`, 사용 중으로 인식)
- `program_id`가 있는 PLC만 조회 (프로그램이 매핑된 PLC만)
- 활성화된 Plant, Process, Line만 조회
- 정렬 순서: Plant → Process → Line → PLC명 → 호기

### 사용 예시

```
GET /v1/plcs/tree
```

---

## 5. PLC 삭제

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

### 단일/일괄 삭제

- `plc_uuids` 배열에 1개만 넣으면 단일 삭제
- `plc_uuids` 배열에 여러 개를 넣으면 일괄 삭제

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

## 6. PLC 다건 저장

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

## 7. PLC 다건 수정

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
      "program_id": "pgm_001",
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
      "program_id": "",
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
<td><code>items[].program_id</code></td>
<td>string</td>
<td>아니오</td>
<td>Program ID (변경 시, 빈 문자열("")이면 매핑 해제)</td>
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

### Program ID 매핑/해제

`program_id` 필드를 사용하여 Program 매핑을 변경하거나 해제할 수 있습니다:

- **Program 매핑**: `program_id`에 실제 Program ID 값을 전달
- **매핑 해제**: `program_id`에 빈 문자열(`""`)을 전달하면 `null`로 설정되어 매핑이 해제됩니다
- **변경하지 않음**: `program_id` 필드를 생략하거나 `null`을 전달하면 기존 값이 유지됩니다

**주의사항:**
- 빈 문자열(`""`)을 전달하면 외래키 제약 위반 없이 안전하게 `null`로 변환됩니다
- `program_id`는 `unique` 제약이 있으므로, 다른 PLC가 이미 사용 중인 Program ID는 매핑할 수 없습니다
- Program ID가 존재하지 않으면 에러가 발생합니다

### 사용 예시

#### 기본 수정 (Program ID 변경 없음)
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

#### Program ID 매핑
```bash
curl -X PUT "http://localhost:8000/v1/plcs/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plc_uuid": "plc-uuid-001",
        "plc_name": "01_01_CELL_FABRICATOR",
        "plc_id": "M1CFB01000",
        "program_id": "pgm_001",
        "update_user": "admin"
      }
    ]
  }'
```

#### Program ID 매핑 해제 (null로 설정)
```bash
curl -X PUT "http://localhost:8000/v1/plcs/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "plc_uuid": "plc-uuid-001",
        "plc_name": "01_01_CELL_FABRICATOR",
        "plc_id": "M1CFB01000",
        "program_id": "",
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

1. **소프트 삭제**: PLC 삭제는 실제 데이터를 삭제하지 않고 `is_deleted=True`로 설정합니다. `is_deleted=false`인 것은 사용 중으로 인식됩니다.
2. **매핑 해제**: PLC 삭제 시 매핑된 `program_id`도 함께 제거됩니다.
3. **Program ID 매핑 해제**: `PUT /v1/plcs/batch` API에서 `program_id`에 빈 문자열(`""`)을 전달하면 외래키 제약 위반 없이 안전하게 `null`로 설정되어 매핑이 해제됩니다. 빈 문자열을 직접 전달하면 자동으로 `None`으로 변환됩니다.
4. **권한 기반 필터링**: 매핑 화면용 드롭다운 API는 `user_id`가 필수이며, 사용자 권한에 따라 공정 목록이 필터링됩니다.
5. **다건 저장/수정**: 저장과 수정은 별도의 API로 분리되어 있습니다. `POST /v1/plcs/batch`는 생성만, `PUT /v1/plcs/batch`는 수정만 처리합니다.
6. **페이지네이션**: 기본값은 `page=1`, `page_size=10`입니다. 페이지네이션 없이 모든 데이터를 한 번에 가져오려면 `page_size=10000`을 사용하세요 (최대값: 10000).
7. **검색**: `plc_id`, `plc_name`, `program_name`은 부분 일치 검색을 지원합니다.
8. **조회 필터링**: 모든 PLC 조회 API는 `is_deleted=false`인 것만 반환합니다.
9. **단일/일괄 삭제**: 삭제 API는 `plc_uuids` 배열에 1개만 넣으면 단일 삭제, 여러 개를 넣으면 일괄 삭제로 동작합니다.

