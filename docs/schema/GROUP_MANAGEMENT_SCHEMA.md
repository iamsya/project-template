# 그룹 관리 테이블 스키마

## 개요

그룹 관리 기능을 위한 테이블 스키마입니다. 사용자가 화면에서 그룹을 생성하고, role과 공정을 선택하여 권한을 부여하며, 사용자를 그룹에 추가/삭제할 수 있습니다.

### 주요 특징

1. **Role 권한**: 시스템 관리자, 통합 관리자, 공정 관리자 중 단수 선택
2. **공정 권한**: 복수 선택 가능 (공정 관리자의 경우)
3. **사용자 매핑**: 그룹에 사용자 추가/삭제 가능
4. **그룹 수정**: role, 공정, 사용자 수정 가능
5. **그룹 삭제**: 소프트 삭제 지원
6. **일반 사용자**: 그룹에 속하지 않음 (메뉴 접근 불가, 채팅만 가능)

---

## 1. Role 마스터 테이블 (ROLE_MASTER)

### 테이블 구조

```sql
CREATE TABLE ROLE_MASTER (
    ROLE_ID VARCHAR(50) PRIMARY KEY,  -- system_admin, integrated_admin, process_manager
    ROLE_NAME VARCHAR(100) NOT NULL,   -- 시스템 관리자, 통합관리자, 공정 관리자
    DESCRIPTION TEXT,
    DISPLAY_ORDER INTEGER NOT NULL DEFAULT 0,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_role_master_active_order 
    ON ROLE_MASTER(IS_ACTIVE, DISPLAY_ORDER);
```

### Role 정보

| ROLE_ID | ROLE_NAME | DESCRIPTION | DISPLAY_ORDER |
|---------|-----------|-------------|---------------|
| system_admin | 시스템 관리자 | 기준정보 + 사용자관리 + 모든 공정 접근 가능 | 1 |
| integrated_admin | 통합관리자 | 모든 공정 접근 가능 | 2 |
| process_manager | 공정 관리자 | 지정한 공정만 접근 가능 | 3 |

### 필드 설명

| 필드명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| ROLE_ID | VARCHAR(50) | ❌ No | Role ID (PK) |
| ROLE_NAME | VARCHAR(100) | ❌ No | Role 한글 이름 |
| DESCRIPTION | TEXT | ✅ Yes | Role 설명 |
| DISPLAY_ORDER | INTEGER | ❌ No | 화면 표시 순서 |
| IS_ACTIVE | BOOLEAN | ❌ No | 활성화 여부 |
| CREATE_DT | TIMESTAMP | ❌ No | 생성 일시 |
| CREATE_USER | VARCHAR(50) | ❌ No | 생성자 |
| UPDATE_DT | TIMESTAMP | ✅ Yes | 수정 일시 |
| UPDATE_USER | VARCHAR(50) | ✅ Yes | 수정자 |

---

## 2. 그룹 테이블 (GROUPS)

### 테이블 구조

```sql
CREATE TABLE GROUPS (
    GROUP_ID VARCHAR(50) PRIMARY KEY,
    GROUP_NAME VARCHAR(100) NOT NULL,
    DESCRIPTION TEXT,
    ROLE_ID VARCHAR(50) NOT NULL REFERENCES ROLE_MASTER(ROLE_ID),  -- Role ID (FK)
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50),
    IS_DELETED BOOLEAN NOT NULL DEFAULT false,
    DELETED_AT TIMESTAMP,
    DELETED_BY VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_group_active_deleted 
    ON GROUPS(IS_ACTIVE, IS_DELETED);
CREATE INDEX idx_group_role 
    ON GROUPS(ROLE_ID);
```

### 일반 사용자

- 그룹에 속하지 않음 (`USER_GROUPS` 테이블에 없음)
- 메뉴 접근 불가
- 채팅방에서 채팅만 가능
- 권한설정 화면이나 테이블에 표시할 필요 없음

### 필드 설명

| 필드명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| GROUP_ID | VARCHAR(50) | ❌ No | 그룹 ID (PK) |
| GROUP_NAME | VARCHAR(100) | ❌ No | 그룹명 |
| DESCRIPTION | TEXT | ✅ Yes | 그룹 설명 |
| ROLE_ID | VARCHAR(50) | ❌ No | Role ID (FK) - ROLE_MASTER 참조 |
| IS_ACTIVE | BOOLEAN | ❌ No | 활성화 여부 |
| CREATE_DT | TIMESTAMP | ❌ No | 생성 일시 |
| CREATE_USER | VARCHAR(50) | ❌ No | 생성자 |
| UPDATE_DT | TIMESTAMP | ✅ Yes | 수정 일시 |
| UPDATE_USER | VARCHAR(50) | ✅ Yes | 수정자 |
| IS_DELETED | BOOLEAN | ❌ No | 삭제 여부 (소프트 삭제) |
| DELETED_AT | TIMESTAMP | ✅ Yes | 삭제 일시 |
| DELETED_BY | VARCHAR(50) | ✅ Yes | 삭제자 |

**참고:** 메뉴 접근 권한은 ROLE_ID로 판단합니다. ROLE_MASTER 테이블에서 Role 정보를 조회합니다.

---

## 3. 그룹별 공정 권한 테이블 (GROUP_PROCESSES)

### 테이블 구조

```sql
CREATE TABLE GROUP_PROCESSES (
    PERMISSION_ID VARCHAR(50) PRIMARY KEY,
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES GROUPS(GROUP_ID),
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE UNIQUE INDEX idx_group_process_unique 
    ON GROUP_PROCESSES(GROUP_ID, PROCESS_ID);
CREATE INDEX idx_group_process_group_active 
    ON GROUP_PROCESSES(GROUP_ID, IS_ACTIVE);
CREATE INDEX idx_group_process_process_active 
    ON GROUP_PROCESSES(PROCESS_ID, IS_ACTIVE);
```

