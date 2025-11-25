# 그룹 관리(권한 관리) 화면 및 API 동작 가이드

## 1. 테이블 데이터 예시

### 1.1 ROLE_MASTER 테이블

| ROLE_ID | ROLE_NAME | DESCRIPTION | DISPLAY_ORDER | IS_ACTIVE |
|---------|-----------|-------------|---------------|-----------|
| system_admin | 시스템 관리자 | 기준정보 + 사용자관리 + 모든 공정 접근 가능 | 1 | true |
| integrated_admin | 통합관리자 | 모든 공정 접근 가능 | 2 | true |
| process_manager | 공정 관리자 | 지정한 공정만 접근 가능 | 3 | true |

### 1.2 GROUPS 테이블

| GROUP_ID | GROUP_NAME | ROLE_ID | DESCRIPTION | IS_ACTIVE | IS_DELETED |
|----------|------------|---------|-------------|-----------|------------|
| group_system_admin | 시스템 관리자 | system_admin | 시스템 관리자 그룹 | true | false |
| group_integrated_admin | 통합관리자 | integrated_admin | 통합관리자 그룹 | true | false |
| group_process_manager_001 | 모듈/화성 담당 | process_manager | 모듈, 화성 공정 담당 그룹 | true | false |
| group_process_manager_002 | 전극/조립 담당 | process_manager | 전극, 조립 공정 담당 그룹 | true | false |

### 1.3 PROCESS_MASTER 테이블

| PROCESS_ID | PROCESS_NAME | IS_ACTIVE |
|------------|--------------|-----------|
| prc_module | 모듈 | true |
| prc_hwaseong | 화성 | true |
| prc_electrode | 전극 | true |
| prc_assembly | 조립 | true |

### 1.4 GROUP_PROCESSES 테이블

| PERMISSION_ID | GROUP_ID | PROCESS_ID | IS_ACTIVE |
|---------------|----------|------------|-----------|
| perm_001 | group_process_manager_001 | prc_module | true |
| perm_002 | group_process_manager_001 | prc_hwaseong | true |
| perm_003 | group_process_manager_002 | prc_electrode | true |
| perm_004 | group_process_manager_002 | prc_assembly | true |

### 1.5 USER_GROUPS 테이블

| MAPPING_ID | USER_ID | GROUP_ID | IS_ACTIVE |
|------------|---------|----------|-----------|
| mapping_001 | user_sys_admin | group_system_admin | true |
| mapping_002 | user_integrated_admin | group_integrated_admin | true |
| mapping_003 | user_process_manager_001 | group_process_manager_001 | true |
| mapping_004 | user_process_manager_002 | group_process_manager_002 | true |

### 1.6 USERS 테이블

| USER_ID | EMPLOYEE_ID | NAME | IS_ACTIVE |
|---------|-------------|------|-----------|
| user_sys_admin | SO10001 | 김관리 | true |
| user_integrated_admin | SO10002 | 이통합 | true |
| user_process_manager_001 | SO10003 | 박모듈 | true |
| user_process_manager_002 | SO10004 | 최화성 | true |
| user_normal | SO10005 | 정일반 | true |

---

## 2. 그룹 관리(권한 관리) 화면 동작

### 2.1 화면 구성

**그룹 관리 화면 구조:**
```
┌─────────────────────────────────────────────────────────┐
│ Role 선택 (라디오 버튼 또는 탭)                           │
├─────────────────────────────────────────────────────────┤
│ ● 시스템 관리자  ○ 통합관리자  ○ 공정 관리자         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ [선택된 Role]의 그룹 목록                                 │
├─────────────────────────────────────────────────────────┤
│ 그룹명 | 공정 | 사용자 수 | 액션                          │
├─────────────────────────────────────────────────────────┤
│ 시스템 관리자 | 전체 | 1명 | [수정] [삭제]               │
└─────────────────────────────────────────────────────────┘

[그룹 추가] 버튼
```

