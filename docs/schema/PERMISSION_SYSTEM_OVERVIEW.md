# 권한 관리 시스템 전체 구조 설명

## 1. 테이블 구조

### 1.1 테이블 목록 및 관계도

```
ROLE_MASTER (Role 마스터)
    ↑ (FK)
    │
GROUPS (그룹)
    ↑ (FK)              ↑ (FK)
    │                   │
USER_GROUPS         GROUP_PROCESSES
(사용자-그룹 매핑)    (그룹-공정 매핑)
    ↑                   ↑
    │                   │
USERS              PROCESS_MASTER
(사용자)            (공정 마스터)
```

### 1.2 테이블 상세 구조

#### 1.2.1 ROLE_MASTER (Role 마스터 테이블)

**목적:** Role 정보를 마스터로 관리 (시스템 관리자, 통합관리자, 공정 관리자)

**테이블명:** `ROLE_MASTER`

**주요 컬럼:**
- `ROLE_ID` (PK): system_admin, integrated_admin, process_manager
- `ROLE_NAME`: 시스템 관리자, 통합관리자, 공정 관리자
- `DESCRIPTION`: Role 설명
- `DISPLAY_ORDER`: 화면 표시 순서 (1, 2, 3)

**예시 데이터:**
| ROLE_ID | ROLE_NAME | DESCRIPTION | DISPLAY_ORDER |
|---------|-----------|-------------|---------------|
| system_admin | 시스템 관리자 | 기준정보 + 사용자관리 + 모든 공정 접근 가능 | 1 |
| integrated_admin | 통합관리자 | 모든 공정 접근 가능 | 2 |
| process_manager | 공정 관리자 | 지정한 공정만 접근 가능 | 3 |

**코드:**
```python
class RoleMaster(Base):
    __tablename__ = "ROLE_MASTER"
    
    role_id = Column("ROLE_ID", String(50), primary_key=True)
    role_name = Column("ROLE_NAME", String(100), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)
    display_order = Column("DISPLAY_ORDER", Integer, nullable=False, server_default="0")
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())
```

#### 1.2.2 GROUPS (그룹 테이블)

**목적:** 권한 그룹 정보 저장 (사용자가 화면에서 생성)

**테이블명:** `GROUPS` (기존: PERMISSION_GROUPS)

**주요 컬럼:**
- `GROUP_ID` (PK): 그룹 ID
- `GROUP_NAME`: 그룹명
- `ROLE_ID` (FK): ROLE_MASTER.ROLE_ID 참조
- `DESCRIPTION`: 그룹 설명
- `IS_ACTIVE`, `IS_DELETED`: 활성화/삭제 플래그

**예시 데이터:**
| GROUP_ID | GROUP_NAME | ROLE_ID | DESCRIPTION |
|----------|------------|---------|-------------|
| group_system_admin | 시스템 관리자 | system_admin | 시스템 관리자 그룹 |
| group_integrated_admin | 통합관리자 | integrated_admin | 통합관리자 그룹 |
| group_process_manager_001 | 모듈/화성 담당 | process_manager | 모듈, 화성 공정 담당 |

**코드:**
```python
class PermissionGroup(Base):
    __tablename__ = "GROUPS"
    
    group_id = Column("GROUP_ID", String(50), primary_key=True)
    group_name = Column("GROUP_NAME", String(100), nullable=False)
    role_id = Column(
        "ROLE_ID", 
        String(50), 
        ForeignKey("ROLE_MASTER.ROLE_ID"),  # FK
        nullable=False,
        index=True
    )
    description = Column("DESCRIPTION", Text, nullable=True)
```

**변경 사항:**
- 기존: `role` 컬럼 (String, 직접 값 저장)
- 변경: `role_id` 컬럼 (FK, ROLE_MASTER 참조)

#### 1.2.3 GROUP_PROCESSES (그룹별 공정 권한 테이블)

**목적:** 공정 관리자 그룹에 지정된 공정 저장

**테이블명:** `GROUP_PROCESSES` (기존: GROUP_PROCESS_PERMISSIONS)

**주요 컬럼:**
- `PERMISSION_ID` (PK): 권한 ID
- `GROUP_ID` (FK): GROUPS.GROUP_ID 참조
- `PROCESS_ID` (FK): PROCESS_MASTER.PROCESS_ID 참조
- `IS_ACTIVE`: 활성화 여부

**예시 데이터:**
| PERMISSION_ID | GROUP_ID | PROCESS_ID |
|---------------|----------|------------|
| perm_001 | group_process_manager_001 | prc_module |
| perm_002 | group_process_manager_001 | prc_hwaseong |
| perm_003 | group_process_manager_002 | prc_electrode |