### 필드 설명

| 필드명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| PERMISSION_ID | VARCHAR(50) | ❌ No | 권한 ID (PK) |
| GROUP_ID | VARCHAR(50) | ❌ No | 권한 그룹 ID (FK) |
| PROCESS_ID | VARCHAR(50) | ❌ No | 공정 ID (FK) |
| IS_ACTIVE | BOOLEAN | ❌ No | 활성화 여부 |
| CREATE_DT | TIMESTAMP | ❌ No | 생성 일시 |
| CREATE_USER | VARCHAR(50) | ❌ No | 생성자 |
| UPDATE_DT | TIMESTAMP | ✅ Yes | 수정 일시 |
| UPDATE_USER | VARCHAR(50) | ✅ Yes | 수정자 |

### 특징

- **공정 관리자**: 이 테이블에 선택한 공정들을 추가 (지정된 공정만 접근 가능)
- **통합관리자**: 이 테이블 확인 불필요 (모든 공정 접근 가능)
- **시스템 관리자**: 이 테이블 확인 불필요 (모든 공정 접근 가능)

---

## 4. 사용자-그룹 매핑 테이블 (USER_GROUPS)

### 테이블 구조

```sql
CREATE TABLE USER_GROUPS (
    MAPPING_ID VARCHAR(50) PRIMARY KEY,
    USER_ID VARCHAR(50) NOT NULL REFERENCES USERS(USER_ID),
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES GROUPS(GROUP_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE UNIQUE INDEX idx_user_group_unique 
    ON USER_GROUPS(USER_ID, GROUP_ID);
CREATE INDEX idx_user_group_user_active 
    ON USER_GROUPS(USER_ID, IS_ACTIVE);
CREATE INDEX idx_user_group_group_active 
    ON USER_GROUPS(GROUP_ID, IS_ACTIVE);
```

### 필드 설명

| 필드명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| MAPPING_ID | VARCHAR(50) | ❌ No | 매핑 ID (PK) |
| USER_ID | VARCHAR(50) | ❌ No | 사용자 ID (FK) |
| GROUP_ID | VARCHAR(50) | ❌ No | 권한 그룹 ID (FK) |
| IS_ACTIVE | BOOLEAN | ❌ No | 활성화 여부 |
| CREATE_DT | TIMESTAMP | ❌ No | 생성 일시 |
| CREATE_USER | VARCHAR(50) | ❌ No | 생성자 |
| UPDATE_DT | TIMESTAMP | ✅ Yes | 수정 일시 |
| UPDATE_USER | VARCHAR(50) | ✅ Yes | 수정자 |

### 특징

- 사용자는 여러 그룹에 속할 수 있음
- 사용자의 최종 권한은 속한 모든 그룹의 권한을 합집합
- 그룹에서 사용자 삭제 시 `IS_ACTIVE = false`로 설정 (소프트 삭제)

---

## 4. 권한 체크 로직

### 4.1 Role별 접근 가능한 공정 조회

#### 시스템 관리자 (system_admin)
- **모든 공정 접근 가능**
- `GROUP_PROCESSES` 테이블 확인 불필요
- 모든 공정에 대한 접근 권한 자동 부여

#### 통합 관리자 (integrated_admin)
- **모든 공정 접근 가능 (조회/편집)**
- `GROUP_PROCESSES` 테이블 확인 불필요
- 모든 공정에 대한 접근 권한 자동 부여

#### 공정 관리자 (process_manager)
- **그룹에서 지정한 특정 공정만 접근 가능 (조회/편집)**
- `GROUP_PROCESSES` 테이블에서 해당 그룹의 `PROCESS_ID` 목록만 접근 가능

#### 일반 사용자 (그룹 없음)
- **메뉴 접근 불가**
- 채팅방에서 채팅만 가능
- `USER_GROUPS` 테이블에 없음

### 4.2 사용자 관리 접근 권한 체크

```python
# 시스템 관리자만 사용자 관리 접근 가능
def can_access_user_management(user_id: str) -> bool:
    """
    사용자가 사용자 관리 기능에 접근할 수 있는지 확인
    
    Returns:
        bool: True면 사용자 관리 접근 가능
    """
    # 사용자가 속한 그룹 중 role이 'system_admin'인 그룹이 있는지 확인
    groups = get_user_groups(user_id)
    return any(group.role == PermissionGroup.ROLE_SYSTEM_ADMIN 
               for group in groups)
```

### 4.3 기준정보 관리 접근 권한 체크

```python
# 시스템 관리자만 기준정보 관리 접근 가능
def can_access_master_management(user_id: str) -> bool:
    """
    사용자가 기준정보 관리 기능에 접근할 수 있는지 확인
    
    Returns:
        bool: True면 기준정보 관리 접근 가능
    """
    groups = get_user_groups(user_id)
    return any(group.role == PermissionGroup.ROLE_SYSTEM_ADMIN 
               for group in groups)
```

### 4.4 공정 접근 권한 체크

```python
def can_access_process(user_id: str, process_id: str) -> bool:
    """
    사용자가 특정 공정에 접근할 수 있는지 확인
    
    Args:
        user_id: 사용자 ID
        process_id: 공정 ID
        
    Returns:
        bool: True면 해당 공정 접근 가능
    """
    groups = get_user_groups(user_id)
    
    for group in groups:
        # 시스템 관리자: 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_SYSTEM_ADMIN:
            return True
        
        # 통합 관리자: 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            return True
        
        # 공정 관리자: GROUP_PROCESS_PERMISSIONS에 해당 공정이 있으면 접근 가능
        if group.role == PermissionGroup.ROLE_PROCESS_MANAGER:
            process_permissions = get_group_process_permissions(group.group_id)
            if any(pp.process_id == process_id for pp in process_permissions):
                return True
    
    return False
```

### 4.5 사용자가 접근 가능한 공정 목록 조회

