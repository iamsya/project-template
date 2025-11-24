# 그룹 관리 테이블 스키마

## 개요

그룹 관리 기능을 위한 테이블 스키마입니다. 사용자가 화면에서 그룹을 생성하고, role과 공정을 선택하여 권한을 부여하며, 사용자를 그룹에 추가/삭제할 수 있습니다.

### 주요 특징

1. **Role 권한**: 시스템 관리자, 통합 관리자, 공정 관리자 중 단수 선택
2. **공정 권한**: 복수 선택 가능 (공정 관리자의 경우)
3. **사용자 매핑**: 그룹에 사용자 추가/삭제 가능
4. **그룹 수정**: role, 공정, 사용자 수정 가능
5. **그룹 삭제**: 소프트 삭제 지원

---

## 1. 권한 그룹 테이블 (PERMISSION_GROUPS)

### 테이블 구조

```sql
CREATE TABLE PERMISSION_GROUPS (
    GROUP_ID VARCHAR(50) PRIMARY KEY,
    GROUP_NAME VARCHAR(100) NOT NULL,
    DESCRIPTION TEXT,
    ROLE VARCHAR(50) NOT NULL,  -- Role 권한 (system_admin, integrated_admin, process_manager)
    MENU_PERMISSIONS JSON,  -- 접근 가능한 메뉴명 리스트 (선택사항)
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
CREATE INDEX idx_permission_group_active_deleted 
    ON PERMISSION_GROUPS(IS_ACTIVE, IS_DELETED);
CREATE INDEX idx_permission_group_role 
    ON PERMISSION_GROUPS(ROLE);
```

### Role 타입

- `system_admin`: 시스템 관리자
  - 사용자 관리 접근 가능
  - 모든 공정 접근 권한
  - 기준정보 관리 접근 가능
  
- `integrated_admin`: 통합 관리자
  - PLC 모든 공정 접근 가능
  - 사용자 관리 접근 불가
  
- `process_manager`: 공정 관리자
  - 화면에서 선택한 공정만 접근 가능
  - 사용자 관리 접근 불가

### 필드 설명

| 필드명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| GROUP_ID | VARCHAR(50) | ❌ No | 권한 그룹 ID (PK) |
| GROUP_NAME | VARCHAR(100) | ❌ No | 권한 그룹명 |
| DESCRIPTION | TEXT | ✅ Yes | 권한 그룹 설명 |
| ROLE | VARCHAR(50) | ❌ No | Role 권한 타입 |
| MENU_PERMISSIONS | JSON | ✅ Yes | 접근 가능한 메뉴명 리스트 |
| IS_ACTIVE | BOOLEAN | ❌ No | 활성화 여부 |
| CREATE_DT | TIMESTAMP | ❌ No | 생성 일시 |
| CREATE_USER | VARCHAR(50) | ❌ No | 생성자 |
| UPDATE_DT | TIMESTAMP | ✅ Yes | 수정 일시 |
| UPDATE_USER | VARCHAR(50) | ✅ Yes | 수정자 |
| IS_DELETED | BOOLEAN | ❌ No | 삭제 여부 (소프트 삭제) |
| DELETED_AT | TIMESTAMP | ✅ Yes | 삭제 일시 |
| DELETED_BY | VARCHAR(50) | ✅ Yes | 삭제자 |

---

## 2. 권한 그룹별 공정 권한 테이블 (GROUP_PROCESS_PERMISSIONS)

### 테이블 구조