**화면 동작:**
- Role 선택 시 해당 Role의 그룹 목록만 표시
- 시스템 관리자 Role 선택 → 시스템 관리자 그룹만 표시
- 통합관리자 Role 선택 → 통합관리자 그룹만 표시
- 공정 관리자 Role 선택 → 공정 관리자 그룹들만 표시 (여러 개 가능)

### 2.2 그룹 생성 시나리오

**시나리오: "모듈/화성 담당" 그룹 생성 (공정 관리자 Role 선택 상태)**

#### 2.2.1 화면 입력

```
1. Role 선택 (화면 상단)
   ● 시스템 관리자
   ○ 통합관리자
   ○ 공정 관리자  ← 선택

2. [그룹 추가] 버튼 클릭

3. 그룹 생성 팝업/폼
   그룹명: "모듈/화성 담당"
   
   공정 선택 (공정 관리자 Role이므로 활성화):
     ☑ 모듈 (prc_module)
     ☑ 화성 (prc_hwaseong)
     ☐ 전극 (prc_electrode)
     ☐ 조립 (prc_assembly)
   
   설명: "모듈, 화성 공정 담당 그룹"
   
   [저장] [취소]
```

**참고:**
- Role은 화면 상단에서 선택 (현재 선택된 Role이 공정 관리자)
- 그룹 생성 시 Role은 현재 선택된 Role로 자동 설정
- 시스템 관리자/통합관리자 Role 선택 시: 공정 선택 영역 비활성화
- 공정 관리자 Role 선택 시: 공정 선택 영역 활성화

#### 2.2.2 API 요청

```http
POST /api/groups
Content-Type: application/json

{
  "group_name": "모듈/화성 담당",
  "role_id": "process_manager",
  "description": "모듈, 화성 공정 담당 그룹",
  "process_ids": ["prc_module", "prc_hwaseong"],
  "create_user": "admin"
}
```

#### 2.2.3 데이터베이스 저장

**1. GROUPS 테이블에 그룹 생성:**
```sql
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_process_manager_001',  -- 자동 생성
        '모듈/화성 담당',
        'process_manager',            -- ROLE_MASTER 참조
        '모듈, 화성 공정 담당 그룹',
        'admin'
    );
```

**2. GROUP_PROCESSES 테이블에 공정 권한 추가:**
```sql
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_001', 'group_process_manager_001', 'prc_module', 'admin'),
    ('perm_002', 'group_process_manager_001', 'prc_hwaseong', 'admin');
```

**3. 저장 결과:**

**GROUPS 테이블:**
| GROUP_ID | GROUP_NAME | ROLE_ID | DESCRIPTION |
|----------|------------|---------|-------------|
| group_process_manager_001 | 모듈/화성 담당 | process_manager | 모듈, 화성 공정 담당 그룹 |

**GROUP_PROCESSES 테이블:**
| PERMISSION_ID | GROUP_ID | PROCESS_ID |
|---------------|----------|------------|
| perm_001 | group_process_manager_001 | prc_module |
| perm_002 | group_process_manager_001 | prc_hwaseong |

### 2.3 그룹 목록 조회 API

**API 요청 (Role별 필터링):**
```http
GET /api/groups?role_id=process_manager
```

**API 응답 (공정 관리자 Role 선택 시):**
```json
{
  "role_id": "process_manager",
  "role_name": "공정 관리자",
  "groups": [
    {
      "group_id": "group_process_manager_001",
      "group_name": "모듈/화성 담당",
      "description": "모듈, 화성 공정 담당 그룹",
      "process_count": 2,
      "user_count": 1,
      "processes": [
        {"process_id": "prc_module", "process_name": "모듈"},
        {"process_id": "prc_hwaseong", "process_name": "화성"}
      ],
      "users": [
        {"user_id": "user_process_manager_001", "name": "박모듈"}
      ]
    },
    {
      "group_id": "group_process_manager_002",
      "group_name": "전극/조립 담당",
      "description": "전극, 조립 공정 담당 그룹",
      "process_count": 2,
      "user_count": 1,
      "processes": [
        {"process_id": "prc_electrode", "process_name": "전극"},
        {"process_id": "prc_assembly", "process_name": "조립"}
      ],
      "users": [
        {"user_id": "user_process_manager_002", "name": "최화성"}
      ]
    }
  ]
}
```