```python
def get_accessible_processes(user_id: str) -> List[str]:
    """
    사용자가 접근 가능한 공정 ID 목록 조회
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        List[str]: 접근 가능한 공정 ID 목록
    """
    groups = get_user_groups(user_id)
    accessible_processes = set()
    
    for group in groups:
        # 시스템 관리자: 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_SYSTEM_ADMIN:
            all_processes = get_all_active_processes()
            accessible_processes.update([p.process_id for p in all_processes])
            continue
        
        # 통합 관리자: 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            all_processes = get_all_active_processes()
            accessible_processes.update([p.process_id for p in all_processes])
            continue
        
        # 공정 관리자: GROUP_PROCESS_PERMISSIONS에 있는 공정만 접근 가능
        if group.role == PermissionGroup.ROLE_PROCESS_MANAGER:
            process_permissions = get_group_process_permissions(group.group_id)
            accessible_processes.update([pp.process_id for pp in process_permissions])
    
    return list(accessible_processes)
```

---

## 5. SQL 쿼리 예시

### 5.1 그룹 목록 조회 (사용자 수 포함)

```sql
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE_ID,
    pg.DESCRIPTION,
    COUNT(DISTINCT ugm.USER_ID) AS user_count,
    pg.CREATE_DT,
    pg.CREATE_USER
FROM GROUPS pg
LEFT JOIN USER_GROUP_MAPPINGS ugm 
    ON pg.GROUP_ID = ugm.GROUP_ID 
    AND ugm.IS_ACTIVE = true
WHERE pg.IS_DELETED = false
    AND pg.IS_ACTIVE = true
GROUP BY pg.GROUP_ID, pg.GROUP_NAME, pg.ROLE_ID, pg.DESCRIPTION, pg.CREATE_DT, pg.CREATE_USER
ORDER BY pg.CREATE_DT DESC;
```

### 5.2 그룹 상세 조회 (공정 목록 포함)

```sql
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE_ID,
    pg.DESCRIPTION,
    pm.PROCESS_ID,
    pm.PROCESS_NAME
FROM GROUPS pg
LEFT JOIN GROUP_PROCESS_PERMISSIONS gpp 
    ON pg.GROUP_ID = gpp.GROUP_ID 
    AND gpp.IS_ACTIVE = true
LEFT JOIN PROCESS_MASTER pm 
    ON gpp.PROCESS_ID = pm.PROCESS_ID 
    AND pm.IS_ACTIVE = true
WHERE pg.GROUP_ID = 'group_001'
    AND pg.IS_DELETED = false
    AND pg.IS_ACTIVE = true;
```

### 5.3 그룹 사용자 목록 조회

```sql
SELECT 
    u.USER_ID,
    u.EMPLOYEE_ID,
    u.NAME,
    u.SITE_LIST,
    ugm.CREATE_DT AS joined_dt
FROM USER_GROUPS ugm
INNER JOIN USERS u 
    ON ugm.USER_ID = u.USER_ID
WHERE ugm.GROUP_ID = 'group_001'
    AND ugm.IS_ACTIVE = true
    AND u.IS_DELETED = false
    AND u.IS_ACTIVE = true
ORDER BY ugm.CREATE_DT DESC;
```

### 5.4 사용자의 Role 확인

```sql
SELECT DISTINCT pg.ROLE
FROM USER_GROUPS ugm
INNER JOIN PERMISSION_GROUPS pg 
    ON ugm.GROUP_ID = pg.GROUP_ID
WHERE ugm.USER_ID = 'user_001'
    AND ugm.IS_ACTIVE = true
    AND pg.IS_ACTIVE = true
    AND pg.IS_DELETED = false;
```

---

## 6. 권한 체크 흐름도

### 6.1 사용자 관리 접근 권한 체크

```
사용자 요청 (사용자 관리 기능)
    ↓
사용자가 속한 그룹 조회
    ↓
그룹의 role 확인
    ↓
role == 'system_admin'?
    ├─ Yes → 접근 허용
    └─ No → 접근 거부 (403 Forbidden)
```

### 6.2 기준정보 관리 접근 권한 체크

```
사용자 요청 (기준정보 관리 기능)
    ↓
사용자가 속한 그룹 조회
    ↓
그룹의 role 확인
    ↓
role == 'system_admin'?
    ├─ Yes → 접근 허용
    └─ No → 접근 거부 (403 Forbidden)
```

### 6.3 공정 접근 권한 체크

```
사용자 요청 (특정 공정의 데이터 조회)
    ↓
사용자가 속한 그룹 조회
    ↓
각 그룹의 role 확인
    ↓
┌─────────────────────────────────────┐
│ role == 'system_admin'?             │
│   ├─ Yes → 접근 허용 (모든 공정)     │
│   └─ No → 다음 확인                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ role == 'integrated_admin'?         │
│   ├─ Yes → 접근 허용 (모든 공정)     │
│   └─ No → 다음 확인                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ role == 'process_manager'?           │
│   ├─ Yes → GROUP_PROCESSES│
│   │        에 해당 공정이 있는지 확인│
│   │   ├─ 있음 → 접근 허용            │
│   │   └─ 없음 → 접근 거부            │
│   └─ No → 접근 거부                  │
└─────────────────────────────────────┘
```

---

## 7. 구현 시 주의사항

### 7.1 Foreign Key 제약조건

- `USER_GROUPS.USER_ID` → `USERS.USER_ID` (같은 Base 사용)
- `USER_GROUPS.GROUP_ID` → `GROUPS.GROUP_ID` (같은 Base 사용)
- `GROUP_PROCESSES.GROUP_ID` → `GROUPS.GROUP_ID` (같은 Base 사용)
- `GROUP_PROCESSES.PROCESS_ID` → `PROCESS_MASTER.PROCESS_ID` (같은 Base 사용)
- `GROUPS.ROLE_ID` → `ROLE_MASTER.ROLE_ID` (같은 Base 사용)