```sql
CREATE TABLE GROUP_PROCESS_PERMISSIONS (
    PERMISSION_ID VARCHAR(50) PRIMARY KEY,
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES PERMISSION_GROUPS(GROUP_ID),
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE UNIQUE INDEX idx_group_process_permission_unique 
    ON GROUP_PROCESS_PERMISSIONS(GROUP_ID, PROCESS_ID);
CREATE INDEX idx_group_process_permission_group_active 
    ON GROUP_PROCESS_PERMISSIONS(GROUP_ID, IS_ACTIVE);
CREATE INDEX idx_group_process_permission_process_active 
    ON GROUP_PROCESS_PERMISSIONS(PROCESS_ID, IS_ACTIVE);
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

- **공정 관리자**: 이 테이블에 선택한 공정들을 추가
- **통합 관리자**: 이 테이블에 모든 공정을 추가하거나, 비어있으면 모든 공정 접근 가능으로 간주
- **시스템 관리자**: 이 테이블에 데이터가 없어도 모든 공정 접근 가능

---

## 3. 사용자-권한 그룹 매핑 테이블 (USER_GROUP_MAPPINGS)

### 테이블 구조

```sql
CREATE TABLE USER_GROUP_MAPPINGS (
    MAPPING_ID VARCHAR(50) PRIMARY KEY,
    USER_ID VARCHAR(50) NOT NULL REFERENCES USERS(USER_ID),
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES PERMISSION_GROUPS(GROUP_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE UNIQUE INDEX idx_user_group_mapping_unique 
    ON USER_GROUP_MAPPINGS(USER_ID, GROUP_ID);
CREATE INDEX idx_user_group_mapping_user_active 
    ON USER_GROUP_MAPPINGS(USER_ID, IS_ACTIVE);
CREATE INDEX idx_user_group_mapping_group_active 
    ON USER_GROUP_MAPPINGS(GROUP_ID, IS_ACTIVE);
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
- `GROUP_PROCESS_PERMISSIONS` 테이블 확인 불필요
- 모든 공정에 대한 접근 권한 자동 부여

#### 통합 관리자 (integrated_admin)
- **PLC 모든 공정 접근 가능**
- `GROUP_PROCESS_PERMISSIONS` 테이블에 모든 공정이 있거나, 비어있으면 모든 공정 접근 가능으로 간주

#### 공정 관리자 (process_manager)
- **선택한 공정만 접근 가능**
- `GROUP_PROCESS_PERMISSIONS` 테이블에서 해당 그룹의 `PROCESS_ID` 목록만 접근 가능

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
        
        # 통합 관리자: PLC 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            # GROUP_PROCESS_PERMISSIONS에 모든 공정이 있거나 비어있으면 모든 공정 접근 가능
            process_permissions = get_group_process_permissions(group.group_id)
            if not process_permissions:  # 비어있으면 모든 공정 접근 가능
                return True
            # 또는 모든 공정이 포함되어 있으면 접근 가능
            all_processes = get_all_active_processes()
            if len(process_permissions) == len(all_processes):
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
        
        # 통합 관리자: PLC 모든 공정 접근 가능
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            process_permissions = get_group_process_permissions(group.group_id)
            if not process_permissions:  # 비어있으면 모든 공정 접근 가능
                all_processes = get_all_active_processes()
                accessible_processes.update([p.process_id for p in all_processes])
            else:
                accessible_processes.update([pp.process_id for pp in process_permissions])
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
    pg.ROLE,
    pg.DESCRIPTION,
    COUNT(DISTINCT ugm.USER_ID) AS user_count,
    pg.CREATE_DT,
    pg.CREATE_USER
FROM PERMISSION_GROUPS pg
LEFT JOIN USER_GROUP_MAPPINGS ugm 
    ON pg.GROUP_ID = ugm.GROUP_ID 
    AND ugm.IS_ACTIVE = true
WHERE pg.IS_DELETED = false
    AND pg.IS_ACTIVE = true
GROUP BY pg.GROUP_ID, pg.GROUP_NAME, pg.ROLE, pg.DESCRIPTION, pg.CREATE_DT, pg.CREATE_USER
ORDER BY pg.CREATE_DT DESC;
```

### 5.2 그룹 상세 조회 (공정 목록 포함)

```sql
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE,
    pg.DESCRIPTION,
    pm.PROCESS_ID,
    pm.PROCESS_NAME
FROM PERMISSION_GROUPS pg
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
FROM USER_GROUP_MAPPINGS ugm
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
FROM USER_GROUP_MAPPINGS ugm
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
│   ├─ Yes → GROUP_PROCESS_PERMISSIONS│
│   │        확인                      │
│   │   ├─ 비어있음 → 모든 공정 접근   │
│   │   └─ 있음 → 포함된 공정만 접근   │
│   └─ No → 다음 확인                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ role == 'process_manager'?           │
│   ├─ Yes → GROUP_PROCESS_PERMISSIONS│
│   │        에 해당 공정이 있는지 확인│
│   │   ├─ 있음 → 접근 허용            │
│   │   └─ 없음 → 접근 거부            │
│   └─ No → 접근 거부                  │
└─────────────────────────────────────┘
```

---

## 7. 구현 시 주의사항

### 7.1 Foreign Key 제약조건

- `USER_GROUP_MAPPINGS.USER_ID` → `USERS.USER_ID` (같은 Base 사용)
- `USER_GROUP_MAPPINGS.GROUP_ID` → `PERMISSION_GROUPS.GROUP_ID` (같은 Base 사용)
- `GROUP_PROCESS_PERMISSIONS.GROUP_ID` → `PERMISSION_GROUPS.GROUP_ID` (같은 Base 사용)
- `GROUP_PROCESS_PERMISSIONS.PROCESS_ID` → `PROCESS_MASTER.PROCESS_ID` (같은 Base 사용)

모든 테이블이 `ai_backend`의 `Base`를 사용하므로 Foreign Key 제약조건이 정상 작동합니다.

### 7.2 그룹 삭제 시 처리

- 그룹 삭제 시 `IS_DELETED = true`로 설정 (소프트 삭제)
- 관련된 `USER_GROUP_MAPPINGS`의 `IS_ACTIVE = false`로 설정
- 관련된 `GROUP_PROCESS_PERMISSIONS`의 `IS_ACTIVE = false`로 설정

### 7.3 사용자 그룹에서 삭제 시 처리

- `USER_GROUP_MAPPINGS`의 `IS_ACTIVE = false`로 설정 (소프트 삭제)
- 실제 레코드는 삭제하지 않음 (이력 관리)

---

## 8. 예시 데이터

### 8.1 전체 예시 데이터 구조

다음은 실제 사용 시나리오를 반영한 예시 데이터입니다.

#### 8.1.1 사용자 데이터 (USERS 테이블)

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

#### 8.1.2 공정 데이터 (PROCESS_MASTER 테이블)

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

#### 8.1.3 권한 그룹 데이터 (PERMISSION_GROUPS 테이블)

```sql
-- 1. 시스템 관리자 그룹
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_system_admin',
        '시스템 관리자',
        'system_admin',
        '시스템 관리자 그룹 - 사용자 관리 및 모든 공정 접근 가능',
        'admin'
    );

-- 2. 통합 관리자 그룹
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_integrated_admin',
        '통합 관리자',
        'integrated_admin',
        '통합 관리자 그룹 - PLC 모든 공정 접근 가능',
        'admin'
    );

