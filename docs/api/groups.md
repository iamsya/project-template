# 그룹 관리 API 가이드

그룹 관리(권한 관리) 화면에서 사용하는 모든 API 엔드포인트 가이드입니다.

## 목차

1. [Role 목록 조회](#1-role-목록-조회)
2. [그룹 목록 조회](#2-그룹-목록-조회)
3. [그룹 상세 조회](#3-그룹-상세-조회)
4. [그룹 생성](#4-그룹-생성)
5. [그룹 수정](#5-그룹-수정)
6. [그룹 삭제](#6-그룹-삭제)
7. [그룹에 공정 추가](#7-그룹에-공정-추가)
8. [그룹에서 공정 제거](#8-그룹에서-공정-제거)
9. [그룹에 사용자 추가](#9-그룹에-사용자-추가)
10. [그룹에서 사용자 제거](#10-그룹에서-사용자-제거)
11. [그룹별 사용자 목록 조회](#11-그룹별-사용자-목록-조회)
12. [그룹별 공정 목록 조회](#12-그룹별-공정-목록-조회)

---

## 1. Role 목록 조회

화면에 표시할 Role 목록을 조회합니다. ROLE_MASTER 테이블에서 활성화된 Role만 조회합니다.

### 엔드포인트

```
GET /v1/groups/roles
```

### 요청 파라미터

없음

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "role_id": "system_admin",
      "role_name": "시스템 관리자",
      "description": "기준정보 + 사용자관리 + 모든 공정 접근 가능",
      "display_order": 1,
      "is_active": true
    },
    {
      "role_id": "integrated_admin",
      "role_name": "통합관리자",
      "description": "모든 공정 접근 가능",
      "display_order": 2,
      "is_active": true
    },
    {
      "role_id": "process_manager",
      "role_name": "공정 관리자",
      "description": "지정한 공정만 접근 가능",
      "display_order": 3,
      "is_active": true
    }
  ]
}
```

### 사용 예시

```bash
curl -X GET "http://localhost:8000/v1/groups/roles"
```

### 설명

- ROLE_MASTER 테이블에서 IS_ACTIVE=true인 Role만 조회
- DISPLAY_ORDER 순서로 정렬하여 반환
- 화면의 Role 선택 라디오 버튼 또는 탭에 사용

---

## 2. 그룹 목록 조회

Role별로 그룹 목록을 조회합니다. 선택된 Role에 해당하는 그룹만 반환합니다.

### 엔드포인트

```
GET /v1/groups
```

### 요청 파라미터

**Query Parameters:**

- role_id (선택사항, string): Role ID로 필터링
  - 예: system_admin, integrated_admin, process_manager
  - 없으면 모든 Role의 그룹 반환

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "group_id": "group_system_admin",
      "group_name": "시스템 관리자",
      "role_id": "system_admin",
      "role_name": "시스템 관리자",
      "description": "시스템 관리자 그룹",
      "process_count": 0,
      "user_count": 1,
      "is_active": true,
      "create_dt": "2025-01-01T00:00:00",
      "create_user": "admin"
    },
    {
      "group_id": "group_process_manager_001",
      "group_name": "모듈/화성 담당",
      "role_id": "process_manager",
      "role_name": "공정 관리자",
      "description": "모듈, 화성 공정 담당 그룹",
      "process_count": 2,
      "user_count": 1,
      "is_active": true,
      "create_dt": "2025-01-01T00:00:00",
      "create_user": "admin"
    }
  ],
  "total": 2
}
```

### 사용 예시

```bash
# 시스템 관리자 Role의 그룹만 조회
curl -X GET "http://localhost:8000/v1/groups?role_id=system_admin"

# 공정 관리자 Role의 그룹만 조회
curl -X GET "http://localhost:8000/v1/groups?role_id=process_manager"

# 모든 그룹 조회
curl -X GET "http://localhost:8000/v1/groups"
```

### 설명

- role_id가 제공되면 해당 Role의 그룹만 반환
- process_count: 그룹에 연결된 공정 개수 (공정 관리자만 0 이상)
- user_count: 그룹에 속한 사용자 개수
- 시스템 관리자/통합관리자 그룹은 process_count가 0 (모든 공정 접근 가능)

---

## 3. 그룹 상세 조회

특정 그룹의 상세 정보를 조회합니다. 그룹 정보, 연결된 공정 목록, 속한 사용자 목록을 포함합니다.

### 엔드포인트

```
GET /v1/groups/{group_id}
```

### 경로 파라미터

- group_id (필수, string): 조회할 그룹 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "data": {
    "group_id": "group_process_manager_001",
    "group_name": "모듈/화성 담당",
    "role_id": "process_manager",
    "role_name": "공정 관리자",
    "description": "모듈, 화성 공정 담당 그룹",
    "is_active": true,
    "create_dt": "2025-01-01T00:00:00",
    "create_user": "admin",
    "update_dt": null,
    "update_user": null,
    "processes": [
      {
        "process_id": "prc_module",
        "process_name": "모듈"
      },
      {
        "process_id": "prc_hwaseong",
        "process_name": "화성"
      }
    ],
    "users": [
      {
        "user_id": "user_process_manager_001",
        "employee_id": "SO10003",
        "name": "박모듈"
      }
    ]
  }
}
```

### 사용 예시

```bash
curl -X GET "http://localhost:8000/v1/groups/group_process_manager_001"
```

### 설명

- 그룹 정보와 함께 연결된 공정 목록, 속한 사용자 목록을 함께 반환
- 공정 관리자 그룹만 processes 배열에 데이터가 있음
- 시스템 관리자/통합관리자 그룹은 processes 배열이 비어있음 (모든 공정 접근 가능)

---

## 4. 그룹 생성

새로운 그룹을 생성합니다.

### 엔드포인트

```
POST /v1/groups
```

### Content-Type

```
application/json
```

### 요청 Body

```json
{
  "group_name": "모듈/화성 담당",
  "role_id": "process_manager",
  "description": "모듈, 화성 공정 담당 그룹",
  "process_ids": ["prc_module", "prc_hwaseong"],
  "create_user": "admin"
}
```

### 요청 필드 설명

- group_name (필수, string): 그룹명
- role_id (필수, string): Role ID (system_admin, integrated_admin, process_manager)
- description (선택사항, string): 그룹 설명
- process_ids (선택사항, array): 공정 ID 목록
  - 공정 관리자 Role일 때만 사용
  - 시스템 관리자/통합관리자 Role일 때는 빈 배열 또는 생략
- create_user (필수, string): 생성자 ID

### 응답 형식

**성공 시 (201 Created):**

```json
{
  "success": true,
  "message": "그룹이 생성되었습니다.",
  "data": {
    "group_id": "group_process_manager_001",
    "group_name": "모듈/화성 담당",
    "role_id": "process_manager",
    "role_name": "공정 관리자",
    "description": "모듈, 화성 공정 담당 그룹",
    "process_count": 2,
    "user_count": 0,
    "is_active": true,
    "create_dt": "2025-01-01T00:00:00",
    "create_user": "admin"
  }
}
```

### 사용 예시

```bash
curl -X POST "http://localhost:8000/v1/groups" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "모듈/화성 담당",
    "role_id": "process_manager",
    "description": "모듈, 화성 공정 담당 그룹",
    "process_ids": ["prc_module", "prc_hwaseong"],
    "create_user": "admin"
  }'
```

### 설명

- group_id는 자동 생성 (형식: group_{role_id}_{타임스탬프})
- role_id가 process_manager인 경우 process_ids 필수
- role_id가 system_admin 또는 integrated_admin인 경우 process_ids는 무시됨
- 그룹 생성 시 GROUP_PROCESSES 테이블에도 공정 권한이 함께 생성됨

---

## 5. 그룹 수정

기존 그룹의 정보를 수정합니다.

### 엔드포인트

```
PUT /v1/groups/{group_id}
```

### 경로 파라미터

- group_id (필수, string): 수정할 그룹 ID

### Content-Type

```
application/json
```

### 요청 Body

```json
{
  "group_name": "모듈/화성/전극 담당",
  "description": "모듈, 화성, 전극 공정 담당 그룹",
  "process_ids": ["prc_module", "prc_hwaseong", "prc_electrode"],
  "update_user": "admin"
}
```

### 요청 필드 설명

- group_name (선택사항, string): 그룹명
- description (선택사항, string): 그룹 설명
- process_ids (선택사항, array): 공정 ID 목록
  - 공정 관리자 그룹일 때만 사용
  - 제공되면 기존 공정 권한을 모두 삭제하고 새로 생성
- update_user (필수, string): 수정자 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "message": "그룹이 수정되었습니다.",
  "data": {
    "group_id": "group_process_manager_001",
    "group_name": "모듈/화성/전극 담당",
    "role_id": "process_manager",
    "role_name": "공정 관리자",
    "description": "모듈, 화성, 전극 공정 담당 그룹",
    "process_count": 3,
    "user_count": 1,
    "is_active": true,
    "update_dt": "2025-01-01T01:00:00",
    "update_user": "admin"
  }
}
```

### 사용 예시

```bash
curl -X PUT "http://localhost:8000/v1/groups/group_process_manager_001" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "모듈/화성/전극 담당",
    "description": "모듈, 화성, 전극 공정 담당 그룹",
    "process_ids": ["prc_module", "prc_hwaseong", "prc_electrode"],
    "update_user": "admin"
  }'
```

### 설명

- role_id는 수정 불가 (그룹의 Role은 변경할 수 없음)
- process_ids를 제공하면 기존 GROUP_PROCESSES 데이터를 모두 삭제하고 새로 생성
- process_ids를 제공하지 않으면 공정 권한은 변경되지 않음

---

## 6. 그룹 삭제

그룹을 삭제합니다. 관련된 사용자 매핑과 공정 권한도 함께 삭제됩니다.

### 엔드포인트

```
DELETE /v1/groups/{group_id}
```

### 경로 파라미터

- group_id (필수, string): 삭제할 그룹 ID

### Query Parameters

- deleted_by (필수, string): 삭제자 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "message": "그룹이 삭제되었습니다.",
  "data": {
    "group_id": "group_process_manager_001",
    "deleted_user_mappings": 1,
    "deleted_process_permissions": 2
  }
}
```

### 사용 예시

```bash
curl -X DELETE "http://localhost:8000/v1/groups/group_process_manager_001?deleted_by=admin"
```

### 설명

- 그룹 삭제 시 관련 데이터도 함께 실제 삭제됨
- USER_GROUPS 테이블의 관련 매핑 삭제
- GROUP_PROCESSES 테이블의 관련 공정 권한 삭제
- GROUPS 테이블의 그룹 삭제
- 삭제 순서: USER_GROUPS → GROUP_PROCESSES → GROUPS (FK 제약조건)

---

## 7. 그룹에 공정 추가

공정 관리자 그룹에 공정을 추가합니다.

### 엔드포인트

```
POST /v1/groups/{group_id}/processes
```

### 경로 파라미터

- group_id (필수, string): 그룹 ID

### Content-Type

```
application/json
```

### 요청 Body

```json
{
  "process_id": "prc_electrode",
  "create_user": "admin"
}
```

### 요청 필드 설명

- process_id (필수, string): 추가할 공정 ID
- create_user (필수, string): 생성자 ID

### 응답 형식

**성공 시 (201 Created):**

```json
{
  "success": true,
  "message": "공정이 추가되었습니다.",
  "data": {
    "permission_id": "perm_005",
    "group_id": "group_process_manager_001",
    "process_id": "prc_electrode",
    "process_name": "전극",
    "is_active": true
  }
}
```

### 사용 예시

```bash
curl -X POST "http://localhost:8000/v1/groups/group_process_manager_001/processes" \
  -H "Content-Type: application/json" \
  -d '{
    "process_id": "prc_electrode",
    "create_user": "admin"
  }'
```

### 설명

- 공정 관리자 그룹에만 사용 가능
- 시스템 관리자/통합관리자 그룹에는 사용 불가 (모든 공정 접근 가능하므로)
- 이미 추가된 공정이면 에러 반환

---

## 8. 그룹에서 공정 제거

공정 관리자 그룹에서 공정을 제거합니다.

### 엔드포인트

```
DELETE /v1/groups/{group_id}/processes/{process_id}
```

### 경로 파라미터

- group_id (필수, string): 그룹 ID
- process_id (필수, string): 제거할 공정 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "message": "공정이 제거되었습니다.",
  "data": {
    "permission_id": "perm_005",
    "group_id": "group_process_manager_001",
    "process_id": "prc_electrode"
  }
}
```

### 사용 예시

```bash
curl -X DELETE "http://localhost:8000/v1/groups/group_process_manager_001/processes/prc_electrode"
```

### 설명

- 공정 관리자 그룹에만 사용 가능
- GROUP_PROCESSES 테이블에서 해당 권한 레코드 삭제

---

## 9. 그룹에 사용자 추가

그룹에 사용자를 추가합니다.

### 엔드포인트

```
POST /v1/groups/{group_id}/users
```

### 경로 파라미터

- group_id (필수, string): 그룹 ID

### Content-Type

```
application/json
```

### 요청 Body

```json
{
  "user_id": "user_process_manager_002",
  "create_user": "admin"
}
```

### 요청 필드 설명

- user_id (필수, string): 추가할 사용자 ID
- create_user (필수, string): 생성자 ID

### 응답 형식

**성공 시 (201 Created):**

```json
{
  "success": true,
  "message": "사용자가 추가되었습니다.",
  "data": {
    "mapping_id": "mapping_005",
    "group_id": "group_process_manager_001",
    "user_id": "user_process_manager_002",
    "employee_id": "SO10004",
    "name": "최화성",
    "is_active": true
  }
}
```

### 사용 예시

```bash
curl -X POST "http://localhost:8000/v1/groups/group_process_manager_001/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_process_manager_002",
    "create_user": "admin"
  }'
```

### 설명

- 사용자는 여러 그룹에 속할 수 있음
- 이미 추가된 사용자면 에러 반환
- USER_GROUPS 테이블에 매핑 레코드 생성

---

## 10. 그룹에서 사용자 제거

그룹에서 사용자를 제거합니다.

### 엔드포인트

```
DELETE /v1/groups/{group_id}/users/{user_id}
```

### 경로 파라미터

- group_id (필수, string): 그룹 ID
- user_id (필수, string): 제거할 사용자 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "message": "사용자가 제거되었습니다.",
  "data": {
    "mapping_id": "mapping_005",
    "group_id": "group_process_manager_001",
    "user_id": "user_process_manager_002"
  }
}
```

### 사용 예시

```bash
curl -X DELETE "http://localhost:8000/v1/groups/group_process_manager_001/users/user_process_manager_002"
```

### 설명

- USER_GROUPS 테이블에서 해당 매핑 레코드 삭제
- 사용자가 다른 그룹에 속해있으면 해당 그룹의 권한은 유지됨

---

## 11. 그룹별 사용자 목록 조회

특정 그룹에 속한 사용자 목록을 조회합니다.

### 엔드포인트

```
GET /v1/groups/{group_id}/users
```

### 경로 파라미터

- group_id (필수, string): 그룹 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "user_id": "user_process_manager_001",
      "employee_id": "SO10003",
      "name": "박모듈",
      "mapping_id": "mapping_003",
      "is_active": true,
      "create_dt": "2025-01-01T00:00:00"
    }
  ],
  "total": 1
}
```

### 사용 예시

```bash
curl -X GET "http://localhost:8000/v1/groups/group_process_manager_001/users"
```

### 설명

- 그룹에 속한 활성 사용자만 조회 (IS_ACTIVE=true)
- 사용자 정보와 매핑 정보를 함께 반환

---

## 12. 그룹별 공정 목록 조회

특정 그룹에 연결된 공정 목록을 조회합니다.

### 엔드포인트

```
GET /v1/groups/{group_id}/processes
```

### 경로 파라미터

- group_id (필수, string): 그룹 ID

### 응답 형식

**성공 시 (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "process_id": "prc_module",
      "process_name": "모듈",
      "permission_id": "perm_001",
      "is_active": true,
      "create_dt": "2025-01-01T00:00:00"
    },
    {
      "process_id": "prc_hwaseong",
      "process_name": "화성",
      "permission_id": "perm_002",
      "is_active": true,
      "create_dt": "2025-01-01T00:00:00"
    }
  ],
  "total": 2
}
```

### 사용 예시

```bash
curl -X GET "http://localhost:8000/v1/groups/group_process_manager_001/processes"
```

### 설명

- 공정 관리자 그룹만 공정 목록이 반환됨
- 시스템 관리자/통합관리자 그룹은 빈 배열 반환 (모든 공정 접근 가능)
- 활성 공정 권한만 조회 (IS_ACTIVE=true)

---

## 에러 응답

모든 API는 실패 시 다음 형식으로 응답합니다:

```json
{
  "success": false,
  "error": {
    "code": "GROUP_NOT_FOUND",
    "message": "그룹을 찾을 수 없습니다.",
    "details": "group_id=group_invalid"
  }
}
```

### 주요 에러 코드

- GROUP_NOT_FOUND: 그룹을 찾을 수 없음
- ROLE_NOT_FOUND: Role을 찾을 수 없음
- PROCESS_NOT_FOUND: 공정을 찾을 수 없음
- USER_NOT_FOUND: 사용자를 찾을 수 없음
- GROUP_DELETE_ERROR: 그룹 삭제 중 오류
- INVALID_ROLE: 잘못된 Role ID
- DUPLICATE_PROCESS: 이미 추가된 공정
- DUPLICATE_USER: 이미 추가된 사용자

---

## 권한 체크

모든 그룹 관리 API는 시스템 관리자 권한이 필요합니다.

- 시스템 관리자: 모든 API 접근 가능
- 통합관리자: 그룹 관리 API 접근 불가
- 공정 관리자: 그룹 관리 API 접근 불가
- 일반 사용자: 그룹 관리 API 접근 불가

---

## 참고사항

1. **그룹 ID 생성 규칙**
   - 형식: `group_{role_id}_{타임스탬프}`
   - 예: `group_process_manager_001_2501011200`

2. **권한 ID 생성 규칙**
   - 형식: `perm_{타임스탬프}`
   - 예: `perm_2501011200`

3. **매핑 ID 생성 규칙**
   - 형식: `mapping_{타임스탬프}`
   - 예: `mapping_2501011200`

4. **Role별 공정 권한**
   - 시스템 관리자: 모든 공정 접근 (GROUP_PROCESSES에 데이터 없음)
   - 통합관리자: 모든 공정 접근 (GROUP_PROCESSES에 데이터 없음)
   - 공정 관리자: GROUP_PROCESSES에 지정된 공정만 접근

5. **여러 그룹에 속한 사용자**
   - 사용자는 여러 그룹에 속할 수 있음
   - 제일 넓은 권한이 적용됨
   - 시스템 관리자 또는 통합관리자 그룹이 하나라도 있으면 모든 공정 접근 가능
   - 공정 관리자 그룹만 있는 경우 모든 그룹의 공정을 합집합으로 반환