모든 테이블이 `ai_backend`의 `Base`를 사용하므로 Foreign Key 제약조건이 정상 작동합니다.

### 7.2 그룹 삭제 시 처리

**구현 파일:** `ai_backend/src/database/crud/group_crud.py`

**처리 로직:**
1. 관련된 `USER_GROUPS` 삭제 (FK 제약조건 때문에 먼저 삭제)
2. 관련된 `GROUP_PROCESSES` 삭제 (FK 제약조건 때문에 먼저 삭제)
3. `GROUPS` 삭제

**코드 예시:**
```python
def delete_group(self, group_id: str, deleted_by: str) -> bool:
    # 1. 그룹 조회
    group = db.query(PermissionGroup).filter(
        PermissionGroup.group_id == group_id
    ).first()
    
    # 2. 관련된 USER_GROUPS 삭제 (FK 제약조건 때문에 먼저 삭제)
    user_mappings = (
        db.query(UserGroupMapping)
        .filter(UserGroupMapping.group_id == group_id)
        .all()
    )
    for mapping in user_mappings:
        db.delete(mapping)
    
    # 3. 관련된 GROUP_PROCESSES 삭제 (FK 제약조건 때문에 먼저 삭제)
    process_permissions = (
        db.query(GroupProcessPermission)
        .filter(GroupProcessPermission.group_id == group_id)
        .all()
    )
    for permission in process_permissions:
        db.delete(permission)
    
    # 4. 그룹 삭제
    db.delete(group)
```

**주의사항:**
- Foreign Key 제약조건으로 인해 그룹 삭제 전에 관련 데이터를 먼저 삭제해야 함
- 실제 삭제(하드 삭제)이므로 데이터가 완전히 제거됨
- 삭제 순서: USER_GROUPS → GROUP_PROCESSES → GROUPS

### 7.3 사용자 그룹에서 삭제 시 처리

- `USER_GROUPS`의 `IS_ACTIVE = false`로 설정 (소프트 삭제)
- 실제 레코드는 삭제하지 않음 (이력 관리)

---

## 8. 예시 데이터

### 8.1 Role 마스터 데이터 초기화

```sql
-- Role 마스터 데이터 삽입
INSERT INTO ROLE_MASTER 
    (ROLE_ID, ROLE_NAME, DESCRIPTION, DISPLAY_ORDER, CREATE_USER)
VALUES 
    (
        'system_admin',
        '시스템 관리자',
        '기준정보 + 사용자관리 + 모든 공정 접근 가능',
        1,
        'admin'
    ),
    (
        'integrated_admin',
        '통합관리자',
        '모든 공정 접근 가능',
        2,
        'admin'
    ),
    (
        'process_manager',
        '공정 관리자',
        '지정한 공정만 접근 가능',
        3,
        'admin'
    );
```

### 8.2 시스템 관리자 그룹 생성

```sql
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_system_admin',
        '시스템 관리자',
        'system_admin',
        '시스템 관리자 그룹 - 사용자 관리 및 모든 공정 접근 가능',
        'admin'
    );
```

### 8.3 통합관리자 그룹 생성

```sql
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_integrated_admin',
        '통합관리자',
        'integrated_admin',
        '통합관리자 그룹 - 모든 공정 접근 가능',
        'admin'
    );
```

### 8.4 공정 관리자 그룹 생성

```sql
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_process_manager_001',
        '모듈 공정 담당자',
        'process_manager',
        '모듈 공정 관리자 그룹',
        'admin'
    );

-- 특정 공정에 대한 권한 추가
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_001', 'group_process_manager_001', 'prc_module', 'admin');
```

### 8.5 사용자를 그룹에 추가

```sql
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_001', 'user_001', 'group_system_admin', 'admin');
```

---

## 8.5 전체 예시 데이터 시나리오

다음은 실제 사용 시나리오를 반영한 완전한 예시 데이터입니다.

### 8.5.1 사용자 데이터 (USERS 테이블)

```sql
-- 사용자 1: 시스템 관리자
INSERT INTO USERS (USER_ID, EMPLOYEE_ID, NAME, IS_ACTIVE, IS_DELETED)
VALUES ('user_sys_admin', 'SO10001', '김관리', true, false);

-- 사용자 2: 통합 관리자
INSERT INTO USERS (USER_ID, EMPLOYEE_ID, NAME, IS_ACTIVE, IS_DELETED)
VALUES ('user_integrated_admin', 'SO10002', '이통합', true, false);

-- 사용자 3: 공정 관리자 (모듈 공정)
INSERT INTO USERS (USER_ID, EMPLOYEE_ID, NAME, IS_ACTIVE, IS_DELETED)
VALUES ('user_process_manager_001', 'SO10003', '박모듈', true, false);

-- 사용자 4: 공정 관리자 (화성 공정)
INSERT INTO USERS (USER_ID, EMPLOYEE_ID, NAME, IS_ACTIVE, IS_DELETED)
VALUES ('user_process_manager_002', 'SO10004', '최화성', true, false);

-- 사용자 5: 공정 관리자 (전극, 조립 공정)
INSERT INTO USERS (USER_ID, EMPLOYEE_ID, NAME, IS_ACTIVE, IS_DELETED)
VALUES ('user_process_manager_003', 'SO10005', '정전극', true, false);
```

### 8.5.2 공정 데이터 (PROCESS_MASTER 테이블)

```sql
-- 공정 마스터 데이터 (예시)
INSERT INTO PROCESS_MASTER (PROCESS_ID, PROCESS_NAME, IS_ACTIVE, CREATE_USER)
VALUES 
    ('prc_module', '모듈', true, 'admin'),
    ('prc_hwaseong', '화성', true, 'admin'),
    ('prc_automation_logistics', '자동화 물류', true, 'admin'),
    ('prc_electrode', '전극', true, 'admin'),
    ('prc_assembly', '조립', true, 'admin');
```