-- 3. 모듈 공정 담당자 그룹
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_module_manager',
        '모듈 공정 담당자',
        'process_manager',
        '모듈 공정 관리자 그룹',
        'admin'
    );

-- 4. 화성 공정 담당자 그룹
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_hwaseong_manager',
        '화성 공정 담당자',
        'process_manager',
        '화성 공정 관리자 그룹',
        'admin'
    );

-- 5. 전극 및 조립 공정 담당자 그룹
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'grp_electrode_assembly_manager',
        '전극 및 조립 공정 담당자',
        'process_manager',
        '전극, 조립 공정 관리자 그룹',
        'admin'
    );
```

#### 8.1.4 그룹별 공정 권한 데이터 (GROUP_PROCESS_PERMISSIONS 테이블)

```sql
-- 통합 관리자: 모든 공정 접근 가능 (모든 공정 추가)
INSERT INTO GROUP_PROCESS_PERMISSIONS 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_integrated_module', 'grp_integrated_admin', 'prc_module', 'admin'),
    ('perm_integrated_hwaseong', 'grp_integrated_admin', 'prc_hwaseong', 'admin'),
    ('perm_integrated_automation', 'grp_integrated_admin', 'prc_automation_logistics', 'admin'),
    ('perm_integrated_electrode', 'grp_integrated_admin', 'prc_electrode', 'admin'),
    ('perm_integrated_assembly', 'grp_integrated_admin', 'prc_assembly', 'admin');

