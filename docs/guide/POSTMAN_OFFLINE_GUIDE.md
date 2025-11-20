# Postman 폐쇄망 환경 사용 가이드

폐쇄망 환경에서 Postman 컬렉션을 import하고 사용하는 방법을 안내합니다.

## 🚀 빠른 해결: Import 시 로그인 요구

**Import 버튼을 누르면 로그인하라고 나오는 경우:**

1. 로그인 화면에서 **"Skip Sign In"** 또는 **"Skip"** 버튼 찾기 (화면 하단 또는 우측 상단)
2. 버튼 클릭하여 로그인 없이 진행
3. 그래도 안 되면: **Settings (⚙️)** > **General** > **Sync** 비활성화
4. 다시 Import 시도

**중요**: Postman은 로그인 없이도 모든 기능을 사용할 수 있습니다!

## 📋 사전 준비사항

### 1. Postman 설치 확인

폐쇄망 환경에서 Postman이 설치되어 있어야 합니다.

```bash
# Postman 설치 확인 (Windows)
where postman

# Postman 설치 확인 (macOS/Linux)
which postman
```

**Postman 설치 방법:**
- **온라인 환경에서 다운로드**: https://www.postman.com/downloads/
- **오프라인 설치 파일**: Postman Desktop App 설치 파일을 USB 등으로 가져와 설치

### 2. Postman 버전 확인

Postman Desktop App을 사용하는 것을 권장합니다 (브라우저 확장 프로그램보다 안정적).

```bash
# Postman 버전 확인
# Postman 앱 실행 후: Help > About Postman
```

**권장 버전**: Postman v10.0 이상

## 📥 컬렉션 Import 방법

### ⚠️ 로그인 요구 시 해결 방법

Postman에서 로그인을 요구하는 경우, 다음 방법으로 우회할 수 있습니다:

#### 방법 A: Skip Sign In 버튼 클릭

1. Postman 앱 실행 시 로그인 화면이 나타나면
2. 화면 하단 또는 우측 상단의 **"Skip Sign In"** 또는 **"Skip"** 버튼 클릭
3. 로그인 없이 Postman 사용 가능

#### 방법 B: Settings에서 로그인 비활성화

1. Postman 실행 후 (로그인 화면에서 Skip 클릭)
2. **Settings** (⚙️ 아이콘) 클릭
3. **General** 탭에서:
   - **"Sync"** 또는 **"Sync with Postman"** 비활성화
   - **"Require Sign In"** 옵션이 있으면 비활성화
4. **Save** 클릭

#### 방법 C: 오프라인 모드로 시작

1. Postman 설치 후 첫 실행 시
2. 인터넷 연결을 차단한 상태에서 실행
3. 자동으로 오프라인 모드로 시작됨
4. 로그인 없이 사용 가능

### 방법 1: File > Import (권장)

1. Postman 앱 실행 (로그인 Skip)
2. **File** > **Import** 클릭
3. **Upload Files** 탭 선택
4. `COMPLETE_API.postman_collection.json` 또는 `PLC_PGM_MAPPING_API.postman_collection.json` 파일 선택
5. **Import** 클릭

### 방법 2: 드래그 앤 드롭

1. Postman 앱 실행 (로그인 Skip)
2. 파일 탐색기에서 `.postman_collection.json` 파일을 Postman 창으로 드래그 앤 드롭
3. 자동으로 import됨

### 방법 3: 폴더에서 직접 열기

1. Postman 앱 실행 (로그인 Skip)
2. **Import** 버튼 클릭
3. **Folder** 탭 선택
4. 컬렉션 파일이 있는 폴더 선택

## 🔍 Import 실패 시 문제 해결

### 문제 0: Import 시 로그인 요구

**증상**: Import 버튼을 클릭하면 로그인 화면이 나타남

**원인**: Postman 최신 버전에서 로그인을 권장하지만, 필수는 아닙니다.

**해결 방법**:

1. **Skip Sign In 버튼 찾기**
   - 로그인 화면에서 화면 하단이나 우측 상단의 **"Skip Sign In"**, **"Skip"**, **"Continue without signing in"** 버튼 클릭
   - 버튼이 보이지 않으면 작은 글씨로 되어 있을 수 있으니 화면 전체를 확인

2. **Settings에서 Sync 비활성화**
   ```
   Settings (⚙️) > General > Sync 비활성화
   ```

3. **오프라인 모드로 강제 실행**
   - 네트워크 연결을 일시적으로 차단
   - Postman 실행
   - 오프라인 모드로 시작됨
   - 이후 네트워크 재연결해도 로그인 없이 사용 가능

4. **구버전 Postman 사용 (최후의 수단)**
   - Postman v8.x 이하 버전은 로그인 요구가 덜함
   - 다만 최신 컬렉션 형식 지원이 제한될 수 있음

**중요**: Postman은 로그인 없이도 모든 기능을 사용할 수 있습니다. 로그인은 동기화와 협업 기능을 위한 것이며, 로컬에서 컬렉션을 import하고 사용하는 데는 필수가 아닙니다.

### 문제 1: "Invalid JSON" 오류

**원인**: JSON 파일 형식이 잘못되었거나 손상됨

**해결 방법**:
1. JSON 파일 유효성 검사:
   ```bash
   # Python으로 JSON 검증
   python -c "import json; json.load(open('COMPLETE_API.postman_collection.json'))"
   ```

2. JSON 포맷터로 확인:
   - 온라인: https://jsonformatter.org/ (폐쇄망에서는 사용 불가)
   - 오프라인: VS Code의 JSON 검증 기능 사용