### 8.5.3 권한 그룹 데이터 (PERMISSION_GROUPS 테이블)

```sql
-- 1. 시스템 관리자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_system_admin',
        '시스템 관리자',
        'system_admin',
        '시스템 관리자 그룹 - 사용자 관리 및 모든 공정 접근 가능',
        'admin'
    );

-- 2. 통합 관리자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_integrated_admin',
        '통합 관리자',
        'integrated_admin',
        '통합 관리자 그룹 - PLC 모든 공정 접근 가능',
        'admin'
    );

-- 3. 모듈 공정 담당자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_module_manager',
        '모듈 공정 담당자',
        'process_manager',
        '모듈 공정 관리자 그룹',
        'admin'
    );

-- 4. 화성 공정 담당자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_hwaseong_manager',
        '화성 공정 담당자',
        'process_manager',
        '화성 공정 관리자 그룹',
        'admin'
    );

-- 5. 전극 및 조립 공정 담당자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_electrode_assembly_manager',
        '전극 및 조립 공정 담당자',
        'process_manager',
        '전극, 조립 공정 관리자 그룹',
        'admin'
    );
```

### 8.5.4 그룹별 공정 권한 데이터 (GROUP_PROCESS_PERMISSIONS 테이블)

```sql
-- 통합 관리자: 모든 공정 접근 가능 (모든 공정 추가)
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_integrated_module', 'grp_integrated_admin', 'prc_module', 'admin'),
    ('perm_integrated_hwaseong', 'grp_integrated_admin', 'prc_hwaseong', 'admin'),
    ('perm_integrated_automation', 'grp_integrated_admin', 'prc_automation_logistics', 'admin'),
    ('perm_integrated_electrode', 'grp_integrated_admin', 'prc_electrode', 'admin'),
    ('perm_integrated_assembly', 'grp_integrated_admin', 'prc_assembly', 'admin');

-- 모듈 공정 담당자: 모듈 공정만 접근 가능
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_module_module', 'grp_module_manager', 'prc_module', 'admin');

-- 화성 공정 담당자: 화성 공정만 접근 가능
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_hwaseong_hwaseong', 'grp_hwaseong_manager', 'prc_hwaseong', 'admin');

-- 전극 및 조립 공정 담당자: 전극, 조립 공정 접근 가능
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_electrode_electrode', 'grp_electrode_assembly_manager', 'prc_electrode', 'admin'),
    ('perm_electrode_assembly', 'grp_electrode_assembly_manager', 'prc_assembly', 'admin');

-- 시스템 관리자는 GROUP_PROCESS_PERMISSIONS에 데이터가 없어도 모든 공정 접근 가능
```

### 8.5.5 사용자-그룹 매핑 데이터 (USER_GROUP_MAPPINGS 테이블)

```sql
-- 사용자 1 (김관리) → 시스템 관리자 그룹
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_001', 'user_sys_admin', 'grp_system_admin', 'admin');

-- 사용자 2 (이통합) → 통합 관리자 그룹
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_002', 'user_integrated_admin', 'grp_integrated_admin', 'admin');

-- 사용자 3 (박모듈) → 모듈 공정 담당자 그룹
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_003', 'user_process_manager_001', 'grp_module_manager', 'admin');

-- 사용자 4 (최화성) → 화성 공정 담당자 그룹
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_004', 'user_process_manager_002', 'grp_hwaseong_manager', 'admin');

-- 사용자 5 (정전극) → 전극 및 조립 공정 담당자 그룹
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_005', 'user_process_manager_003', 'grp_electrode_assembly_manager', 'admin');
```

### 8.5.6 예시 데이터 조회 결과

#### 그룹 목록 조회 (사용자 수 포함)

```sql
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE_ID,
    COUNT(DISTINCT ugm.USER_ID) AS user_count,
    pg.CREATE_DT
FROM GROUPS pg
LEFT JOIN USER_GROUP_MAPPINGS ugm 
    ON pg.GROUP_ID = ugm.GROUP_ID 
    AND ugm.IS_ACTIVE = true
WHERE pg.IS_DELETED = false
    AND pg.IS_ACTIVE = true
GROUP BY pg.GROUP_ID, pg.GROUP_NAME, pg.ROLE, pg.CREATE_DT
ORDER BY pg.CREATE_DT DESC;
```

**결과:**
| GROUP_ID | GROUP_NAME | ROLE | USER_COUNT | CREATE_DT |
|----------|------------|------|------------|-----------|
| grp_system_admin | 시스템 관리자 | system_admin | 1 | 2023-11-03 |
| grp_integrated_admin | 통합 관리자 | integrated_admin | 1 | 2023-11-04 |
| grp_module_manager | 모듈 공정 담당자 | process_manager | 1 | 2023-11-05 |
| grp_hwaseong_manager | 화성 공정 담당자 | process_manager | 1 | 2023-11-06 |
| grp_electrode_assembly_manager | 전극 및 조립 공정 담당자 | process_manager | 1 | 2023-11-05 |

#### 그룹 상세 조회 (공정 목록 포함)

```sql
-- 그룹 ID: grp_electrode_assembly_manager
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE_ID,
    pm.PROCESS_ID,
    pm.PROCESS_NAME
FROM GROUPS pg
LEFT JOIN GROUP_PROCESS_PERMISSIONS gpp 
    ON pg.GROUP_ID = gpp.GROUP_ID 
    AND gpp.IS_ACTIVE = true
LEFT JOIN PROCESS_MASTER pm 
    ON gpp.PROCESS_ID = pm.PROCESS_ID 
    AND pm.IS_ACTIVE = true
WHERE pg.GROUP_ID = 'grp_electrode_assembly_manager'
    AND pg.IS_DELETED = false
    AND pg.IS_ACTIVE = true;
```

