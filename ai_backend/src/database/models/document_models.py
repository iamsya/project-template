# _*_ coding: utf-8 _*_
"""
Document Models - shared_core에서 re-export
ai_backend는 shared_core의 Document 모델을 사용합니다.
programs-document 외래키는 포기하고, 다른 테이블들이 Document를 참조할 수 있도록 shared_core 사용
"""
# shared_core의 Document 모델들을 re-export
from shared_core.models import Document, DocumentChunk, ProcessingJob

# 기존 코드와의 호환성을 위한 별칭들
DocumentMetadata = Document

__all__ = [
    "Document",
    "DocumentChunk", 
    "ProcessingJob",
    "DocumentMetadata",
]