**API 응답 (시스템 관리자 Role 선택 시):**
```http
GET /api/groups?role_id=system_admin
```

```json
{
  "role_id": "system_admin",
  "role_name": "시스템 관리자",
  "groups": [
    {
      "group_id": "group_system_admin",
      "group_name": "시스템 관리자",
      "description": "시스템 관리자 그룹",
      "process_count": 0,
      "user_count": 1,
      "processes": [],  // 시스템 관리자는 모든 공정 접근 가능
      "users": [
        {"user_id": "user_sys_admin", "name": "김관리"}
      ]
    }
  ]
}
```

**API 응답 (통합관리자 Role 선택 시):**
```http
GET /api/groups?role_id=integrated_admin
```

```json
{
  "role_id": "integrated_admin",
  "role_name": "통합관리자",
  "groups": [
    {
      "group_id": "group_integrated_admin",
      "group_name": "통합관리자",
      "description": "통합관리자 그룹",
      "process_count": 0,
      "user_count": 1,
      "processes": [],  // 통합관리자는 모든 공정 접근 가능
      "users": [
        {"user_id": "user_integrated_admin", "name": "이통합"}
      ]
    }
  ]
}
```

**SQL 쿼리 (Role별 필터링):**
```sql
SELECT 
    g.GROUP_ID,
    g.GROUP_NAME,
    g.ROLE_ID,
    rm.ROLE_NAME,
    g.DESCRIPTION,
    COUNT(DISTINCT gp.PROCESS_ID) AS process_count,
    COUNT(DISTINCT ug.USER_ID) AS user_count
FROM GROUPS g
INNER JOIN ROLE_MASTER rm ON g.ROLE_ID = rm.ROLE_ID
LEFT JOIN GROUP_PROCESSES gp ON g.GROUP_ID = gp.GROUP_ID AND gp.IS_ACTIVE = true
LEFT JOIN USER_GROUPS ug ON g.GROUP_ID = ug.GROUP_ID AND ug.IS_ACTIVE = true
WHERE g.IS_DELETED = false
    AND g.IS_ACTIVE = true
    AND g.ROLE_ID = 'process_manager'  -- 선택된 Role로 필터링
GROUP BY g.GROUP_ID, g.GROUP_NAME, g.ROLE_ID, rm.ROLE_NAME, g.DESCRIPTION
ORDER BY g.CREATE_DT DESC;
```

---

## 3. API 데이터 조회 시 권한별 동작

### 3.1 공정 목록 조회 API (`GET /api/masters/processes`)

**권한별 동작:**

#### 3.1.1 시스템 관리자 (user_sys_admin)

**요청:**
```http
GET /api/masters/processes?user_id=user_sys_admin
```

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → mapping_001: user_sys_admin → group_system_admin

2. GROUPS 조회
   → group_system_admin: ROLE_ID = 'system_admin'

3. ROLE_MASTER 조회
   → system_admin: ROLE_NAME = '시스템 관리자'

4. 권한 체크
   → role_id == 'system_admin' → 모든 공정 접근 가능

5. PROCESS_MASTER 조회
   → 모든 활성 공정 반환
```

**응답:**
```json
{
  "processes": [
    {"process_id": "prc_module", "process_name": "모듈"},
    {"process_id": "prc_hwaseong", "process_name": "화성"},
    {"process_id": "prc_electrode", "process_name": "전극"},
    {"process_id": "prc_assembly", "process_name": "조립"}
  ],
  "total": 4
}
```

#### 3.1.2 통합관리자 (user_integrated_admin)

**요청:**
```http
GET /api/masters/processes?user_id=user_integrated_admin
```

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → mapping_002: user_integrated_admin → group_integrated_admin

2. GROUPS 조회
   → group_integrated_admin: ROLE_ID = 'integrated_admin'

3. 권한 체크
   → role_id == 'integrated_admin' → 모든 공정 접근 가능

4. PROCESS_MASTER 조회
   → 모든 활성 공정 반환
```

