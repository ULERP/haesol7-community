"""LLM 기반 에이전트 유틸리티"""

import openai
from django.conf import settings
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)

# LLM API 설정
try:
    if settings.LLM_PROVIDER == 'openai' and settings.OPENAI_API_KEY:
        openai.api_key = settings.OPENAI_API_KEY
    elif settings.LLM_PROVIDER == 'anthropic' and settings.ANTHROPIC_API_KEY:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
except Exception as e:
    logger.warning(f"LLM API 설정 실패: {e}")


class LLMPersona:
    """AI 페르소나 정의"""
    
    PERSONAS = {
        '다정한 이웃': {
            'name': '다정한 이웃',
            'tone': '따뜻하고 친절한',
            'style': '존댓글, 정중한 표현',
            'emoji': '😊',
        },
        '자랑스러운 이웃': {
            'name': '자랑스러운 이웃',
            'tone': '축하하고 응원하는',
            'style': '긍정적, 격려적 표현',
            'emoji': '🌟',
        },
        '따뜻한 동네': {
            'name': '따뜻한 동네',
            'tone': '따뜻하고 포용적인',
            'style': '공동체 지향적',
            'emoji': '🏘️',
        },
        '정보 도우미': {
            'name': '정보 도우미',
            'tone': '친절하고 전문적인',
            'style': '명확하고 쉬운 설명',
            'emoji': '📚',
        },
    }
    
    @classmethod
    def get_system_prompt(cls, persona_name: str) -> str:
        """페르소나별 시스템 프롬프트 생성"""
        persona = cls.PERSONAS.get(persona_name, cls.PERSONAS['다정한 이웃'])
        
        return f"""
당신은 아파트 커뮤니티의 '{persona_name}'입니다.
성격: {persona['tone']}
표현 스타일: {persona['style']}

주의사항:
1. 항상 한국어로 친근하게 대답하세요
2. 주민들이 편하게 느낄 수 있도록 합니다
3. 길지 않게 간결하게 작성하세요 (2-3문장)
4. 이모지를 적절히 활용하세요
5. 공식적이지 않되, 존중하는 말투를 유지하세요
"""


class NotificationGenerator:
    """알림 메시지 자동 생성"""
    
    @staticmethod
    def generate_activity_notification(
        activity_name: str,
        points: int,
        persona: str = '다정한 이웃'
    ) -> str:
        """활동 승인 알림 생성"""
        
        try:
            if settings.LLM_PROVIDER == 'openai' and settings.OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": LLMPersona.get_system_prompt(persona)
                        },
                        {
                            "role": "user",
                            "content": f"'{activity_name}' 활동이 승인되었고 {points}포인트를 획득했습니다. 이를 축하하는 메시지를 만들어주세요."
                        }
                    ],
                    temperature=0.7,
                    max_tokens=100,
                    timeout=5
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM 활동 알림 생성 실패: {e}")
        
        # Fallback: 템플릿 메시지
        return f"축하합니다! '{activity_name}' 활동이 승인되었어요! 💪 +{points}P 적립되었습니다!"
    
    @staticmethod
    def generate_badge_notification(
        badge_title: str,
        persona: str = '자랑스러운 이웃'
    ) -> str:
        """배지 획득 알림 생성"""
        
        try:
            if settings.LLM_PROVIDER == 'openai' and settings.OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": LLMPersona.get_system_prompt(persona)
                        },
                        {
                            "role": "user",
                            "content": f"사용자가 '{badge_title}' 배지를 획득했습니다. 축하 메시지를 만들어주세요."
                        }
                    ],
                    temperature=0.7,
                    max_tokens=100,
                    timeout=5
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"LLM 배지 알림 생성 실패: {e}")
        
        return f"🏅 축하합니다! '{badge_title}' 배지를 획득하셨어요! 앞으로도 활동을 응원합니다!"


class RAGChatbot:
    """RAG 기반 규약 안내 챗봇"""
    
    @staticmethod
    def answer_question(question: str, documents: List[dict]) -> tuple[str, float]:
        """
        관리 규약 문서를 기반으로 질문에 답변
        
        Returns:
            (답변, 신뢰도)
        """
        
        try:
            # 문서 컨텍스트 구성
            context = "\n".join([
                f"[{doc['category']}]\n{doc['content']}"
                for doc in documents[:3]  # 상위 3개 문서만 사용
            ])
            
            if settings.LLM_PROVIDER == 'openai' and settings.OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": LLMPersona.get_system_prompt('정보 도우미')
                        },
                        {
                            "role": "user",
                            "content": f"""
다음 아파트 관리 규약을 참고하여 질문에 답변해주세요.

[관리 규약]
{context}

[질문]
{question}

- 규약에 없는 내용이면 "규약에 명시되지 않아 관리사무소에 문의하시길 권장합니다"라고 답변하세요
- 명확한 근거가 있으면 신뢰도 점수를 높여주세요
"""
                        }
                    ],
                    temperature=0.5,
                    max_tokens=200,
                    timeout=10
                )
                
                answer = response.choices[0].message.content
                confidence = 0.85  # OpenAI 답변은 높은 신뢰도
                
                return answer, confidence
        except Exception as e:
            logger.warning(f"RAG 챗봇 오류: {e}")
        
        # Fallback
        return "해당 내용에 대해 관리사무소에 문의하시길 권장합니다.", 0.5


class CertificateGenerator:
    """자동 감사장 생성"""
    
    @staticmethod
    def generate_certificate(
        user_name: str,
        activities: List[str],
        total_hours: float,
        badges: List[str]
    ) -> dict:
        """
        연말 감사장 데이터 생성
        
        Returns:
            감사장 정보 dict (PDF 생성용)
        """
        
        certificate_data = {
            'recipient_name': user_name,
            'issue_date': '2025년 12월 31일',
            'activities': activities,
            'total_hours': total_hours,
            'badges': badges,
            'message': f"""
{user_name} 주민께

올해 한 해 동안 우리 아파트의 안전하고 쾌적한 환경을 위해
끊임없는 봉사와 배려로 함께해주셨습니다.

귀하의 노고에 진심으로 감사드리며,
새로운 한 해에도 변함없는 관심과 참여를 부탁드립니다.

해솔7 아파트 커뮤니티 일동
"""
        }
        
        return certificate_data