### 문제 2: "Collection version not supported" 오류

**원인**: Postman 버전이 컬렉션 형식을 지원하지 않음

**해결 방법**:
1. Postman 버전 업데이트 (가능한 경우)
2. 컬렉션 파일의 schema 버전 확인:
   ```json
   {
     "info": {
       "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
     }
   }
   ```
3. Postman v8.0 이상이면 v2.1.0 스키마를 지원합니다

### 문제 3: Import는 되지만 요청이 실행되지 않음

**원인**: 환경 변수나 설정이 누락됨

**해결 방법**:
1. 컬렉션의 변수 확인:
   - `base_url`: 기본 API URL (기본값: `http://localhost:8000`)
   - `api_version`: API 버전 (기본값: `v1`)
   - `user_id`: 사용자 ID (기본값: `user001`)

2. 환경 변수 설정:
   - Postman에서 **Environments** 생성
   - 변수 값 설정

### 문제 4: Postman이 인터넷 연결을 요구함

**원인**: Postman이 초기 로그인이나 동기화를 시도함

**해결 방법**:
1. **Skip Sign In** 버튼 클릭 (화면 하단 또는 우측 상단 확인)
2. **Settings** > **General** > **Sync** 비활성화
3. 오프라인 모드로 사용:
   - Postman은 기본적으로 오프라인에서도 작동합니다
   - 로그인 없이도 컬렉션 import 및 사용 가능
4. 네트워크를 일시적으로 차단한 상태에서 Postman 실행 후 오프라인 모드로 시작

## 📁 프로젝트의 Postman 컬렉션

프로젝트에는 다음 Postman 컬렉션 파일이 포함되어 있습니다:

1. **COMPLETE_API.postman_collection.json**
   - 위치: `ai_backend/COMPLETE_API.postman_collection.json`
   - 용도: 전체 API 테스트용
   - 포함 API: PLC, Master, Program, Document 등 모든 API

2. **PLC_PGM_MAPPING_API.postman_collection.json**
   - 위치: `ai_backend/PLC_PGM_MAPPING_API.postman_collection.json`
   - 용도: PLC-PGM 매핑 관련 API 테스트용
   - 포함 API: PLC 조회, 매핑 저장 등

## 🔧 환경 변수 설정

### 컬렉션 변수 확인 및 수정

1. Postman에서 컬렉션 선택
2. **Variables** 탭 클릭
3. 다음 변수들을 환경에 맞게 수정:

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `base_url` | `http://localhost:8000` | API 서버 주소 |
| `api_version` | `v1` | API 버전 |
| `user_id` | `user001` | 사용자 ID |
| `plc_uuid` | `plc_001_...` | PLC UUID (예시) |
| `program_id` | `pgm_...` | Program ID (예시) |

### 환경별 설정 예시

**개발 환경:**
```
base_url: http://localhost:8000
```

**폐쇄망 Kubernetes 환경:**
```
base_url: http://<node-ip>:30080
```

**Port Forwarding 사용 시:**
```
base_url: http://localhost:8000
# 터미널에서: kubectl port-forward svc/ai_backend-service 8000:8000
```

## ✅ Import 확인 방법

1. **컬렉션 목록 확인**
   - 왼쪽 사이드바에서 컬렉션 이름 확인
   - 예: "Complete API Collection"

2. **요청 목록 확인**
   - 컬렉션을 펼쳐서 요청들이 제대로 import되었는지 확인

3. **변수 확인**
   - 컬렉션 선택 > **Variables** 탭에서 변수 확인

4. **요청 실행 테스트**
   - 간단한 GET 요청 (예: `/v1/plcs`) 실행하여 정상 작동 확인

## 🚨 주의사항

1. **로그인 불필요**: Postman은 로그인 없이도 모든 기능을 사용할 수 있습니다. Import 시 로그인을 요구해도 "Skip Sign In"으로 우회 가능합니다.
2. **인터넷 연결 불필요**: Postman은 오프라인에서도 컬렉션 import 및 API 테스트가 가능합니다.
3. **파일 인코딩**: JSON 파일은 UTF-8 인코딩이어야 합니다.
4. **파일 경로**: 파일 경로에 한글이나 특수문자가 있으면 문제가 될 수 있습니다.
5. **Postman 버전**: 오래된 버전은 최신 컬렉션 형식을 지원하지 않을 수 있습니다.
6. **Sync 기능**: Settings에서 Sync를 비활성화하면 로그인 요구가 줄어듭니다.

## 📝 대안 방법

Postman을 사용할 수 없는 경우:

### 1. cURL 사용
```bash
# 컬렉션의 요청을 cURL 명령어로 변환하여 사용
curl -X GET "http://localhost:8000/v1/plcs?user_id=user001"
```

### 2. HTTPie 사용
```bash
# HTTPie 설치 후
http GET localhost:8000/v1/plcs user_id==user001
```

### 3. Swagger UI 사용
- API 서버의 `/docs` 엔드포인트에서 Swagger UI 사용
- 폐쇄망 환경에서는 오프라인 Swagger UI 설정 필요 (참고: `SWAGGER_UI_OFFLINE_SETUP.md`)

## 🔗 관련 문서

- [API 가이드](../api/plcs.md)
- [API 가이드 - Masters](../api/masters.md)
- [Swagger UI 오프라인 설정](../../ai_backend/SWAGGER_UI_OFFLINE_SETUP.md)

