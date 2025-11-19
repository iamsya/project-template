# 채팅 화면 API 가이드

채팅 화면에서 사용하는 PLC 관련 API 가이드입니다.

## 목차

1. [PLC Tree 구조 조회](#1-plc-tree-구조-조회)

---

## 1. PLC Tree 구조 조회

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

## 참고사항

1. **필터링**: `is_deleted=false`이고 `program_id`가 있는 PLC만 반환됩니다.
2. **계층 구조**: Plant → Process → Line → PLC명 → 호기 순서로 계층 구조를 제공합니다.
3. **프론트엔드 사용**: 채팅 화면에서 PLC를 선택할 때 이 Tree 구조를 사용하여 사용자가 PLC를 쉽게 찾을 수 있습니다.