**결과:**
| GROUP_ID | GROUP_NAME | ROLE | PROCESS_ID | PROCESS_NAME |
|----------|------------|------|------------|--------------|
| grp_electrode_assembly_manager | 전극 및 조립 공정 담당자 | process_manager | prc_electrode | 전극 |
| grp_electrode_assembly_manager | 전극 및 조립 공정 담당자 | process_manager | prc_assembly | 조립 |

#### 그룹 사용자 목록 조회

```sql
-- 그룹 ID: grp_module_manager
SELECT 
    u.USER_ID,
    u.EMPLOYEE_ID,
    u.NAME,
    ugm.CREATE_DT AS joined_dt
FROM USER_GROUPS ugm
INNER JOIN USERS u 
    ON ugm.USER_ID = u.USER_ID
WHERE ugm.GROUP_ID = 'grp_module_manager'
    AND ugm.IS_ACTIVE = true
    AND u.IS_DELETED = false
    AND u.IS_ACTIVE = true;
```

**결과:**
| USER_ID | EMPLOYEE_ID | NAME | JOINED_DT |
|---------|-------------|------|-----------|
| user_process_manager_001 | SO10003 | 박모듈 | 2023-11-05 10:00:00 |

#### 사용자의 접근 가능한 공정 조회

```sql
-- 사용자 ID: user_process_manager_003 (정전극)
-- 이 사용자는 전극 및 조립 공정 담당자 그룹에 속함

SELECT DISTINCT pm.PROCESS_ID, pm.PROCESS_NAME
FROM USER_GROUPS ugm
INNER JOIN PERMISSION_GROUPS pg 
    ON ugm.GROUP_ID = pg.GROUP_ID
LEFT JOIN GROUP_PROCESS_PERMISSIONS gpp 
    ON pg.GROUP_ID = gpp.GROUP_ID 
    AND gpp.IS_ACTIVE = true
LEFT JOIN PROCESS_MASTER pm 
    ON gpp.PROCESS_ID = pm.PROCESS_ID 
    AND pm.IS_ACTIVE = true
WHERE ugm.USER_ID = 'user_process_manager_003'
    AND ugm.IS_ACTIVE = true
    AND pg.IS_ACTIVE = true
    AND pg.IS_DELETED = false
    AND (
        -- 시스템 관리자: 모든 공정 접근 가능 (GROUP_PROCESS_PERMISSIONS 확인 불필요)
        pg.ROLE = 'system_admin'
        OR
        -- 통합 관리자: GROUP_PROCESS_PERMISSIONS에 모든 공정이 있거나 비어있으면 모든 공정
        (pg.ROLE = 'integrated_admin' AND gpp.PROCESS_ID IS NOT NULL)
        OR
        -- 공정 관리자: GROUP_PROCESS_PERMISSIONS에 있는 공정만
        (pg.ROLE = 'process_manager' AND gpp.PROCESS_ID IS NOT NULL)
    );
```

**결과:**
| PROCESS_ID | PROCESS_NAME |
|------------|--------------|
| prc_electrode | 전극 |
| prc_assembly | 조립 |

---

## 9. REST API에서 권한 체크 구현 예시

### 9.1 사용자 관리 API - 시스템 관리자만 접근 가능

```python
# ai_backend/src/api/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models.permission_group_models import PermissionGroup
from src.database.models.user_models import User
from src.database.crud.user_crud import UserCRUD

router = APIRouter(tags=["user-management"])


def check_user_management_permission(user_id: str, db: Session) -> bool:
    """
    사용자 관리 접근 권한 확인
    시스템 관리자(role='system_admin')만 접근 가능
    """
    from sqlalchemy import and_
    
    # 사용자가 속한 활성 그룹 조회
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(
            and_(
                UserGroupMapping.user_id == user_id,
                UserGroupMapping.is_active == True,
                PermissionGroup.is_active == True,
                PermissionGroup.is_deleted == False
            )
        )
        .all()
    )
    
    # 시스템 관리자 role이 있는지 확인
    return any(group.role == PermissionGroup.ROLE_SYSTEM_ADMIN for group in groups)


@router.get("/users", summary="사용자 목록 조회")
def get_users(
    user_id: str = Query(..., description="사용자 ID (권한 검증용)", example="user_sys_admin"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    사용자 목록 조회 API
    
    **권한 요구사항:**
    - 시스템 관리자(role='system_admin')만 접근 가능
    """
    # 권한 체크
    if not check_user_management_permission(user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 관리 기능에 접근할 권한이 없습니다. 시스템 관리자만 접근 가능합니다."
        )
    
    # 사용자 목록 조회
    user_crud = UserCRUD(db)
    users = user_crud.get_all_users(page=page, page_size=page_size)
    
    return {
        "status": "success",
        "data": users,
        "page": page,
        "page_size": page_size
    }


@router.post("/users", summary="사용자 생성")
def create_user(
    employee_id: str,
    name: str,
    user_id: str = Query(..., description="요청한 사용자 ID (권한 검증용)", example="user_sys_admin"),
    db: Session = Depends(get_db),
):
    """
    사용자 생성 API
    
    **권한 요구사항:**
    - 시스템 관리자(role='system_admin')만 접근 가능
    """
    # 권한 체크
    if not check_user_management_permission(user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자 생성 권한이 없습니다. 시스템 관리자만 접근 가능합니다."
        )
    
    # 사용자 생성
    user_crud = UserCRUD(db)
    new_user = user_crud.create_user(
        user_id=f"user_{employee_id}",
        employee_id=employee_id,
        name=name
    )
    
    return {
        "status": "success",
        "message": "사용자가 생성되었습니다.",
        "data": {
            "user_id": new_user.user_id,
            "employee_id": new_user.employee_id,
            "name": new_user.name
        }
    }
```

### 9.2 기준정보 관리 API - 시스템 관리자만 접근 가능

