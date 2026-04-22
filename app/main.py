# -*- coding: utf-8 -*-
"""
FastAPI Application Entry Point
================================
TCM Knowledge Q&A System with SSE Streaming

Author: Alice 🌸
"""

import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 添加项目路径
sys.path.append(r'C:\Users\联想\.openclaw\workspace')

# 路由
from app.routers import chat
from app.routers.paper import generate as paper_generate
from app.llm_minimax import warmup_llm, set_mock_mode

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TCMApp")


# ==================== 生命周期 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("=" * 50)
    logger.info("  TCM Knowledge Q&A System Starting...")
    logger.info("  Version: 1.0.0")
    logger.info("  SSE Endpoint: /api/chat/stream")
    logger.info("=" * 50)

    # ---- 非阻塞 LLM 预热 ----
    # 后台运行，不卡 FastAPI 启动
    await warmup_llm(background=True)

    yield  # 应用运行中
    
    logger.info("TCM System Shutting Down...")


# ==================== FastAPI 应用 ====================
app = FastAPI(
    title="TCM Knowledge Q&A System",
    description="""
## 中医知识问答系统 (TCM Q&A)

### 核心功能
- 🌸 **多Agent协作**: 画像构建 + 图谱校验 + 老中医批判
- 📊 **SSE流式输出**: 实时推送思考过程、校验结果、3D资源
- 🎯 **3D可视化**: Three.js 人体穴位高亮 + 经络游走动画
- 🧓 **老中医风格**: 严格的置信度审核，引经据典

### SSE 事件类型
| 事件 | 说明 |
|------|------|
| `thought` | Agent思考中 (进度推送) |
| `fact_check` | 图谱校验结果 |
| `critique` | 老中医批判反馈 |
| `resource_3d` | 3D穴位资源 |
| `verdict` | 最终判定 |
| `heartbeat` | 心跳保活 |
| `complete` | 完成 |
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ==================== 中间件 ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 挂载路由 ====================
app.include_router(chat.router)
app.include_router(paper_generate.router)


# ==================== 静态文件 ====================
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    logger.info("Static files mounted at /static")
except Exception as e:
    logger.warning(f"Static files not mounted: {e}")


# ==================== 根路径 ====================
@app.get("/", tags=["root"])
async def root():
    """系统根路径"""
    return {
        "name": "Paper Generation System",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "paper_generate": "/api/paper/generate/outline",
            "paper_export": "/api/paper/export",
            "health": "/api/chat/health"
        }
    }


@app.get("/health", tags=["health"])
async def health():
    """健康检查"""
    return {"status": "ok"}


# ==================== 启动入口 ====================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
