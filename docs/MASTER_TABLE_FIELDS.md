# 마스터 테이블 필드 용도 설명

## 개요
Plant, Process, Line 마스터 테이블의 공통 필드(`description`, `display_order`, `metadata_json`) 용도를 설명합니다.

---

## 1. DESCRIPTION (설명)

### 용도
- **기준정보 항목에 대한 추가 설명**을 저장하는 필드
- 사용자가 해당 항목에 대한 상세 정보나 메모를 기록할 수 있음
- 화면에서 툴팁이나 상세 정보 표시에 활용 가능

### 사용 예시
```python
# Plant 생성 시
plant = PlantMaster(
    plant_id="plant_001",
    plant_code="P001",
    plant_name="본사 공장",
    description="서울 본사에 위치한 메인 제조 공장입니다.",  # 추가 설명
    create_user="admin"
)
```

### 특징
- `Text` 타입: 긴 텍스트 저장 가능
- `nullable=True`: 필수 항목 아님 (선택적)
- 화면에서 표시/숨김 처리 가능

---

## 2. DISPLAY_ORDER (표시 순서)

### 용도
- **드롭다운이나 목록에서 항목을 정렬할 때 사용하는 순서 값**
- 숫자가 작을수록 앞에 표시됨 (오름차순 정렬)
- 같은 `display_order` 값이면 `code`로 2차 정렬

### 사용 예시
```python
# Process 생성 시
process1 = ProcessMaster(
    process_id="process_001",
    process_code="PR001",
    process_name="모듈",
    display_order=1,  # 첫 번째로 표시
    create_user="admin"
)

process2 = ProcessMaster(
    process_id="process_002",
    process_code="PR002",
    process_name="전극",
    display_order=2,  # 두 번째로 표시
    create_user="admin"
)
```

### 정렬 로직
```python
# CRUD에서 사용하는 정렬 방식
query.order_by(
    ProcessMaster.display_order,  # 1차 정렬: display_order 오름차순
    ProcessMaster.process_code    # 2차 정렬: code 오름차순
)
```

### 특징
- `Integer` 타입: 정수 값
- `nullable=True`, `default=0`: 기본값 0
- 인덱스: `IS_ACTIVE + DISPLAY_ORDER` 복합 인덱스로 조회 성능 최적화
- 화면에서 드롭다운 항목 순서 제어에 필수

---

## 3. METADATA_JSON (메타데이터 JSON)

### 용도
- **기준정보 항목에 대한 확장 가능한 추가 정보**를 JSON 형식으로 저장
- 테이블 스키마 변경 없이 유연하게 정보를 추가/수정 가능
- 향후 요구사항 변경 시 스키마 마이그레이션 없이 대응 가능

### 사용 예시
```python
# Plant 생성 시 메타데이터 저장
plant = PlantMaster(
    plant_id="plant_001",
    plant_code="P001",
    plant_name="본사 공장",
    metadata_json={
        "location": {
            "address": "서울시 강남구",
            "latitude": 37.5665,
            "longitude": 126.9780
        },
        "capacity": {
            "max_production": 10000,
            "unit": "units/day"
        },
        "contact": {
            "manager": "홍길동",
            "phone": "02-1234-5678"
        }
    },
    create_user="admin"
)
```

### 활용 사례
1. **위치 정보**: 주소, 좌표 등
2. **용량 정보**: 최대 생산량, 단위 등
3. **연락처 정보**: 담당자, 전화번호 등
4. **설비 정보**: 장비 목록, 상태 등
5. **커스텀 필드**: 프로젝트별 특수 요구사항

### 특징
- `JSON` 타입: 구조화된 데이터 저장
- `nullable=True`: 필수 항목 아님
- 스키마 변경 없이 확장 가능
- API 응답에 포함하여 프론트엔드에서 활용 가능

### 주의사항
- JSON 구조는 프로젝트 내에서 일관성 있게 정의 필요
- 너무 많은 정보를 저장하면 성능 저하 가능
- 중요한 비즈니스 로직 데이터는 별도 컬럼으로 관리 권장

---

## 요약

| 필드 | 타입 | 용도 | 필수 여부 | 기본값 |
|------|------|------|-----------|--------|
| `description` | Text | 기준정보 항목에 대한 추가 설명 | 선택 | NULL |
| `display_order` | Integer | 드롭다운/목록 정렬 순서 | 선택 | 0 |
| `metadata_json` | JSON | 확장 가능한 추가 정보 | 선택 | NULL |

### 사용 권장사항
- **description**: 사용자에게 도움이 되는 간단한 설명 (1-2줄 권장)
- **display_order**: 드롭다운에서 중요도에 따라 1, 2, 3... 순서로 설정
- **metadata_json**: 향후 확장 가능성이 있는 정보만 저장, 핵심 데이터는 별도 컬럼 사용