**코드:**
```python
class GroupProcessPermission(Base):
    __tablename__ = "GROUP_PROCESSES"
    
    permission_id = Column("PERMISSION_ID", String(50), primary_key=True)
    group_id = Column(
        "GROUP_ID", 
        String(50), 
        ForeignKey("GROUPS.GROUP_ID"),  # FK (테이블명 변경)
        nullable=False,
        index=True
    )
    process_id = Column(
        "PROCESS_ID", 
        String(50), 
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=False,
        index=True
    )
```

**특징:**
- 시스템 관리자, 통합관리자 그룹은 이 테이블에 데이터 없음 (모든 공정 접근)
- 공정 관리자 그룹만 이 테이블에 공정 지정

#### 1.2.4 USER_GROUPS (사용자-그룹 매핑 테이블)

**목적:** 사용자와 그룹의 매핑 관계 저장

**테이블명:** `USER_GROUPS` (기존: USER_GROUP_MAPPINGS)

**주요 컬럼:**
- `MAPPING_ID` (PK): 매핑 ID
- `USER_ID` (FK): USERS.USER_ID 참조
- `GROUP_ID` (FK): GROUPS.GROUP_ID 참조
- `IS_ACTIVE`: 활성화 여부

**예시 데이터:**
| MAPPING_ID | USER_ID | GROUP_ID |
|------------|---------|----------|
| mapping_001 | user_sys_admin | group_system_admin |
| mapping_002 | user_integrated_admin | group_integrated_admin |
| mapping_003 | user_process_manager_001 | group_process_manager_001 |

**코드:**
```python
class UserGroupMapping(Base):
    __tablename__ = "USER_GROUPS"
    
    mapping_id = Column("MAPPING_ID", String(50), primary_key=True)
    user_id = Column(
        "USER_ID", 
        String(50), 
        ForeignKey("USERS.USER_ID"),
        nullable=False,
        index=True
    )
    group_id = Column(
        "GROUP_ID", 
        String(50), 
        ForeignKey("GROUPS.GROUP_ID"),  # FK (테이블명 변경)
        nullable=False,
        index=True
    )
```

**특징:**
- 사용자는 여러 그룹에 속할 수 있음 (1:N 관계)
- 일반 사용자는 이 테이블에 없음 (메뉴 접근 불가)

---

## 2. 테이블 간 관계 (Foreign Key)

### 2.1 Foreign Key 관계도

```
ROLE_MASTER
    │
    │ (1:N)
    ↓
GROUPS (ROLE_ID → ROLE_MASTER.ROLE_ID)
    │
    ├─ (1:N) → USER_GROUPS (GROUP_ID → GROUPS.GROUP_ID)
    │              │
    │              └─ (N:1) → USERS (USER_ID → USERS.USER_ID)
    │
    └─ (1:N) → GROUP_PROCESSES (GROUP_ID → GROUPS.GROUP_ID)
                   │
                   └─ (N:1) → PROCESS_MASTER (PROCESS_ID → PROCESS_MASTER.PROCESS_ID)
```

### 2.2 Foreign Key 제약조건

1. **GROUPS.ROLE_ID** → **ROLE_MASTER.ROLE_ID**
   - 그룹은 반드시 유효한 Role을 가져야 함
   - ROLE_MASTER에 없는 Role_ID는 사용 불가

2. **USER_GROUPS.GROUP_ID** → **GROUPS.GROUP_ID**
   - 사용자는 반드시 존재하는 그룹에만 속할 수 있음
   - 그룹 삭제 시 매핑도 함께 처리 필요

3. **GROUP_PROCESSES.GROUP_ID** → **GROUPS.GROUP_ID**
   - 공정 권한은 반드시 존재하는 그룹에만 연결 가능

4. **GROUP_PROCESSES.PROCESS_ID** → **PROCESS_MASTER.PROCESS_ID**
   - 공정 권한은 반드시 존재하는 공정에만 연결 가능

---

## 3. 코드 구조

### 3.1 모델 파일

**파일:** `ai_backend/src/database/models/permission_group_models.py`

**클래스:**
1. `RoleMaster`: ROLE_MASTER 테이블 모델
2. `PermissionGroup`: GROUPS 테이블 모델
3. `GroupProcessPermission`: GROUP_PROCESSES 테이블 모델
4. `UserGroupMapping`: USER_GROUPS 테이블 모델

### 3.2 권한 체크 로직

**파일:** `ai_backend/src/database/crud/program_crud.py`

**메서드:** `get_accessible_process_ids(user_id)`