**응답:**
```json
{
  "processes": [
    {"process_id": "prc_module", "process_name": "모듈"},
    {"process_id": "prc_hwaseong", "process_name": "화성"},
    {"process_id": "prc_electrode", "process_name": "전극"},
    {"process_id": "prc_assembly", "process_name": "조립"}
  ],
  "total": 4
}
```

#### 3.1.3 공정 관리자 (user_process_manager_001)

**요청:**
```http
GET /api/masters/processes?user_id=user_process_manager_001
```

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → mapping_003: user_process_manager_001 → group_process_manager_001

2. GROUPS 조회
   → group_process_manager_001: ROLE_ID = 'process_manager'

3. 권한 체크
   → role_id == 'process_manager' → GROUP_PROCESSES 확인 필요

4. GROUP_PROCESSES 조회
   → perm_001: group_process_manager_001 → prc_module
   → perm_002: group_process_manager_001 → prc_hwaseong

5. PROCESS_MASTER 조회 (필터링)
   → prc_module, prc_hwaseong만 반환
```

**응답:**
```json
{
  "processes": [
    {"process_id": "prc_module", "process_name": "모듈"},
    {"process_id": "prc_hwaseong", "process_name": "화성"}
  ],
  "total": 2
}
```

#### 3.1.4 일반 사용자 (user_normal)

**요청:**
```http
GET /api/masters/processes?user_id=user_normal
```

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → 조회 결과 없음 (테이블에 없음)

2. 권한 체크
   → 그룹 없음 → 접근 불가

3. 빈 리스트 반환
```

**응답:**
```json
{
  "processes": [],
  "total": 0
}
```

### 3.2 프로그램 목록 조회 API (`GET /api/programs`)

**권한별 동작:**

#### 3.2.1 시스템 관리자 (user_sys_admin)

**요청:**
```http
GET /api/programs?user_id=user_sys_admin&page=1&page_size=10
```

**데이터 흐름:**
```
1. 권한 체크
   → role_id == 'system_admin' → 모든 공정 접근 가능

2. PROGRAMS 테이블 조회
   → 모든 공정의 프로그램 조회 (필터링 없음)
```

**응답:**
```json
{
  "programs": [
    {
      "program_id": "pgm_001",
      "program_name": "모듈 프로그램",
      "process_id": "prc_module",
      "process_name": "모듈",
      "status": "completed"
    },
    {
      "program_id": "pgm_002",
      "program_name": "화성 프로그램",
      "process_id": "prc_hwaseong",
      "process_name": "화성",
      "status": "completed"
    },
    {
      "program_id": "pgm_003",
      "program_name": "전극 프로그램",
      "process_id": "prc_electrode",
      "process_name": "전극",
      "status": "completed"
    },
    {
      "program_id": "pgm_004",
      "program_name": "조립 프로그램",
      "process_id": "prc_assembly",
      "process_name": "조립",
      "status": "completed"
    }
  ],
  "total": 4,
  "page": 1,
  "page_size": 10
}
```

#### 3.2.2 통합관리자 (user_integrated_admin)

**요청:**
```http
GET /api/programs?user_id=user_integrated_admin&page=1&page_size=10
```

**데이터 흐름:**
```
1. 권한 체크
   → role_id == 'integrated_admin' → 모든 공정 접근 가능

2. PROGRAMS 테이블 조회
   → 모든 공정의 프로그램 조회 (필터링 없음)
```

**응답:** (시스템 관리자와 동일 - 모든 프로그램 반환)

#### 3.2.3 공정 관리자 (user_process_manager_001)

**요청:**
```http
GET /api/programs?user_id=user_process_manager_001&page=1&page_size=10
```

