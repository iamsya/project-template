# _*_ coding: utf-8 _*_
"""LLM Chat REST API endpoints (Redis 기반, 확장 가능)."""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.api.services.llm_chat_service import LLMChatService
from src.api.services.program_service import ProgramService
from src.core.dependencies import get_db, get_llm_chat_service, get_program_service
from src.types.request.chat_request import (
    CreateChatRequest,
    UserMessageRequest,
)
from src.types.response.chat_response import (
    AIResponse,
    ChatListResponse,
    ConversationClearedResponse,
    ConversationHistoryResponse,
    CreateChatResponse,
)
from src.types.response.exceptions import HandledException

logger = logging.getLogger(__name__)
router = APIRouter(tags=["llm-chat"])

class GenerateTitleRequest(BaseModel):
    message: str

@router.post("/chat/{chat_id}/message", response_model=AIResponse)
def send_message(
    chat_id: str,
    request: UserMessageRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """사용자 메시지를 전송하고 AI 응답을 받습니다."""
    logger.info(f"Received message for chat {chat_id}: {request.message[:50]}...")
    
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    ai_response = llm_chat_service.send_message_simple(
        chat_id, 
        request.message, 
        request.user_id,
        request.plc_uuid
    )
    
    return AIResponse(
        message_id=ai_response["message_id"],
        content=ai_response["content"],
        user_id="ai",
        timestamp=ai_response["timestamp"]
    )

@router.post("/chat/{chat_id}/stream")
async def send_message_stream(
    chat_id: str,
    request: UserMessageRequest,
    db: Session = Depends(get_db),
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service),
    program_service: ProgramService = Depends(get_program_service),
):
    """스트리밍 방식으로 메시지를 전송하고 AI 응답을 받습니다 (SSE)."""

    async def generate_stream():
        # 청크를 전달하기 위한 큐
        chunk_queue = asyncio.Queue()
        stream_active = asyncio.Event()
        stream_active.set()
        
        # Heartbeat task (10초마다 전송, Nginx 타임아웃 60초 대비)
        async def heartbeat_sender():
            try:
                elapsed_time = 0
                heartbeat_messages = {
                    10: "사용자의 의도를 파악하고 있습니다...",
                    30: "정확한 답변을 찾기 위해 노력하고 있습니다...",
                    50: "거의 다 완료되었습니다. 조금만 기다려주세요..."
                }
                
                while stream_active.is_set():
                    await asyncio.sleep(10)  # 10초마다 heartbeat
                    elapsed_time += 10
                    
                    # 경과 시간에 따라 적절한 메시지 선택
                    message = None
                    if elapsed_time in heartbeat_messages:
                        message = heartbeat_messages[elapsed_time]
                    else:
                        # 50초 이후에는 계속 마지막 메시지 표시
                        message = heartbeat_messages[50]
                    
                    heartbeat_data = {
                        'type': 'heartbeat',
                        'message': message,
                        'timestamp': llm_chat_service.get_current_timestamp()
                    }
                    await chunk_queue.put(heartbeat_data)
                    logger.debug(f"Sent heartbeat for chat {chat_id} at {elapsed_time}s: {message}")
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"Heartbeat sender error: {e}")
        
        # AI 스트림 수신 task
        async def ai_stream_receiver():
            try:
                # 사용자 메시지 저장
                user_message_id = llm_chat_service.save_user_message(
                    chat_id, request.message, request.user_id, request.plc_uuid
                )

                # 사용자 메시지 전송
                user_message_data = {
                    'type': 'user_message',
                    'message_id': user_message_id,
                    'content': request.message,
                    'user_id': request.user_id,
                    'timestamp': llm_chat_service.get_current_timestamp()
                }
                await chunk_queue.put(user_message_data)

                # AI 응답 생성 (스트리밍)
                async for chunk in llm_chat_service.generate_ai_response_stream(chat_id, request.user_id, request.plc_uuid):
                    await chunk_queue.put(chunk)
                
                # 완료 신호
                await chunk_queue.put(None)
                
            except HandledException as e:
                # HandledException은 스트림으로 전달 (연결 유지)
                logger.error(f"HandledException in streaming: {str(e)}")
                from src.types.response.chat_response import StreamErrorResponse
                error_response = StreamErrorResponse(
                    code=e.code,
                    message=e.message,
                    content=f"메시지 처리 중 오류가 발생했습니다: {e.message}",
                    timestamp=llm_chat_service.get_current_timestamp(),
                    chat_id=chat_id
                )
                await chunk_queue.put(error_response.dict())
                await chunk_queue.put(None)
            except Exception as e:
                # 예상치 못한 예외도 스트림으로 전달 (연결 유지)
                logger.error(f"Unexpected error in streaming: {str(e)}")
                from src.types.response.chat_response import StreamErrorResponse
                error_response = StreamErrorResponse(
                    code=-2,  # UNDEFINED_ERROR
                    message='정의되지 않은 오류입니다.',
                    content=f"메시지 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}",
                    timestamp=llm_chat_service.get_current_timestamp(),
                    chat_id=chat_id
                )
                await chunk_queue.put(error_response.dict())
                await chunk_queue.put(None)
        
        # 두 task를 병렬로 실행
        heartbeat_task = asyncio.create_task(heartbeat_sender())
        ai_stream_task = asyncio.create_task(ai_stream_receiver())
        
        try:
            # 큐에서 받은 데이터를 yield
            while True:
                chunk = await chunk_queue.get()
                if chunk is None:  # 완료 신호
                    break
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        finally:
            # 리소스 정리
            stream_active.clear()
            heartbeat_task.cancel()
            ai_stream_task.cancel()
            try:
                await asyncio.gather(heartbeat_task, ai_stream_task, return_exceptions=True)
            except Exception as e:
                logger.warning(f"Task cleanup error: {e}")

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get(
    "/chat/{chat_id}/history",
    response_model=ConversationHistoryResponse,
    summary="대화 히스토리 조회",
    description="""
    채팅방의 대화 히스토리(메시지 목록)를 조회합니다.
    
    **파라미터:**
    - `chat_id` (path): 조회할 채팅방의 고유 ID
    
    **조회 우선순위:**
    1. Redis 캐시에서 먼저 조회 (캐시 히트 시 즉시 반환)
    2. Redis에 없거나 실패한 경우 데이터베이스에서 조회
    3. 조회된 데이터를 Redis에 캐시 저장 (TTL: 30분)
    
    **응답 형식:**
    ```json
    {
      "type": "conversation_history",
      "history": [
        {
          "role": "user",
          "content": "사용자 메시지 내용",
          "timestamp": "2025-01-01T12:00:00+09:00",
          "cancelled": false,
          "message_id": "msg001",
          "plc_uuid": "plc-uuid-001",
          "plc_hierarchy": {
            "plant": {"id": "plant001", "code": "P001", "name": "공장1"},
            "process": {"id": "process001", "code": "PR001", "name": "공정1"},
            "line": {"id": "line001", "code": "L001", "name": "라인1"}
          },
          "plc_snapshot": {
            "plc_uuid": "plc-uuid-001",
            "plc_id": "M1CFB01000",
            "plc_name": "01_01_CELL_FABRICATOR",
            "plant_id": "plant001",
            "plant_name": "공장1",
            "plant_code": "P001",
            "process_id": "process001",
            "process_name": "공정1",
            "process_code": "PR001",
            "line_id": "line001",
            "line_name": "라인1",
            "line_code": "L001",
            "unit": "1",
            "create_dt": "2025-10-31 18:39:00"
          }
        },
        {
          "role": "assistant",
          "content": "AI 응답 내용",
          "timestamp": "2025-01-01T12:00:05+09:00",
          "cancelled": false,
          "message_id": "msg002",
          "plc_uuid": "plc-uuid-001",
          "plc_hierarchy": null,
          "plc_snapshot": null
        },
        ...
      ]
    }
    ```
    
    **메시지 객체 필드 설명:**
    - `role`: 메시지 역할
      - `"user"`: 사용자 메시지
      - `"assistant"`: AI 응답 메시지
      - `"system"`: 시스템 메시지 (취소된 메시지 등)
    - `content`: 메시지 내용 (텍스트)
    - `timestamp`: 메시지 생성 일시 (ISO 8601 형식, Asia/Seoul 타임존)
    - `cancelled`: 메시지 취소 여부 (boolean)
    - `message_id`: 메시지 고유 ID
    - `plc_uuid`: 관련 PLC UUID (선택적, null 가능)
    - `plc_hierarchy`: PLC 계층 구조 정보 (선택적, null 가능)
      - `plant`: Plant 정보 (id, code, name)
      - `process`: Process 정보 (id, code, name)
      - `line`: Line 정보 (id, code, name)
      - 메시지 생성 시점의 PLC 계층 구조 스냅샷 정보
    - `plc_snapshot`: PLC 전체 스냅샷 정보 (선택적, null 가능)
      - 메시지 생성 시점의 PLC 전체 정보 (plant, process, line, 호기, plc명, 등록일시 등)
      - 스냅샷이 있으면 스냅샷 사용, 없으면 null (공란)
    
    **PLC 정보 반환 규칙:**
    - PLC가 활성화된 경우 (`is_active=true`): 스냅샷 정보를 그대로 반환
    - PLC가 비활성화된 경우 (`is_active=false`): `plc_hierarchy`와 `plc_snapshot`을 `null`로 반환
      - `plc_uuid`는 그대로 반환 (메시지와의 연결 정보 유지)
      - 프론트엔드에서 `plc_hierarchy`와 `plc_snapshot`이 `null`이면 PLC 정보 폼을 비워야 함

    **정렬:**
    - 메시지는 생성 일시(`timestamp`) 기준 오름차순으로 정렬됩니다.
    - 가장 오래된 메시지가 첫 번째, 가장 최근 메시지가 마지막에 위치합니다.

    **캐싱:**
    - Redis 캐시 사용 시 성능 향상
    - 캐시 TTL: 30분
    - 캐시 미스 시 자동으로 DB에서 조회 후 캐시 갱신

    **예외 상황:**
    - `CHAT_SESSION_NOT_FOUND`: 유효하지 않은 chat_id
    - `CHAT_HISTORY_LOAD_ERROR`: 히스토리 조회 중 오류 발생

    **사용 예시:**
    - `GET /v1/chat/chat001/history`
    """,
)
def get_conversation_history(
    chat_id: str = Path(..., description="채팅방 고유 ID", example="chat001"),
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """대화 기록을 조회합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    history = llm_chat_service.get_conversation_history(chat_id)
    return ConversationHistoryResponse(history=history)

@router.post("/chat/{chat_id}/clear", response_model=ConversationClearedResponse)
def clear_conversation(
    chat_id: str,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """대화 기록을 초기화합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    llm_chat_service.clear_conversation(chat_id)
    return ConversationClearedResponse(message="대화 기록이 초기화되었습니다.")

@router.post("/chat/{chat_id}/cancel")
async def cancel_generation(
    chat_id: str,
    user_id: str = "user",
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """현재 생성 중인 AI 응답을 취소합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    success = await llm_chat_service.cancel_generation(chat_id, user_id)
    if success:
        return {"message": "AI 응답 생성이 취소되었습니다.", "cancelled": True}
    else:
        return {"message": "취소할 수 있는 생성이 없습니다.", "cancelled": False}

@router.post("/chat/chats", response_model=CreateChatResponse)
def create_chat(
    request: CreateChatRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """새로운 채팅을 생성합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    chat_id = llm_chat_service.create_chat(request.chat_title, request.user_id)
    chat_info = llm_chat_service.get_chat_info(chat_id)
    
    return CreateChatResponse(
        chat_id=chat_id,
        chat_title=request.chat_title,
        user_id=request.user_id,
        created_at=chat_info["created_at"]
    )


@router.get("/chat/chats", response_model=ChatListResponse)
def get_chats(
    user_id: str,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """사용자의 채팅 목록을 조회합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    chats = llm_chat_service.get_user_chats(user_id)
    return ChatListResponse(chats=chats)


@router.delete("/chat/chats/{chat_id}")
def delete_chat(
    chat_id: str,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """채팅을 삭제합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    success = llm_chat_service.delete_chat(chat_id)
    if success:
        return {"message": "채팅이 삭제되었습니다.", "deleted": True}
    else:
        return {"message": "채팅 삭제에 실패했습니다.", "deleted": False}


@router.put("/chat/chats/{chat_id}/title")
def update_chat_title(
    chat_id: str,
    new_title: str,
    user_id: str,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """채팅방 이름을 변경합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    success = llm_chat_service.update_chat_title(chat_id, new_title, user_id)
    if success:
        return {"message": "채팅방 이름이 변경되었습니다.", "success": True}
    else:
        return {"message": "채팅방 이름 변경에 실패했습니다.", "success": False}


@router.post("/chat/generate-title")
async def generate_chat_title(
    request: GenerateTitleRequest,
    llm_chat_service: LLMChatService = Depends(get_llm_chat_service)
):
    """메시지를 기반으로 채팅방 제목을 생성합니다."""
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리
    title = await llm_chat_service.generate_chat_title(request.message)
    return {"title": title}