**로직 흐름:**
```python
def get_accessible_process_ids(user_id: str) -> Optional[List[str]]:
    # 1. 사용자가 속한 활성 그룹 조회
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(UserGroupMapping.user_id == user_id)
        .filter(UserGroupMapping.is_active == True)
        .filter(PermissionGroup.is_active == True)
        .filter(PermissionGroup.is_deleted == False)
        .all()
    )
    
    # 2. 그룹이 없으면 접근 불가 (일반 사용자)
    if not groups:
        return []
    
    # 3. 시스템 관리자 또는 통합관리자: 모든 공정 접근 가능
    for group in groups:
        if group.role_id in ['system_admin', 'integrated_admin']:
            return None  # None = 모든 공정 접근 가능
    
    # 4. 공정 관리자: GROUP_PROCESSES에 지정된 공정만
    accessible_process_ids = set()
    for group in groups:
        if group.role_id == 'process_manager':
            process_permissions = (
                db.query(GroupProcessPermission)
                .filter(GroupProcessPermission.group_id == group.group_id)
                .filter(GroupProcessPermission.is_active == True)
                .all()
            )
            accessible_process_ids.update([pp.process_id for pp in process_permissions])
    
    return list(accessible_process_ids) if accessible_process_ids else []
```

---

## 4. 권한 체크 동작 방식

### 4.1 시스템 관리자 (system_admin)

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → user_sys_admin → group_system_admin

2. GROUPS 조회
   → group_system_admin.ROLE_ID = 'system_admin'

3. ROLE_MASTER 조회 (선택사항)
   → system_admin.ROLE_NAME = '시스템 관리자'

4. 권한 체크
   → role_id == 'system_admin' → 모든 공정 접근 가능
   → GROUP_PROCESSES 확인 불필요

5. 결과
   → None (모든 공정 접근 가능)
```

**접근 가능:**
- ✅ 기준정보 관리
- ✅ 사용자 관리
- ✅ 모든 공정 데이터

### 4.2 통합관리자 (integrated_admin)

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → user_integrated_admin → group_integrated_admin

2. GROUPS 조회
   → group_integrated_admin.ROLE_ID = 'integrated_admin'

3. 권한 체크
   → role_id == 'integrated_admin' → 모든 공정 접근 가능
   → GROUP_PROCESSES 확인 불필요

4. 결과
   → None (모든 공정 접근 가능)
```

**접근 가능:**
- ❌ 기준정보 관리
- ❌ 사용자 관리
- ✅ 모든 공정 데이터

### 4.3 공정 관리자 (process_manager)

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → user_process_manager_001 → group_process_manager_001

2. GROUPS 조회
   → group_process_manager_001.ROLE_ID = 'process_manager'

3. 권한 체크
   → role_id == 'process_manager' → GROUP_PROCESSES 확인 필요

4. GROUP_PROCESSES 조회
   → perm_001: group_process_manager_001 → prc_module
   → perm_002: group_process_manager_001 → prc_hwaseong

5. 결과
   → ['prc_module', 'prc_hwaseong']
```

**접근 가능:**
- ❌ 기준정보 관리
- ❌ 사용자 관리
- ✅ 지정한 공정 데이터만 (GROUP_PROCESSES에 저장된 공정)

### 4.4 일반 사용자 (그룹 없음)

**데이터 흐름:**
```
1. USER_GROUPS 조회
   → 조회 결과 없음 (테이블에 없음)

2. 권한 체크
   → 그룹 없음 → 접근 불가

3. 결과
   → [] (빈 리스트)
```

**접근 가능:**
- ❌ 모든 메뉴 접근 불가
- ✅ 채팅만 가능

### 4.5 여러 그룹에 속한 사용자 (권한 합집합)

**핵심 원칙:** 제일 넓은 권한이 적용됩니다.

**예시 1: 시스템 관리자 + 공정 관리자 그룹**
```
1. USER_GROUPS 조회
   → mapping_005: user_multi_001 → group_system_admin
   → mapping_006: user_multi_001 → group_process_manager_001

2. GROUPS 조회
   → group_system_admin.ROLE_ID = 'system_admin'
   → group_process_manager_001.ROLE_ID = 'process_manager'

3. 권한 체크
   → group_system_admin.role_id == 'system_admin' → 즉시 None 반환
   → 제일 넓은 권한인 "모든 공정 접근"이 적용됨

4. 결과
   → None (모든 공정 접근 가능)
```

**예시 2: 통합관리자 + 공정 관리자 그룹**
```
1. USER_GROUPS 조회
   → mapping_007: user_multi_002 → group_integrated_admin
   → mapping_008: user_multi_002 → group_process_manager_001