-- 모듈 공정 담당자: 모듈 공정만 접근 가능
INSERT INTO GROUP_PROCESS_PERMISSIONS 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_module_module', 'grp_module_manager', 'prc_module', 'admin');

-- 화성 공정 담당자: 화성 공정만 접근 가능
INSERT INTO GROUP_PROCESS_PERMISSIONS 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_hwaseong_hwaseong', 'grp_hwaseong_manager', 'prc_hwaseong', 'admin');

-- 전극 및 조립 공정 담당자: 전극, 조립 공정 접근 가능
INSERT INTO GROUP_PROCESS_PERMISSIONS 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_electrode_electrode', 'grp_electrode_assembly_manager', 'prc_electrode', 'admin'),
    ('perm_electrode_assembly', 'grp_electrode_assembly_manager', 'prc_assembly', 'admin');

-- 시스템 관리자는 GROUP_PROCESS_PERMISSIONS에 데이터가 없어도 모든 공정 접근 가능
```

#### 8.1.5 사용자-그룹 매핑 데이터 (USER_GROUP_MAPPINGS 테이블)

```sql
-- 사용자 1 (김관리) → 시스템 관리자 그룹
INSERT INTO USER_GROUP_MAPPINGS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_001', 'user_sys_admin', 'grp_system_admin', 'admin');

-- 사용자 2 (이통합) → 통합 관리자 그룹
INSERT INTO USER_GROUP_MAPPINGS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_002', 'user_integrated_admin', 'grp_integrated_admin', 'admin');

-- 사용자 3 (박모듈) → 모듈 공정 담당자 그룹
INSERT INTO USER_GROUP_MAPPINGS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_003', 'user_process_manager_001', 'grp_module_manager', 'admin');

-- 사용자 4 (최화성) → 화성 공정 담당자 그룹
INSERT INTO USER_GROUP_MAPPINGS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_004', 'user_process_manager_002', 'grp_hwaseong_manager', 'admin');

-- 사용자 5 (정전극) → 전극 및 조립 공정 담당자 그룹
INSERT INTO USER_GROUP_MAPPINGS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_005', 'user_process_manager_003', 'grp_electrode_assembly_manager', 'admin');
```

### 8.2 예시 데이터 조회 결과

#### 8.2.1 그룹 목록 조회 (사용자 수 포함)

```sql
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE,
    COUNT(DISTINCT ugm.USER_ID) AS user_count,
    pg.CREATE_DT
FROM PERMISSION_GROUPS pg
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

#### 8.2.2 그룹 상세 조회 (공정 목록 포함)

```sql
-- 그룹 ID: grp_electrode_assembly_manager
SELECT 
    pg.GROUP_ID,
    pg.GROUP_NAME,
    pg.ROLE,
    pm.PROCESS_ID,
    pm.PROCESS_NAME
FROM PERMISSION_GROUPS pg
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

#### 8.2.3 그룹 사용자 목록 조회

```sql
-- 그룹 ID: grp_module_manager
SELECT 
    u.USER_ID,
    u.EMPLOYEE_ID,
    u.NAME,
    ugm.CREATE_DT AS joined_dt
FROM USER_GROUP_MAPPINGS ugm
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