```python
# ai_backend/src/api/routers/master_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models.permission_group_models import PermissionGroup
from src.database.models.master_models import ProcessMaster

router = APIRouter(tags=["master-management"])


def check_master_management_permission(user_id: str, db: Session) -> bool:
    """
    기준정보 관리 접근 권한 확인
    시스템 관리자(role='system_admin')만 접근 가능
    """
    from sqlalchemy import and_
    from src.database.models.permission_group_models import UserGroupMapping
    
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(
            and_(
                UserGroupMapping.user_id == user_id,
                UserGroupMapping.is_active == True,
                PermissionGroup.is_active == True,
                PermissionGroup.is_deleted == False
            )
        )
        .all()
    )
    
    return any(group.role == PermissionGroup.ROLE_SYSTEM_ADMIN for group in groups)


@router.post("/processes", summary="공정 생성")
def create_process(
    process_id: str,
    process_name: str,
    user_id: str = Query(..., description="요청한 사용자 ID (권한 검증용)", example="user_sys_admin"),
    db: Session = Depends(get_db),
):
    """
    공정 생성 API
    
    **권한 요구사항:**
    - 시스템 관리자(role='system_admin')만 접근 가능
    """
    # 권한 체크
    if not check_master_management_permission(user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="기준정보 관리 권한이 없습니다. 시스템 관리자만 접근 가능합니다."
        )
    
    # 공정 생성 로직
    new_process = ProcessMaster(
        process_id=process_id,
        process_name=process_name,
        is_active=True,
        create_user=user_id
    )
    db.add(new_process)
    db.commit()
    
    return {
        "status": "success",
        "message": "공정이 생성되었습니다.",
        "data": {
            "process_id": new_process.process_id,
            "process_name": new_process.process_name
        }
    }
```

### 9.3 프로그램 목록 조회 API - 공정 접근 권한 체크

```python
# ai_backend/src/api/routers/program_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from src.database.base import get_db
from src.database.models.permission_group_models import (
    PermissionGroup,
    UserGroupMapping,
    GroupProcessPermission
)
from src.database.models.program_models import Program

router = APIRouter(tags=["program-management"])


def get_user_accessible_processes(user_id: str, db: Session) -> list:
    """
    사용자가 접근 가능한 공정 ID 목록 조회
    
    Returns:
        list: 접근 가능한 공정 ID 목록 (빈 리스트면 모든 공정 접근 가능)
    """
    # 사용자가 속한 활성 그룹 조회
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(
            and_(
                UserGroupMapping.user_id == user_id,
                UserGroupMapping.is_active == True,
                PermissionGroup.is_active == True,
                PermissionGroup.is_deleted == False
            )
        )
        .all()
    )
    
    accessible_processes = set()
    has_system_admin = False
    has_integrated_admin = False
    
    for group in groups:
        # 시스템 관리자: 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_SYSTEM_ADMIN:
            has_system_admin = True
            # 모든 활성 공정 조회
            all_processes = db.query(ProcessMaster).filter(
                ProcessMaster.is_active == True
            ).all()
            accessible_processes.update([p.process_id for p in all_processes])
            continue
        
        # 통합 관리자: PLC 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            has_integrated_admin = True
            # GROUP_PROCESS_PERMISSIONS 확인
            process_permissions = (
                db.query(GroupProcessPermission)
                .filter(
                    and_(
                        GroupProcessPermission.group_id == group.group_id,
                        GroupProcessPermission.is_active == True
                    )
                )
                .all()
            )
            if not process_permissions:  # 비어있으면 모든 공정 접근 가능
                all_processes = db.query(ProcessMaster).filter(
                    ProcessMaster.is_active == True
                ).all()
                accessible_processes.update([p.process_id for p in all_processes])
            else:
                accessible_processes.update([pp.process_id for pp in process_permissions])
            continue
        
        # 공정 관리자: GROUP_PROCESS_PERMISSIONS에 있는 공정만 접근 가능
        if group.role == PermissionGroup.ROLE_PROCESS_MANAGER:
            process_permissions = (
                db.query(GroupProcessPermission)
                .filter(
                    and_(
                        GroupProcessPermission.group_id == group.group_id,
                        GroupProcessPermission.is_active == True
                    )
                )
                .all()
            )
            accessible_processes.update([pp.process_id for pp in process_permissions])
    
    # 시스템 관리자나 통합 관리자가 있으면 빈 리스트 반환 (모든 공정 접근 가능)
    if has_system_admin or (has_integrated_admin and not accessible_processes):
        return []
    
    return list(accessible_processes)


@router.get("/programs", summary="프로그램 목록 조회")
def get_program_list(
    user_id: Optional[str] = Query(None, description="사용자 ID (권한 기반 필터링용)", example="user_process_manager_003"),
    process_id: Optional[str] = Query(None, description="공정 ID로 필터링", example="prc_electrode"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    프로그램 목록 조회 API
    
    **권한 기반 필터링:**
    - user_id가 제공된 경우: 사용자의 권한 그룹에 따라 접근 가능한 공정의 프로그램만 조회
      - 시스템 관리자: 모든 공정의 프로그램 조회 가능
      - 통합 관리자: PLC 모든 공정의 프로그램 조회 가능
      - 공정 관리자: 지정된 공정의 프로그램만 조회 가능
    - user_id가 없는 경우: 모든 프로그램 조회 (권한 필터링 없음)
    """
    query = db.query(Program).filter(Program.is_deleted == False)
    
    # 권한 기반 필터링
    if user_id:
        accessible_processes = get_user_accessible_processes(user_id, db)
        
        if accessible_processes:  # 빈 리스트가 아니면 특정 공정만 필터링
            query = query.filter(Program.process_id.in_(accessible_processes))
        # 빈 리스트면 모든 공정 접근 가능하므로 필터링 없음
    
    # 공정 ID 필터링 (추가 필터)
    if process_id:
        query = query.filter(Program.process_id == process_id)
    
    # 페이지네이션
    total = query.count()
    programs = query.order_by(Program.create_dt.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "status": "success",
        "data": [
            {
                "program_id": p.program_id,
                "program_name": p.program_name,
                "process_id": p.process_id,
                "status": p.status
            }
            for p in programs
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }
```

