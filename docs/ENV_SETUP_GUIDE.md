# 환경 변수 설정 가이드

## 개요

이 가이드는 External API Provider를 포함한 모든 LLM Provider의 환경 변수 설정 방법을 설명합니다.

## .env 파일 생성

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# ==========================================
# LLM Provider Configuration
# ==========================================
# 사용할 LLM 제공자 선택: openai, azure_openai, external_api
LLM_PROVIDER=openai

# ==========================================
# OpenAI Configuration
# ==========================================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# ==========================================
# Azure OpenAI Configuration
# ==========================================
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MAX_TOKENS=1000
AZURE_OPENAI_TEMPERATURE=0.7

# ==========================================
# External API Configuration
# ==========================================
EXTERNAL_API_URL=https://your-external-api.com/api/chat
EXTERNAL_API_AUTHORIZATION=Bearer your_token_here
EXTERNAL_API_MAX_TOKENS=1000
EXTERNAL_API_TEMPERATURE=0.7

# ==========================================
# Application Configuration
# ==========================================
APP_VERSION=1.0.0
APP_LOCALE=en
APP_LOG_LEVEL=info
APP_DEBUG=false
APP_ROOT_PATH=

# ==========================================
# Server Configuration
# ==========================================
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_DEBUG=false
SERVER_RELOAD=false
SERVER_LOG_LEVEL=info

# ==========================================
# CORS Configuration
# ==========================================
CORS_ORIGINS=http://localhost:8000,file://

# ==========================================
# Database Configuration
# ==========================================
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=chat_db
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=password

# ==========================================
# Cache Configuration
# ==========================================
CACHE_ENABLED=true
CACHE_TTL_CHAT_MESSAGES=1800
CACHE_TTL_USER_CHATS=600

# ==========================================
# Redis Configuration
# ==========================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ==========================================
# Logging Configuration
# ==========================================
LOG_TO_FILE=false
LOG_DIR=./logs
LOG_FILE=app.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30
LOG_INCLUDE_EXC_INFO=true

# ==========================================
# File Upload Configuration
# ==========================================
UPLOAD_BASE_PATH=./uploads
UPLOAD_MAX_SIZE=52428800
UPLOAD_ALLOWED_TYPES=pdf,txt,doc,docx,jpg,jpeg,png,gif,xls,xlsx
```

## External API Provider 설정

### 1. 기본 설정

```bash
# Provider 타입 설정
LLM_PROVIDER=external_api

# API 엔드포인트
EXTERNAL_API_URL=https://your-external-api.com/api/chat

# 인증 헤더 (Bearer 토큰, API 키 등)
EXTERNAL_API_AUTHORIZATION=Bearer your_token_here
```

### 2. 고급 설정

```bash
# 최대 토큰 수 (기본값: 1000)
EXTERNAL_API_MAX_TOKENS=2000

# 온도 설정 (기본값: 0.7)
EXTERNAL_API_TEMPERATURE=0.5
```

### 3. 스트리밍 지원

External API가 스트리밍을 지원하는 경우:
- 일반 요청: `{EXTERNAL_API_URL}`
- 스트리밍 요청: `{EXTERNAL_API_URL}/stream`

## Provider 전환

### OpenAI → External API

```bash
# 1. .env 파일 수정
LLM_PROVIDER=external_api
EXTERNAL_API_URL=https://your-api.com/chat
EXTERNAL_API_AUTHORIZATION=Bearer your_token

# 2. 서버 재시작
python main.py
```

### External API → Azure OpenAI

```bash
# 1. .env 파일 수정
LLM_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment

# 2. 서버 재시작
python main.py
```

## 환경 변수 검증

설정이 올바른지 확인하려면:

```bash
# 가상환경 활성화
source app/backend/venv_py312/bin/activate

# 테스트 실행
python test_external_api_simple.py
```

## 보안 주의사항

1. **API 키 보호**: `.env` 파일을 `.gitignore`에 추가
2. **토큰 관리**: Bearer 토큰을 안전하게 보관
3. **환경 분리**: 개발/스테이징/프로덕션 환경별로 다른 설정 사용

## 문제 해결

### 1. External API 연결 실패

```
❌ External API error: 401 Unauthorized
```

**해결 방법:**
- `EXTERNAL_API_AUTHORIZATION` 확인
- Bearer 토큰 형식 확인: `Bearer your_token_here`
- API 서버 상태 확인

### 2. 스트리밍 응답 오류

```
❌ External API returned status 404
```

**해결 방법:**
- `/stream` 엔드포인트 지원 여부 확인
- API 문서에서 스트리밍 지원 확인
- URL 경로 정확성 확인

### 3. 응답 파싱 오류

```
❌ JSON decode error
```

**해결 방법:**
- API 응답 형식 확인
- `content`, `text`, `response` 필드 중 하나가 있는지 확인
- API 문서 참조하여 응답 구조 확인

## 추가 리소스

- [LLM Provider 가이드](./LLM_PROVIDER_GUIDE.md)
- [설정 가이드](./CONFIG_GUIDE.md)
- [예외 처리 가이드](./EXCEPTION_GUIDE.md)
