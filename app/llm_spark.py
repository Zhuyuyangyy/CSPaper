# -*- coding: utf-8 -*-
"""
星火大模型 LLM 调用层 (app/llm_spark.py)
=====================================
提供带有容灾能力的星火 API 调用：

1. Tenacity 指数退避重试 (3 次: 1s → 2s → 4s)
2. 全局兜底回复 (重试全败时返回)
3. 异步非阻塞预热 (不卡 FastAPI 启动)

Author: Alice 🌸
"""

from __future__ import annotations

import sys
import asyncio
import logging
from typing import Any, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

sys.path.append(r"C:\Users\联想\.openclaw\workspace")

# ==================== 日志 ====================
logger = logging.getLogger("LLM.Spark")

# ==================== 常量 ====================

# 预设兜底回复 (全败时返回)
FALLBACK_REPLY = "老中医正在闭目养神，请稍后再试 🌿"

# 兜底回复的 SSE 事件格式
FALLBACK_SSE_EVENT = {
    "event": "verdict",
    "data": {
        "verdict": "ERROR",
        "confidence": 0.0,
        "reason": FALLBACK_REPLY,
        "source": "llm_fallback",
    },
}


# ==================== Tenacity 重试配置 ====================

# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.NetworkError,
    httpx.RemoteProtocolError,
    ConnectionResetError,
    ConnectionError,
    TimeoutError,
)


# ==================== 核心 LLM 调用 ====================