**데이터 흐름:**
```
1. 권한 체크
   → role_id == 'process_manager' → GROUP_PROCESSES 확인

2. GROUP_PROCESSES 조회
   → prc_module, prc_hwaseong

3. PROGRAMS 테이블 조회 (필터링)
   → process_id IN ('prc_module', 'prc_hwaseong')만 조회
```

**응답:**
```json
{
  "programs": [
    {
      "program_id": "pgm_001",
      "program_name": "모듈 프로그램",
      "process_id": "prc_module",
      "process_name": "모듈",
      "status": "completed"
    },
    {
      "program_id": "pgm_002",
      "program_name": "화성 프로그램",
      "process_id": "prc_hwaseong",
      "process_name": "화성",
      "status": "completed"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 10
}
```

**SQL 쿼리:**
```sql
SELECT p.*
FROM PROGRAMS p
WHERE p.IS_DELETED = false
    AND p.PROCESS_ID IN (
        SELECT gp.PROCESS_ID
        FROM USER_GROUPS ug
        INNER JOIN GROUPS g ON ug.GROUP_ID = g.GROUP_ID
        INNER JOIN GROUP_PROCESSES gp ON g.GROUP_ID = gp.GROUP_ID
        WHERE ug.USER_ID = 'user_process_manager_001'
            AND ug.IS_ACTIVE = true
            AND g.IS_ACTIVE = true
            AND g.IS_DELETED = false
            AND gp.IS_ACTIVE = true
    )
ORDER BY p.CREATE_DT DESC
LIMIT 10 OFFSET 0;
```

#### 3.2.4 일반 사용자 (user_normal)

**요청:**
```http
GET /api/programs?user_id=user_normal&page=1&page_size=10
```

**데이터 흐름:**
```
1. 권한 체크
   → 그룹 없음 → 접근 불가

2. 빈 리스트 반환
```

**응답:**
```json
{
  "programs": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

### 3.3 PLC 목록 조회 API (`GET /api/plcs`)

**권한별 동작:**

#### 3.3.1 시스템 관리자 (user_sys_admin)

**요청:**
```http
GET /api/plcs?user_id=user_sys_admin&page=1&page_size=10
```

**데이터 흐름:**
```
1. 권한 체크
   → role_id == 'system_admin' → 모든 공정 접근 가능

2. PLC 테이블 조회
   → 모든 공정의 PLC 조회 (필터링 없음)
```

**응답:** 모든 PLC 반환

#### 3.3.2 공정 관리자 (user_process_manager_001)

**요청:**
```http
GET /api/plcs?user_id=user_process_manager_001&page=1&page_size=10
```

**데이터 흐름:**
```
1. 권한 체크
   → role_id == 'process_manager' → GROUP_PROCESSES 확인

2. GROUP_PROCESSES 조회
   → prc_module, prc_hwaseong

3. PLC 테이블 조회 (필터링)
   → PROCESS_ID IN ('prc_module', 'prc_hwaseong')만 조회
```

**응답:** 모듈, 화성 공정의 PLC만 반환

---

## 4. 권한별 API 동작 요약표

| API | 시스템 관리자 | 통합관리자 | 공정 관리자 | 일반 사용자 |
|-----|-------------|--------------|-----------|-----------|
| `GET /api/masters/processes` | 모든 공정 | 모든 공정 | 지정한 공정만 | 빈 리스트 |
| `GET /api/programs` | 모든 프로그램 | 모든 프로그램 | 지정한 공정의 프로그램만 | 빈 리스트 |
| `GET /api/plcs` | 모든 PLC | 모든 PLC | 지정한 공정의 PLC만 | 빈 리스트 |
| `GET /api/masters` (드롭다운) | 모든 공정 | 모든 공정 | 지정한 공정만 | 빈 리스트 |
| 기준정보 관리 메뉴 | ✅ 접근 가능 | ❌ 접근 불가 | ❌ 접근 불가 | ❌ 접근 불가 |
| 사용자 관리 메뉴 | ✅ 접근 가능 | ❌ 접근 불가 | ❌ 접근 불가 | ❌ 접근 불가 |
| 공정 메뉴 | ✅ 접근 가능 | ✅ 접근 가능 | ✅ 접근 가능 | ❌ 접근 불가 |

---

## 5. 그룹 관리 화면에서 Role 선택

### 5.1 Role 목록 조회 API

**API 요청:**
```http
GET /api/roles
```

**API 응답:**
```json
{
  "roles": [
    {
      "role_id": "system_admin",
      "role_name": "시스템 관리자",
      "description": "기준정보 + 사용자관리 + 모든 공정 접근 가능",
      "display_order": 1
    },
    {
      "role_id": "integrated_admin",
      "role_name": "통합관리자",
      "description": "모든 공정 접근 가능",
      "display_order": 2
    },
    {
      "role_id": "process_manager",
      "role_name": "공정 관리자",
      "description": "지정한 공정만 접근 가능",
      "display_order": 3
    }
  ]
}
```

**SQL 쿼리:**
```sql
SELECT 
    ROLE_ID,
    ROLE_NAME,
    DESCRIPTION,
    DISPLAY_ORDER