### 9.4 공정 접근 권한 체크 유틸리티 함수

```python
# ai_backend/src/utils/permission_utils.py
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models.permission_group_models import (
    PermissionGroup,
    UserGroupMapping,
    GroupProcessPermission
)
from src.database.models.master_models import ProcessMaster


def check_process_access(user_id: str, process_id: str, db: Session) -> bool:
    """
    사용자가 특정 공정에 접근할 수 있는지 확인
    
    Args:
        user_id: 사용자 ID
        process_id: 공정 ID
        db: 데이터베이스 세션
        
    Returns:
        bool: True면 해당 공정 접근 가능
    """
    # 사용자가 속한 활성 그룹 조회
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(
            and_(
                UserGroupMapping.user_id == user_id,
                UserGroupMapping.is_active == True,
                PermissionGroup.is_active == True,
                PermissionGroup.is_deleted == False
            )
        )
        .all()
    )
    
    for group in groups:
        # 시스템 관리자: 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_SYSTEM_ADMIN:
            return True
        
        # 통합 관리자: PLC 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            # GROUP_PROCESS_PERMISSIONS 확인
            process_permissions = (
                db.query(GroupProcessPermission)
                .filter(
                    and_(
                        GroupProcessPermission.group_id == group.group_id,
                        GroupProcessPermission.is_active == True
                    )
                )
                .all()
            )
            # 비어있으면 모든 공정 접근 가능
            if not process_permissions:
                return True
            # 또는 해당 공정이 포함되어 있으면 접근 가능
            if any(pp.process_id == process_id for pp in process_permissions):
                return True
        
        # 공정 관리자: GROUP_PROCESS_PERMISSIONS에 해당 공정이 있으면 접근 가능
        if group.role == PermissionGroup.ROLE_PROCESS_MANAGER:
            process_permissions = (
                db.query(GroupProcessPermission)
                .filter(
                    and_(
                        GroupProcessPermission.group_id == group.group_id,
                        GroupProcessPermission.process_id == process_id,
                        GroupProcessPermission.is_active == True
                    )
                )
                .first()
            )
            if process_permissions:
                return True
    
    return False


def get_user_roles(user_id: str, db: Session) -> List[str]:
    """
    사용자의 role 목록 조회
    
    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        
    Returns:
        List[str]: role 목록 (예: ['system_admin', 'process_manager'])
    """
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(
            and_(
                UserGroupMapping.user_id == user_id,
                UserGroupMapping.is_active == True,
                PermissionGroup.is_active == True,
                PermissionGroup.is_deleted == False
            )
        )
        .all()
    )
    
    return list(set([group.role for group in groups]))
```

### 9.5 API 사용 예시

#### 예시 1: 시스템 관리자가 사용자 목록 조회

```bash
# 요청
GET /v1/users?user_id=user_sys_admin&page=1&page_size=10

# 응답 (성공)
{
    "status": "success",
    "data": [
        {
            "user_id": "user_sys_admin",
            "employee_id": "SO10001",
            "name": "김관리"
        },
        ...
    ],
    "page": 1,
    "page_size": 10
}
```

#### 예시 2: 공정 관리자가 사용자 목록 조회 시도 (권한 없음)

```bash
# 요청
GET /v1/users?user_id=user_process_manager_001&page=1&page_size=10

# 응답 (실패)
{
    "detail": "사용자 관리 기능에 접근할 권한이 없습니다. 시스템 관리자만 접근 가능합니다."
}
# HTTP Status: 403 Forbidden
```

#### 예시 3: 공정 관리자가 프로그램 목록 조회 (자신의 공정만 조회)

```bash
# 요청 (user_process_manager_003은 전극, 조립 공정만 접근 가능)
GET /v1/programs?user_id=user_process_manager_003&page=1&page_size=10

# 응답
{
    "status": "success",
    "data": [
        {
            "program_id": "pgm_electrode_001",
            "program_name": "전극 공정 프로그램1",
            "process_id": "prc_electrode",
            "status": "completed"
        },
        {
            "program_id": "pgm_assembly_001",
            "program_name": "조립 공정 프로그램1",
            "process_id": "prc_assembly",
            "status": "completed"
        }
        // 모듈, 화성 공정의 프로그램은 조회되지 않음
    ],
    "total": 2,
    "page": 1,
    "page_size": 10
}
```

#### 예시 4: 시스템 관리자가 프로그램 목록 조회 (모든 공정 조회)

```bash
# 요청
GET /v1/programs?user_id=user_sys_admin&page=1&page_size=10

# 응답
{
    "status": "success",
    "data": [
        {
            "program_id": "pgm_module_001",
            "program_name": "모듈 공정 프로그램1",
            "process_id": "prc_module",
            "status": "completed"
        },
        {
            "program_id": "pgm_electrode_001",
            "program_name": "전극 공정 프로그램1",
            "process_id": "prc_electrode",
            "status": "completed"
        }
        // 모든 공정의 프로그램이 조회됨
    ],
    "total": 10,
    "page": 1,
    "page_size": 10
}
```

---

## 10. 요약

### 테이블 구조

1. **PERMISSION_GROUPS**: 그룹 정보 및 role 저장
2. **GROUP_PROCESS_PERMISSIONS**: 그룹별 공정 권한 (복수 선택)
3. **USER_GROUP_MAPPINGS**: 사용자-그룹 매핑

### Role별 권한

- **시스템 관리자**: 사용자 관리 + 기준정보 관리 + 모든 공정 접근
- **통합 관리자**: PLC 모든 공정 접근
- **공정 관리자**: 선택한 공정만 접근

### 권한 체크 방법

1. 사용자 관리/기준정보 관리: `role == 'system_admin'` 확인
2. 공정 접근: role에 따라 `GROUP_PROCESS_PERMISSIONS` 확인