class SparkLLM:
    """星火大模型调用器 (含容灾)"""

    def __init__(
        self,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        # 环境变量兜底
        import os

        self.app_id = app_id or os.getenv("SPARK_APP_ID", "")
        self.api_key = api_key or os.getenv("SPARK_API_KEY", "")
        self.api_secret = api_secret or os.getenv("SPARK_API_SECRET", "")
        self.api_url = api_url or os.getenv(
            "SPARK_API_URL",
            "wss://spark-api.xf-yun.com/v3.1/chat",
        )
        self._client: Optional[httpx.AsyncClient] = None

    # ---- 内部: 真正发起请求 ----

    async def _call_spark_api(
        self,
        messages: list[dict[str, str]],
        model: str = "general",
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        实际调用星火 WebSocket API (内部方法，带真实网络 I/O)。
        异常全部上抛，由装饰器捕获触发重试。
        """
        if not self.api_key:
            raise ConnectionError("SPARK_API_KEY is not configured")

        payload = {
            "header": {"app_id": self.app_id, "uid": "tcm_user"},
            "parameter": {
                "chat": {
                    "domain": model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_k": 6,
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {"role": m["role"], "content": m["content"]}
                        for m in messages
                    ]
                }
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.api_url.rstrip('/')}/chat",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("code") != 0:
                raise ConnectionError(
                    f"Spark API error: {result.get('message', 'unknown')}"
                )

            choices = result.get("payload", {}).get("choices", {})
            content = choices.get("text", [{}])[0].get("content", "")
            usage = result.get("payload", {}).get("usage", {})

            return {
                "content": content,
                "usage": usage,
                "model": model,
            }

    # ---- 对外: 带重试的异步调用 ----

    @staticmethod
    def _build_retry_decorator():
        """构建 tenacity 重试装饰器 (指数退避: 1s → 2s → 4s)"""
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "general",
        temperature: float = 0.5,
        max_tokens: int = 2048,
        use_fallback: bool = True,
    ) -> dict[str, Any]:
        """
        对外暴露的聊天接口。

        - 自动重试 3 次 (指数退避: 1s, 2s, 4s)
        - 全败 → 返回兜底回复 (use_fallback=True) 或重新抛出异常
        """
        retry_decorator = self._build_retry_decorator()

        # 把同步装饰器转成 async wrapper
        @retry_decorator
        async def _retry_call():
            return await self._call_spark_api(
                messages, model, temperature, max_tokens
            )

        try:
            return await _retry_call()
        except RETRYABLE_EXCEPTIONS as exc:
            if use_fallback:
                logger.error(
                    "Spark API 全败，返回兜底回复: %s", exc
                )
                return {
                    "content": FALLBACK_REPLY,
                    "usage": {},
                    "model": model,
                    "source": "fallback",
                }
            raise

    async def chat_raw(
        self,
        messages: list[dict[str, str]],
        model: str = "general",
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        不带兜底的原始调用 (外部已知风险时使用)。
        重试全败会直接抛异常。
        """
        retry_decorator = self._build_retry_decorator()

        @retry_decorator
        async def _retry_call():
            return await self._call_spark_api(
                messages, model, temperature, max_tokens
            )

        return await _retry_call()


# ==================== 模拟模式 (开发/演示用) ====================


class MockSparkLLM(SparkLLM):
    """
    模拟 LLM，固定返回假数据，用于本地开发和演示。
    可以注入人工延迟模拟网络慢/超时。
    """

    async def _call_spark_api(
        self,
        messages: list[dict[str, str]],
        model: str = "general",
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        import random
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # 断网信号检测 (共享全局事件)
        if _network_outage.is_set():
            raise httpx.ConnectError("Simulated network outage")

        last_msg = messages[-1]["content"] if messages else ""

        return {
            "content": f"【Mock回复】收到: {last_msg[:30]}... (模拟)",
            "usage": {"prompt_tokens": 50, "completion_tokens": 30},
            "model": model,
            "source": "mock",
        }


# ==================== 单例 & 工厂 ====================

# 全局 LLM 实例 (懒加载)
_llm_instance: Optional[SparkLLM] = None
_mock_mode = False

# ---- 断网模拟信号 (供 Mock 和测试共享) ----
_network_outage = asyncio.Event()   # set() = 断网中, clear() = 正常
_patch_guard = asyncio.Lock()       # 确保 patch/unpatch 原子操作


def set_mock_mode(enabled: bool = True):
    """切换 Mock 模式 (开发/测试用)"""
    global _mock_mode, _llm_instance
    _mock_mode = enabled
    _llm_instance = None  # 重置以便下次取到正确的类


def get_llm() -> SparkLLM:
    """获取 LLM 单例，自动适配 Mock 或真实模式"""
    global _llm_instance
    if _llm_instance is None:
        if _mock_mode:
            _llm_instance = MockSparkLLM()
        else:
            _llm_instance = SparkLLM()
    return _llm_instance


# ==================== 异步预热 (不卡 FastAPI 启动) ====================


async def warmup_llm(background: bool = True):
    """
    异步预热 LLM API。

    Args:
        background: True → 在后台任务中预热，不阻塞启动
                    False → 同步等待预热完成 (仅启动时使用)
    """
    llm = get_llm()

    if background:
        # 后台预热，不阻塞 FastAPI 启动
        asyncio.create_task(_do_warmup(llm))
        logger.info("LLM 预热任务已后台启动")
    else:
        # 同步预热 (仅首次)
        await _do_warmup(llm)


async def _do_warmup(llm: SparkLLM):
    """实际执行预热 (发一个简单请求激活连接池)"""
    try:
        logger.info("LLM 预热中...")
        # 发一个最小化请求探活
        await llm.chat(
            messages=[{"role": "user", "content": "你好"}],
            use_fallback=True,
        )
        logger.info("LLM 预热完成 ✓")
    except Exception as e:
        # 预热失败不影响启动，记录即可
        logger.warning("LLM 预热失败 (不影响主服务): %s", e)


# ==================== 便捷工具函数 ====================


async def chat_with_fallback(
    messages: list[dict[str, str]],
    model: str = "general",
) -> dict[str, Any]:
    """
    一行调用: 带重试 + 兜底的聊天接口。
    推荐在 Agent 内部使用。
    """
    return await get_llm().chat(messages=messages, model=model)


def get_fallback_sse_event() -> dict[str, Any]:
    """返回兜底回复的 SSE 事件格式 (dict)"""
    return FALLBACK_SSE_EVENT.copy()


# ==================== 自检 / 模拟断网测试 ====================

async def simulate_network_outage(duration_seconds: float = 2.0):
    """
    模拟断网 N 秒的场景 (设置全局 _network_outage Event)。
    MockSparkLLM 会主动检测此事件并抛出 ConnectError。
    仅用于测试环境！
    """
    logger.info("断网模拟开始 (%ds)...", duration_seconds)
    _network_outage.set()          # 广播断网信号
    await asyncio.sleep(duration_seconds)
    _network_outage.clear()       # 恢复网络
    logger.info("网络恢复 (断网 %ds 结束)", duration_seconds)


async def self_test():
    """手动自检: 模拟断网 2 秒，验证重试 + 兜底逻辑"""
    print("\n" + "=" * 60)
    print("  LLM Resilience Self-Test (simulating 2s network outage)")
    print("=" * 60)

    # 启用 Mock 模式
    set_mock_mode(enabled=True)
    llm = get_llm()

    # 断网 8s > 所有重试间隔总和 (1+2+4=7s)，确保 3 次全败
    print("\n[Step 1] Simulating 8s network outage ...")
    asyncio.create_task(simulate_network_outage(8.0))

    # 稍等 0.5s 确保断网已注入
    await asyncio.sleep(0.5)

    print("[Step 2] Triggering LLM call (expect retries then fallback) ...")
    result = await llm.chat(
        messages=[{"role": "user", "content": "黄连能治感冒吗？"}],
        use_fallback=True,
    )

    print(f"\nResult  : {result['content']}")
    print(f"Source  : {result.get('source', 'unknown')}")
    print(f"Model  : {result.get('model', 'unknown')}")

    # 验证: 经历了断网 + 重试 + 兜底
    assert "老中医正在闭目养神" in result["content"], \
        f"Fallback reply mismatch! Got: {result['content']}"
    assert result.get("source") == "fallback", \
        f"Expected source=fallback, got: {result.get('source')}"

    print("\n[PASS] Retries + Fallback logic verified!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(self_test())