2. GROUPS 조회
   → group_integrated_admin.ROLE_ID = 'integrated_admin'
   → group_process_manager_001.ROLE_ID = 'process_manager'

3. 권한 체크
   → group_integrated_admin.role_id == 'integrated_admin' → 즉시 None 반환
   → 제일 넓은 권한인 "모든 공정 접근"이 적용됨

4. 결과
   → None (모든 공정 접근 가능)
```

**예시 3: 공정 관리자 그룹 2개 (공정 합집합)**
```
1. USER_GROUPS 조회
   → mapping_009: user_multi_003 → group_process_manager_001
   → mapping_010: user_multi_003 → group_process_manager_002

2. GROUPS 조회
   → group_process_manager_001.ROLE_ID = 'process_manager'
   → group_process_manager_002.ROLE_ID = 'process_manager'

3. 권한 체크
   → system_admin/integrated_admin 없음 → 공정 관리자 처리

4. GROUP_PROCESSES 조회
   → group_process_manager_001: prc_module, prc_hwaseong
   → group_process_manager_002: prc_electrode, prc_assembly

5. 공정 합집합
   → accessible_process_ids = {'prc_module', 'prc_hwaseong', 'prc_electrode', 'prc_assembly'}

6. 결과
   → ['prc_module', 'prc_hwaseong', 'prc_electrode', 'prc_assembly']
```

**권한 우선순위:**
1. **시스템 관리자** 또는 **통합관리자** (하나라도 있으면 → 모든 공정 접근)
2. **공정 관리자** (여러 그룹의 공정을 합집합)

---

## 5. 실제 데이터 예시로 보는 동작

### 5.1 테이블 데이터

**ROLE_MASTER:**
| ROLE_ID | ROLE_NAME | DISPLAY_ORDER |
|---------|-----------|---------------|
| system_admin | 시스템 관리자 | 1 |
| integrated_admin | 통합관리자 | 2 |
| process_manager | 공정 관리자 | 3 |

**GROUPS:**
| GROUP_ID | GROUP_NAME | ROLE_ID |
|----------|------------|---------|
| group_system_admin | 시스템 관리자 | system_admin |
| group_integrated_admin | 통합관리자 | integrated_admin |
| group_process_manager_001 | 모듈/화성 담당 | process_manager |

**GROUP_PROCESSES:**
| PERMISSION_ID | GROUP_ID | PROCESS_ID |
|---------------|----------|------------|
| perm_001 | group_process_manager_001 | prc_module |
| perm_002 | group_process_manager_001 | prc_hwaseong |

**USER_GROUPS:**
| MAPPING_ID | USER_ID | GROUP_ID |
|------------|---------|----------|
| mapping_001 | user_sys_admin | group_system_admin |
| mapping_003 | user_process_manager_001 | group_process_manager_001 |

### 5.2 API 호출 예시

#### 예시 1: 공정 목록 조회 (공정 관리자)

**요청:**
```http
GET /api/masters/processes?user_id=user_process_manager_001
```

**데이터베이스 쿼리:**
```sql
-- 1. 사용자 그룹 조회
SELECT ug.GROUP_ID
FROM USER_GROUPS ug
WHERE ug.USER_ID = 'user_process_manager_001'
    AND ug.IS_ACTIVE = true;
-- 결과: group_process_manager_001

-- 2. 그룹의 Role 확인
SELECT g.ROLE_ID
FROM GROUPS g
WHERE g.GROUP_ID = 'group_process_manager_001';
-- 결과: process_manager

-- 3. 공정 권한 조회
SELECT gp.PROCESS_ID
FROM GROUP_PROCESSES gp
WHERE gp.GROUP_ID = 'group_process_manager_001'
    AND gp.IS_ACTIVE = true;
-- 결과: prc_module, prc_hwaseong

-- 4. 공정 목록 조회
SELECT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
WHERE pm.PROCESS_ID IN ('prc_module', 'prc_hwaseong')
    AND pm.IS_ACTIVE = true;
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

#### 예시 2: 공정 목록 조회 (시스템 관리자)

**요청:**
```http
GET /api/masters/processes?user_id=user_sys_admin
```

