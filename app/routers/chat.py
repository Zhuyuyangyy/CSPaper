# -*- coding: utf-8 -*-
"""
FastAPI SSE Router - Chat with Multi-Channel Streaming
=====================================================
支持多类型事件流式推送：
- thought: Agent思考中
- fact_check: 图谱校验分数
- critique: 老中医反馈
- resource_3d: 3D穴位资源
- verdict: 最终判定
"""

import sys
import json
import asyncio
import logging
from typing import AsyncGenerator, Optional, Any
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# 尝试导入，如果不存在则创建简化版
try:
    from sse_starlette import SSE
except ImportError:
    SSE = None

sys.path.append(r'C:\Users\联想\.openclaw\workspace')

from app.agents.critique_agent import CritiqueAgent
from app.agents.resource_generator import ResourceGenerator
from app.agents.profile_builder import ProfileBuilder
from app.rag.graph_service import GraphRAGService

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("ChatRouter")

# ==================== 事件类型枚举 ====================
class SSEEventType(str, Enum):
    """SSE事件类型"""
    THINKING = "thought"           # Agent思考中
    FACT_CHECK = "fact_check"      # 图谱校验
    CRITIQUE = "critique"          # 老中医批判
    RESOURCE_3D = "resource_3d"    # 3D资源
    VERDICT = "verdict"            # 最终判定
    ERROR = "error"                # 错误
    COMPLETE = "complete"          # 完成
    HEARTBEAT = "heartbeat"        # 心跳保活


# ==================== 请求/响应模型 ====================
class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    user_id: str = Field(default="anonymous", description="用户ID")
    enable_3d: bool = Field(default=True, description="是否启用3D资源")
    enable_critique: bool = Field(default=True, description="是否启用老中医批判")
    conversation_history: list[dict] = Field(default_factory=list, description="对话历史")


class SSEEvent(BaseModel):
    """SSE事件模型"""
    event: str = Field(..., description="事件类型")
    data: Any = Field(..., description="事件数据")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[str] = Field(default=None, description="事件ID")


