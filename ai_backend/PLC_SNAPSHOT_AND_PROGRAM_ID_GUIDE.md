# PLC 스냅샷 저장 및 Program ID 조회 가이드

## 1. 스냅샷 저장 방안

### 문제 상황

채팅 메시지 전송 시 PLC UUID를 사용하지만, 메시지 조회 시에는 **메시지 생성 시점의 계층 구조**를 표시해야 합니다.

- 화면 계층: `Plant → 공정 → Line → 장비 그룹 → 호기 → PLC`
- 스냅샷 저장 항목: `plant, 공정, line, 호기, plc명, 등록일시`

### 해결 방안: 스키마 변경 없이 JSON 필드 활용

**현재 `CHAT_MESSAGES` 테이블 구조:**
- `plc_uuid`: PLC UUID (FK)
- `plc_hierarchy_snapshot`: JSON 필드 (이미 존재)

**스냅샷 JSON 구조:**
```json
{
  "plc_uuid": "uuid-123",
  "plc_id": "M1CFB01000",
  "plc_name": "01_01_CELL_FABRICATOR",
  "plant_id": "SN12",
  "plant_name": "BOSK KY1",
  "plant_code": "BOSK_KY1",
  "process_id": "process_001",
  "process_name": "공정",
  "process_code": "PROCESS",
  "line_id": "SN1241",
  "line_name": "Line1",
  "line_code": "LINE1",
  "unit": "1",
  "create_dt": "2025-10-31 18:39:00"
}
```

### 구현 방법

#### 1. 스냅샷 생성 함수 사용

```python
from src.database.crud.plc_crud import PLCCRUD

plc_crud = PLCCRUD(db_session)

# PLC UUID로 스냅샷 생성
snapshot = plc_crud.create_plc_hierarchy_snapshot(plc_uuid="uuid-123")

# 결과:
# {
#   "plc_uuid": "uuid-123",
#   "plc_id": "M1CFB01000",
#   "plc_name": "01_01_CELL_FABRICATOR",
#   "plant_id": "SN12",
#   "plant_name": "BOSK KY1",
#   ...
#   "create_dt": "2025-10-31 18:39:00"
# }
```

#### 2. 채팅 메시지 저장 시 스냅샷 저장

```python
from src.database.crud.chat_crud import ChatCRUD

chat_crud = ChatCRUD(db_session)

# 메시지 저장 시 스냅샷 자동 저장
message = chat_crud.save_user_message(
    chat_id="chat001",
    user_id="user001",
    message="선택한 PLC Ladder 기능 확인",
    plc_uuid="uuid-123",  # PLC UUID 전달
    plc_hierarchy_snapshot=snapshot  # 스냅샷 전달
)
```

#### 3. 메시지 조회 시 스냅샷 사용

```python
# 메시지 조회 시 plc_hierarchy_snapshot 자동 포함
messages = chat_crud.get_messages_from_db(chat_id="chat001")

for msg in messages:
    if msg.plc_hierarchy_snapshot:
        snapshot = msg.plc_hierarchy_snapshot
        print(f"Plant: {snapshot['plant_name']}")
        print(f"공정: {snapshot['process_name']}")
        print(f"Line: {snapshot['line_name']}")
        print(f"호기: {snapshot['unit']}")
        print(f"PLC명: {snapshot['plc_name']}")
        print(f"등록일시: {snapshot['create_dt']}")
```

### 장점

1. **스키마 변경 불필요**: 기존 `plc_hierarchy_snapshot` JSON 필드 활용
2. **유연성**: JSON이므로 필요 시 필드 추가/제거 용이
3. **과거 데이터 보존**: 메시지 생성 시점의 계층 구조 영구 보존
4. **성능**: JOIN 없이 스냅샷에서 직접 조회 가능

### 대안 (스키마 변경 시)

만약 스키마를 변경하고 싶다면:

```sql
ALTER TABLE CHAT_MESSAGES
ADD COLUMN PLC_PLANT_NAME_SNAPSHOT VARCHAR(255),
ADD COLUMN PLC_PROCESS_NAME_SNAPSHOT VARCHAR(255),
ADD COLUMN PLC_LINE_NAME_SNAPSHOT VARCHAR(255),
ADD COLUMN PLC_UNIT_SNAPSHOT VARCHAR(100),
ADD COLUMN PLC_NAME_SNAPSHOT VARCHAR(255),
ADD COLUMN PLC_CREATE_DT_SNAPSHOT DATETIME;
```

**단점:**
- 스키마 변경 필요
- 컬럼 추가로 인한 마이그레이션 작업
- 유연성 부족 (필드 추가 시 ALTER 필요)

**결론: JSON 필드 활용 권장**

---

## 2. PLC UUID → Program ID 조회

### 사용 목적

Open API 호출 시 `plc_uuid`에 해당하는 `program_id` 값을 전달해야 합니다.

### 구현된 함수

```python
from src.database.crud.plc_crud import PLCCRUD

plc_crud = PLCCRUD(db_session)

# PLC UUID로 Program ID 조회
program_id = plc_crud.get_program_id_from_plc_uuid(plc_uuid="uuid-123")

if program_id:
    print(f"Program ID: {program_id}")
    # Open API 호출 시 program_id 사용
else:
    print("Program ID가 없습니다.")
```

### 사용 예시

```python
# 채팅 메시지에서 PLC UUID 추출
plc_uuid = message.plc_uuid

# Program ID 조회
program_id = plc_crud.get_program_id_from_plc_uuid(plc_uuid)

if program_id:
    # Open API 호출
    response = open_api_client.call(
        program_id=program_id,
        query=message.message
    )
else:
    # Program ID가 없으면 에러 처리
    logger.warning(f"PLC {plc_uuid}에 매핑된 Program이 없습니다.")
```

### 반환 값

- **성공**: `str` - Program ID
- **실패**: `None` - PLC를 찾을 수 없거나 Program이 매핑되지 않음

### 로깅

- **성공**: `INFO` 레벨로 조회 결과 로깅
- **실패**: `WARNING` 레벨로 경고 로깅
- **에러**: `ERROR` 레벨로 에러 로깅

---

## 요약

### 1. 스냅샷 저장
- **함수**: `plc_crud.create_plc_hierarchy_snapshot(plc_uuid)`
- **저장 위치**: `CHAT_MESSAGES.plc_hierarchy_snapshot` (JSON)
- **스키마 변경**: 불필요 (기존 JSON 필드 활용)

### 2. Program ID 조회
- **함수**: `plc_crud.get_program_id_from_plc_uuid(plc_uuid)`
- **반환**: `Optional[str]` - Program ID 또는 None
- **용도**: Open API 호출 시 program_id 전달