**데이터베이스 쿼리:**
```sql
-- 1. 사용자 그룹 조회
SELECT ug.GROUP_ID
FROM USER_GROUPS ug
WHERE ug.USER_ID = 'user_sys_admin'
    AND ug.IS_ACTIVE = true;
-- 결과: group_system_admin

-- 2. 그룹의 Role 확인
SELECT g.ROLE_ID
FROM GROUPS g
WHERE g.GROUP_ID = 'group_system_admin';
-- 결과: system_admin

-- 3. 권한 체크
-- role_id == 'system_admin' → 모든 공정 접근 가능
-- GROUP_PROCESSES 확인 불필요

-- 4. 공정 목록 조회 (필터링 없음)
SELECT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
WHERE pm.IS_ACTIVE = true;
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

## 6. 주요 변경 사항 요약

### 6.1 테이블명 변경

| 기존 테이블명 | 변경된 테이블명 |
|--------------|---------------|
| PERMISSION_GROUPS | GROUPS |
| GROUP_PROCESS_PERMISSIONS | GROUP_PROCESSES |
| USER_GROUP_MAPPINGS | USER_GROUPS |

### 6.2 컬럼 변경

**GROUPS 테이블:**
- 기존: `ROLE` (String, 직접 값 저장)
- 변경: `ROLE_ID` (String, FK, ROLE_MASTER 참조)

### 6.3 신규 테이블

**ROLE_MASTER:**
- Role 정보를 마스터로 관리
- ROLE_ID, ROLE_NAME, DESCRIPTION, DISPLAY_ORDER

### 6.4 코드 변경

**program_crud.py:**
- `group.role` → `group.role_id`로 변경
- 테이블명 참조 업데이트 (GROUPS, GROUP_PROCESSES, USER_GROUPS)

---

## 7. 화면 동작 방식

### 7.1 그룹 관리 화면

**화면 구조:**
```
┌─────────────────────────────────────────┐
│ Role 선택 (라디오 버튼)                    │
│ ● 시스템 관리자  ○ 통합관리자  ○ 공정 관리자 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [선택된 Role]의 그룹 목록                  │
│ 그룹명 | 공정 | 사용자 수 | 액션           │
└─────────────────────────────────────────┘

[그룹 추가] 버튼
```

**동작:**
1. Role 선택 → 해당 Role의 그룹만 표시
2. 그룹 추가 → 현재 선택된 Role로 그룹 생성
3. 공정 관리자 Role 선택 시 → 공정 선택 영역 활성화
4. 시스템 관리자/통합관리자 Role 선택 시 → 공정 선택 영역 비활성화

### 7.2 API 호출

**Role 목록 조회:**
```http
GET /api/roles
→ ROLE_MASTER 테이블에서 조회
```

**그룹 목록 조회:**
```http
GET /api/groups?role_id=process_manager
→ GROUPS 테이블에서 role_id로 필터링
```

---

## 8. 핵심 포인트

1. **Role 정보는 ROLE_MASTER에서 관리**
   - 화면에 표시할 Role 목록은 ROLE_MASTER에서 조회
   - Role 한글 이름, 설명 등은 테이블에서 관리

2. **그룹은 ROLE_ID로 Role 참조**
   - GROUPS.ROLE_ID → ROLE_MASTER.ROLE_ID (FK)
   - Role 정보 변경 시 ROLE_MASTER만 수정하면 됨

3. **권한 체크는 ROLE_ID 기반**
   - 시스템 관리자/통합관리자: GROUP_PROCESSES 확인 불필요
   - 공정 관리자: GROUP_PROCESSES 확인 필요

4. **테이블명이 더 직관적**
   - GROUPS, GROUP_PROCESSES, USER_GROUPS

5. **일반 사용자는 그룹 없음**
   - USER_GROUPS 테이블에 없음
   - 모든 권한 체크에서 False 반환
   - 채팅만 가능

6. **여러 그룹에 속한 사용자: 제일 넓은 권한 적용**
   - 시스템 관리자 또는 통합관리자 그룹이 하나라도 있으면 → 모든 공정 접근 가능
   - 공정 관리자 그룹만 있는 경우 → 모든 그룹의 공정을 합집합으로 반환
   - 예: system_admin + process_manager → 모든 공정 접근 (system_admin 권한 우선)
   - 예: process_manager 그룹 2개 (A: prc_module, B: prc_electrode) → ['prc_module', 'prc_electrode']

7. **그룹 삭제 시 관련 데이터 자동 삭제**
   - 그룹 삭제 시 관련된 `USER_GROUPS` 실제 삭제 (사용자 매핑 삭제)
   - 관련된 `GROUP_PROCESSES` 실제 삭제 (공정 권한 삭제)
   - `GROUPS` 실제 삭제
   - 삭제 순서: USER_GROUPS → GROUP_PROCESSES → GROUPS (FK 제약조건)
   - 구현 파일: `ai_backend/src/database/crud/group_crud.py`