# ==================== SSE 事件流生成器 ====================
class TCMEventStream:
    """中医问答事件流"""
    
    def __init__(self, request: ChatRequest):
        self.request = request
        self.critique_agent = CritiqueAgent()
        self.resource_generator = ResourceGenerator()
        self.profile_builder = ProfileBuilder()
        self.graph_service = GraphRAGService()
        
        # 加载图谱数据
        try:
            self.graph_service.load_from_json()
        except Exception:
            pass
        
        self.event_id = 0
    
    def _next_id(self) -> str:
        """生成事件ID"""
        self.event_id += 1
        return f"evt_{self.event_id}_{int(datetime.now().timestamp())}"
    
    async def _emit(
        self,
        event_type: SSEEventType,
        data: Any,
        retry: int = 3000
    ) -> dict:
        """生成SSE事件"""
        return {
            "event": event_type.value,
            "data": json.dumps(data, ensure_ascii=False),
            "id": self._next_id(),
            "retry": retry
        }
    
    async def _send_thinking(self, thought: str, progress: float = 0.0):
        """发送思考事件"""
        return await self._emit(SSEEventType.THINKING, {
            "thought": thought,
            "progress": progress,
            "stage": self._get_stage(progress)
        })
    
    def _get_stage(self, progress: float) -> str:
        """根据进度获取阶段名"""
        stages = {
            0.1: "理解问题",
            0.25: "构建画像",
            0.4: "图谱校验",
            0.55: "老中医审核",
            0.7: "生成3D资源",
            0.85: "综合判断",
            0.95: "生成回复"
        }
        for threshold, name in sorted(stages.items()):
            if progress <= threshold:
                return name
        return "完成"
    
    async def generate_stream(self) -> AsyncGenerator[dict, None]:
        """生成事件流"""
        message = self.request.message
        
        # ===== Stage 1: 理解问题 =====
        yield await self._send_thinking("正在理解您的问题...", 0.05)
        await asyncio.sleep(0.3)
        
        # ===== Stage 2: 解析意图 =====
        yield await self._send_thinking("正在解析中医语义...", 0.15)
        profile = self.profile_builder.build(message, self.request.user_id)
        await asyncio.sleep(0.2)
        
        # 发送画像结果
        yield await self._emit(SSEEventType.THINKING, {
            "type": "profile",
            "data": profile.to_dict(),
            "progress": 0.2
        })
        
        # ===== Stage 3: 图谱校验 =====
        yield await self._send_thinking("正在检索知识图谱...", 0.3)
        await asyncio.sleep(0.3)
        
        # 解析声明进行校验
        claim = self._extract_claim(message)
        if claim:
            graph_result = self._verify_claim(claim)
            
            yield await self._emit(SSEEventType.FACT_CHECK, {
                "claim": claim,
                "confidence": graph_result.get("confidence", 0.0),
                "verdict": graph_result.get("verdict", "UNCERTAIN"),
                "reason": graph_result.get("reason", ""),
                "levels_passed": graph_result.get("levels_passed", 0),
                "progress": 0.4
            })
            
            # ===== Stage 4: 老中医批判 =====
            if self.request.enable_critique and graph_result.get("confidence", 1.0) < 0.7:
                yield await self._send_thinking("老中医正在审核...", 0.5)
                
                critique_result = self.critique_agent.critique(
                    claim=claim,
                    confidence=graph_result.get("confidence", 0.0),
                    graph_result=graph_result
                )
                
                yield await self._emit(SSEEventType.CRITIQUE, {
                    "verdict": critique_result["verdict"],
                    "confidence": critique_result["confidence"],
                    "critique_text": critique_result["critique"],
                    "classic_quote": critique_result.get("classic_quote", ""),
                    "correct_treatment": critique_result.get("correct_treatment", ""),
                    "progress": 0.6
                })
                
                # 如果被拒绝，生成3D资源帮助用户理解
                if critique_result["verdict"] == "REJECT" and self.request.enable_3d:
                    async for event in self._generate_3d_resources(claim, critique_result):
                        yield event
            else:
                # 通过校验，给出正面反馈
                yield await self._emit(SSEEventType.CRITIQUE, {
                    "verdict": "ACCEPT",
                    "confidence": graph_result.get("confidence", 0.8),
                    "critique_text": f"善！此言深合医理。吾已验证图谱，正统无误。",
                    "progress": 0.65
                })
        
        # ===== Stage 5: 生成3D资源 =====
        if self.request.enable_3d:
            async for event in self._generate_3d_resources_for_symptoms(message):
                yield event
        
        # ===== Stage 6: 最终判定 =====
        yield await self._send_thinking("综合判断中...", 0.9)
        await asyncio.sleep(0.2)
        
        final_verdict = self._generate_final_verdict(profile, claim if 'claim' in locals() else None)
        yield await self._emit(SSEEventType.VERDICT, {
            "summary": final_verdict["summary"],
            "syndromes": final_verdict.get("syndromes", []),
            "recommendations": final_verdict.get("recommendations", []),
            "is_rejected": final_verdict.get("is_rejected", False),
            "progress": 0.95
        })
        
        # ===== Complete =====
        yield await self._emit(SSEEventType.COMPLETE, {
            "message": "问答完成",
            "timestamp": datetime.now().isoformat()
        })
    
    async def _generate_3d_resources(self, claim: str, critique_result: dict) -> dict:
        """为声明生成3D资源"""
        # 尝试从声明中提取穴位
        point = self._extract_point(claim)
        if point:
            yield await self._emit(SSEEventType.THINKING, {
                "thought": f"正在生成{point}的3D定位数据...",
                "progress": 0.7
            })
            
            try:
                resource_json = self.resource_generator.generate_json(
                    target=point,
                    treatment="针刺",
                    disease=""
                )
                resource_data = json.loads(resource_json)
                
                yield await self._emit(SSEEventType.RESOURCE_3D, {
                    "type": "acupoint",
                    "point_code": point,
                    "point_name": resource_data.get("point_name", ""),
                    "coords": resource_data.get("coords", []),
                    "meridian_path": resource_data.get("meridian_path", []),
                    "meridian_name": resource_data.get("meridian_name", ""),
                    "animation_desc": resource_data.get("animation_desc", ""),
                    "anatomy_note": resource_data.get("anatomy_note", ""),
                    "stimulation": resource_data.get("stimulation", ""),
                    "threejs_ready": True,
                    "progress": 0.75
                })
            except Exception as e:
                logger.warning(f"3D resource generation failed: {e}")
    
    async def _generate_3d_resources_for_symptoms(self, message: str) -> dict:
        """为症状生成3D资源"""
        yield await self._send_thinking("正在生成穴位3D模型...", 0.8)
        
        # 根据证型推荐穴位
        syndrome_tips = {
            "热证": ["LI4", "LI11", "DU14"],
            "寒证": ["RN4", "RN6", "DU4"],
            "湿邪": ["SP9", "ST40", "RN9"],
            "气虚": ["RN6", "ST36", "SP6"],
            "血虚": ["SP10", "ST36", "KI3"],
        }
        
        # 简单匹配
        for syndrome, points in syndrome_tips.items():
            if syndrome in message or any(p in message for p in ["火", "热", "干"]):
                for point in points[:1]:  # 只选一个主要穴位
                    try:
                        resource_json = self.resource_generator.generate_json(
                            target=point,
                            treatment="按摩",
                            disease=syndrome
                        )
                        resource_data = json.loads(resource_json)
                        
                        yield await self._emit(SSEEventType.RESOURCE_3D, {
                            "type": "acupoint_recommendation",
                            "for_syndrome": syndrome,
                            **resource_data,
                            "progress": 0.85
                        })
                    except Exception:
                        pass
                break
    
    def _extract_claim(self, message: str) -> Optional[str]:
        """从消息中提取声明"""
        # 简单模式匹配
        patterns = [
            r"(.+?)(可以|能|可|能治|主治)(.+)",
            r"(.+?)(性|味|归经|功效)(.+)",
            r"(.+?)(治疗|主治)(.+)",
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return message.strip()
        
        return None
    
    def _extract_point(self, text: str) -> Optional[str]:
        """从文本中提取穴位"""
        known_points = {
            "合谷": "LI4", "足三里": "ST36", "百会": "DU20",
            "涌泉": "KI1", "太溪": "KI3", "三阴交": "SP6",
            "关元": "RN4", "气海": "RN6", "中脘": "RN12",
        }
        
        for name, code in known_points.items():
            if name in text:
                return code
        
        return None
    
    def _verify_claim(self, claim: str) -> dict:
        """校验声明"""
        try:
            return self.graph_service.verify_fact(claim)
        except Exception as e:
            logger.error(f"Graph verification error: {e}")
            return {
                "verdict": "UNCERTAIN",
                "confidence": 0.5,
                "reason": f"图谱校验异常: {str(e)}",
                "levels_passed": 0
            }
    
    def _generate_final_verdict(self, profile, claim: Optional[str]) -> dict:
        """生成最终判定"""
        result = {
            "summary": profile.generate_summary() if hasattr(profile, 'generate_summary') else "综合分析完成",
            "syndromes": [],
            "recommendations": [],
            "is_rejected": False
        }
        
        if hasattr(profile, 'syndromes'):
            result["syndromes"] = [s["type"] for s in profile.syndromes[:3]]
        
        if hasattr(profile, 'tips'):
            result["recommendations"] = profile.tips[:3]
        
        return result


# ==================== SSE 心跳保持 ====================
async def heartbeat_generator():
    """心跳生成器，防止连接断开"""
    while True:
        yield {
            "event": SSEEventType.HEARTBEAT.value,
            "data": json.dumps({"timestamp": datetime.now().isoformat()}),
            "id": f"hb_{int(datetime.now().timestamp())}",
            "retry": 5000
        }
        await asyncio.sleep(5)


# ==================== API 端点 ====================
@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    聊天流式接口 - SSE
    
    事件类型:
    - thought: Agent思考过程
    - fact_check: 图谱校验结果
    - critique: 老中医批判
    - resource_3d: 3D穴位资源
    - verdict: 最终判定
    - heartbeat: 心跳保活
    - complete: 完成
    - error: 错误
    """
    
    async def event_generator():
        stream = TCMEventStream(request)
        
        # 并行运行主事件流和心跳
        main_task = None
        
        try:
            # 创建主事件流任务
            main_task = asyncio.create_task(stream.generate_stream().__anext__())
            
            while True:
                # 等待任一任务完成
                done, pending = await asyncio.wait(
                    [main_task, asyncio.create_task(asyncio.sleep(0.05))],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if main_task in done:
                    try:
                        event = main_task.result()
                        if event is None:
                            break
                        
                        # 确保输出是有效的SSE格式
                        if isinstance(event, dict) and "event" in event:
                            yield event
                        
                        # 检查是否完成
                        if event.get("event") in [SSEEventType.COMPLETE.value, "complete"]:
                            break
                        
                        # 获取下一个事件
                        main_task = asyncio.create_task(stream.generate_stream().__anext__())
                        
                    except StopAsyncIteration:
                        break
                    except Exception as e:
                        logger.error(f"Stream error: {e}")
                        yield {
                            "event": "error",
                            "data": json.dumps({"error": str(e)}),
                            "id": f"err_{int(datetime.now().timestamp())}"
                        }
                        break
                
                # 定期发送心跳
                yield {
                    "event": SSEEventType.HEARTBEAT.value,
                    "data": json.dumps({"timestamp": datetime.now().isoformat()}),
                    "id": f"hb_{int(datetime.now().timestamp())}",
                    "retry": 5000
                }
                
        except asyncio.CancelledError:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
                "id": f"err_{int(datetime.now().timestamp())}"
            }
        finally:
            if main_task and not main_task.done():
                main_task.cancel()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept",
        }
    )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ==================== 简化版流式响应 ====================
@router.post("/simple-stream")
async def simple_chat_stream(request: ChatRequest):
    """
    简化版聊天流 - 使用轮询而非SSE
    适用于不支持SSE的环境
    """
    # 生成所有事件
    stream = TCMEventStream(request)
    events = []
    
    async for event in stream.generate_stream():
        events.append(event)
    
    return JSONResponse({
        "events": events,
        "request": request.message,
        "timestamp": datetime.now().isoformat()
    })