FROM ROLE_MASTER
WHERE IS_ACTIVE = true
ORDER BY DISPLAY_ORDER ASC;
```

### 5.2 화면에서 Role 선택 시 동작

**시나리오: Role 선택에 따른 화면 변화**

#### 5.2.1 "시스템 관리자" Role 선택 시

```
1. 화면 상단 Role 선택
   ● 시스템 관리자  ← 선택
   ○ 통합관리자
   ○ 공정 관리자

2. 그룹 목록 영역
   ┌─────────────────────────────────┐
   │ 그룹명 | 공정 | 사용자 수 | 액션 │
   ├─────────────────────────────────┤
   │ 시스템 관리자 | 전체 | 1명 | [수정] [삭제] │
   └─────────────────────────────────┘

3. [그룹 추가] 버튼 클릭 시
   그룹명: [입력]
   공정 선택 영역: [비활성화/숨김]
     → 시스템 관리자는 모든 공정 접근 가능하므로 공정 선택 불필요
   설명: [입력]
   
   저장 시:
   - GROUP_PROCESSES 테이블에 데이터 추가 안 함
   - GROUPS 테이블에 ROLE_ID='system_admin'로 저장
```

#### 5.2.2 "통합관리자" Role 선택 시

```
1. 화면 상단 Role 선택
   ○ 시스템 관리자
   ● 통합관리자  ← 선택
   ○ 공정 관리자

2. 그룹 목록 영역
   ┌─────────────────────────────────┐
   │ 그룹명 | 공정 | 사용자 수 | 액션 │
   ├─────────────────────────────────┤
   │ 통합관리자 | 전체 | 1명 | [수정] [삭제] │
   └─────────────────────────────────┘

3. [그룹 추가] 버튼 클릭 시
   그룹명: [입력]
   공정 선택 영역: [비활성화/숨김]
     → 통합관리자는 모든 공정 접근 가능하므로 공정 선택 불필요
   설명: [입력]
   
   저장 시:
   - GROUP_PROCESSES 테이블에 데이터 추가 안 함
   - GROUPS 테이블에 ROLE_ID='integrated_admin'로 저장
```

#### 5.2.3 "공정 관리자" Role 선택 시

```
1. 화면 상단 Role 선택
   ○ 시스템 관리자
   ○ 통합관리자
   ● 공정 관리자  ← 선택

2. 그룹 목록 영역
   ┌─────────────────────────────────┐
   │ 그룹명 | 공정 | 사용자 수 | 액션 │
   ├─────────────────────────────────┤
   │ 모듈/화성 담당 | 모듈, 화성 | 1명 | [수정] [삭제] │
   │ 전극/조립 담당 | 전극, 조립 | 1명 | [수정] [삭제] │
   └─────────────────────────────────┘