#### 8.2.4 사용자의 접근 가능한 공정 조회

```sql
-- 사용자 ID: user_process_manager_003 (정전극)
-- 이 사용자는 전극 및 조립 공정 담당자 그룹에 속함

SELECT DISTINCT pm.PROCESS_ID, pm.PROCESS_NAME
FROM USER_GROUP_MAPPINGS ugm
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

### 8.3 권한 시나리오 예시

#### 시나리오 1: 시스템 관리자 (user_sys_admin)

- **속한 그룹**: grp_system_admin (role: system_admin)
- **접근 가능한 기능**:
  - ✅ 사용자 관리 (사용자 추가/수정/삭제)
  - ✅ 기준정보 관리 (Plant, Process, Line 마스터 관리)
  - ✅ 모든 공정의 PLC/Program 조회 및 관리
- **접근 가능한 공정**: 모든 공정 (prc_module, prc_hwaseong, prc_automation_logistics, prc_electrode, prc_assembly)

#### 시나리오 2: 통합 관리자 (user_integrated_admin)

- **속한 그룹**: grp_integrated_admin (role: integrated_admin)
- **접근 가능한 기능**:
  - ❌ 사용자 관리 (접근 불가)
  - ❌ 기준정보 관리 (접근 불가)
  - ✅ 모든 공정의 PLC/Program 조회 및 관리
- **접근 가능한 공정**: 모든 공정 (GROUP_PROCESS_PERMISSIONS에 모든 공정이 있음)

#### 시나리오 3: 공정 관리자 - 모듈 (user_process_manager_001)

- **속한 그룹**: grp_module_manager (role: process_manager)
- **접근 가능한 기능**:
  - ❌ 사용자 관리 (접근 불가)
  - ❌ 기준정보 관리 (접근 불가)
  - ✅ 모듈 공정의 PLC/Program만 조회 및 관리
- **접근 가능한 공정**: prc_module만

#### 시나리오 4: 공정 관리자 - 전극 및 조립 (user_process_manager_003)

- **속한 그룹**: grp_electrode_assembly_manager (role: process_manager)
- **접근 가능한 기능**:
  - ❌ 사용자 관리 (접근 불가)
  - ❌ 기준정보 관리 (접근 불가)
  - ✅ 전극, 조립 공정의 PLC/Program만 조회 및 관리
- **접근 가능한 공정**: prc_electrode, prc_assembly

---

## 9. 권한 체크 구현 가이드

### 9.1 API 엔드포인트에서 권한 체크

```python
from functools import wraps
from fastapi import HTTPException, status

def require_role(allowed_roles: List[str]):
    """특정 role만 접근 가능한 API 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or get_current_user_id()
            user_roles = get_user_roles(user_id)
            
            if not any(role in allowed_roles for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="접근 권한이 없습니다."
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 사용 예시
@router.get("/users")
@require_role([PermissionGroup.ROLE_SYSTEM_ADMIN])
async def get_users():
    """시스템 관리자만 접근 가능"""
    pass
```

### 9.2 공정 접근 권한 체크

```python
def check_process_access(user_id: str, process_id: str) -> bool:
    """공정 접근 권한 확인"""
    groups = get_user_active_groups(user_id)
    
    for group in groups:
        if group.role == PermissionGroup.ROLE_SYSTEM_ADMIN:
            return True  # 시스템 관리자는 모든 공정 접근 가능
        
        if group.role == PermissionGroup.ROLE_INTEGRATED_ADMIN:
            # 통합 관리자는 모든 공정 접근 가능 (또는 GROUP_PROCESS_PERMISSIONS 확인)
            return True
        
        if group.role == PermissionGroup.ROLE_PROCESS_MANAGER:
            # 공정 관리자는 GROUP_PROCESS_PERMISSIONS 확인
            permissions = get_group_process_permissions(group.group_id)
            if any(p.process_id == process_id for p in permissions):
                return True
    
    return False
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