3. [그룹 추가] 버튼 클릭 시
   그룹명: [입력]
   공정 선택 영역: [활성화]
     ☑ 모듈 (prc_module)
     ☑ 화성 (prc_hwaseong)
     ☐ 전극 (prc_electrode)
     ☐ 조립 (prc_assembly)
   설명: [입력]
   
   저장 시:
   - GROUPS 테이블에 ROLE_ID='process_manager'로 저장
   - GROUP_PROCESSES 테이블에 선택한 공정 추가
     → perm_001: group_process_manager_001 → prc_module
     → perm_002: group_process_manager_001 → prc_hwaseong
```

---

## 6. 실제 API 호출 예시

### 6.1 그룹 목록 조회 (Role별)

**요청 (공정 관리자 Role 선택 시):**
```http
GET /api/groups?role_id=process_manager
```

**응답:**
```json
{
  "role_id": "process_manager",
  "role_name": "공정 관리자",
  "groups": [
    {
      "group_id": "group_process_manager_001",
      "group_name": "모듈/화성 담당",
      "description": "모듈, 화성 공정 담당 그룹",
      "processes": [
        {"process_id": "prc_module", "process_name": "모듈"},
        {"process_id": "prc_hwaseong", "process_name": "화성"}
      ],
      "user_count": 1,
      "users": [
        {"user_id": "user_process_manager_001", "name": "박모듈"}
      ]
    },
    {
      "group_id": "group_process_manager_002",
      "group_name": "전극/조립 담당",
      "description": "전극, 조립 공정 담당 그룹",
      "processes": [
        {"process_id": "prc_electrode", "process_name": "전극"},
        {"process_id": "prc_assembly", "process_name": "조립"}
      ],
      "user_count": 1,
      "users": [
        {"user_id": "user_process_manager_002", "name": "최화성"}
      ]
    }
  ]
}
```

**요청 (시스템 관리자 Role 선택 시):**
```http
GET /api/groups?role_id=system_admin
```

**응답:**
```json
{
  "role_id": "system_admin",
  "role_name": "시스템 관리자",
  "groups": [
    {
      "group_id": "group_system_admin",
      "group_name": "시스템 관리자",
      "description": "시스템 관리자 그룹",
      "processes": [],
      "user_count": 1,
      "users": [
        {"user_id": "user_sys_admin", "name": "김관리"}
      ]
    }
  ]
}
```

### 6.2 공정 목록 조회 (권한 기반)

**요청 (공정 관리자):**
```http
GET /api/masters/processes?user_id=user_process_manager_001
```

**응답:**
```json
{
  "processes": [
    {"process_id": "prc_module", "process_name": "모듈"},
    {"process_id": "prc_hwaseong", "process_name": "화성"}
  ],
  "total": 2
}
```

**요청 (시스템 관리자):**
```http
GET /api/masters/processes?user_id=user_sys_admin
```

**응답:**
```json
{
  "processes": [
    {"process_id": "prc_module", "process_name": "모듈"},
    {"process_id": "prc_hwaseong", "process_name": "화성"},
    {"process_id": "prc_electrode", "process_name": "전극"},
    {"process_id": "prc_assembly", "process_name": "조립"}
  ],
  "total": 4
}
```

---

## 7. 핵심 포인트

1. **Role 정보는 ROLE_MASTER 테이블에서 관리**
   - 화면에 표시할 Role 목록은 `GET /api/roles`로 조회
   - Role 한글 이름, 설명 등은 ROLE_MASTER에서 가져옴

2. **그룹 생성 시 Role 선택에 따른 동작**
   - 시스템 관리자/통합관리자: 공정 선택 불필요 (모든 공정 접근)
   - 공정 관리자: 공정 선택 필수 (GROUP_PROCESSES에 저장)

3. **API 조회 시 권한별 필터링**
   - 시스템 관리자/통합관리자: 모든 데이터 반환
   - 공정 관리자: GROUP_PROCESSES에 지정된 공정의 데이터만 반환
   - 일반 사용자: 빈 리스트 반환

4. **테이블명 변경**
   - `PERMISSION_GROUPS` → `GROUPS`
   - `GROUP_PROCESS_PERMISSIONS` → `GROUP_PROCESSES`
   - `USER_GROUP_MAPPINGS` → `USER_GROUPS`

