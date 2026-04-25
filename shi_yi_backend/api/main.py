"""
FastAPI 后端 - 史易枢机 6-Bit FSM 分析引擎
前后端分离架构 API 层
"""

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.llm.chain import IChingChain
from src.db.faiss_client import FAISSIChingClient


# =============================================================================
# 启动与关闭
# =============================================================================

# 全局单例，避免重复初始化
_chain: IChingChain | None = None
_db_client: FAISSIChingClient | None = None


def get_chain() -> IChingChain:
    global _chain
    if _chain is None:
        _chain = IChingChain()
    return _chain


def get_db_client() -> FAISSIChingClient:
    global _db_client
    if _db_client is None:
        _db_client = FAISSIChingClient()
        _db_client.connect()
    return _db_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时预热
    print("[INFO] 初始化 Chain 和 DB Client...")
    get_chain()
    try:
        get_db_client()
    except Exception as e:
        print(f"[WARNING] DB 连接失败: {e}")
    yield
    # 关闭时清理
    global _chain, _db_client
    _chain = None
    _db_client = None


# =============================================================================
# FastAPI 应用
# =============================================================================

app = FastAPI(
    title="史易枢机 API",
    description="6-Bit FSM 历史事件分析引擎",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件 - 允许 localhost:5173 (Vite 开发服务器)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 请求/响应模型
# =============================================================================

class InferRequest(BaseModel):
    query: str = Field(..., description="用户输入的历史事件", min_length=1)


class RetrievalResultItem(BaseModel):
    """检索结果项"""
    hexagram_name: str | None = None
    text_type: str | None = None
    context: str | None = None
    content: str | None = None
    distance: float | None = None

    class Config:
        extra="allow"


class BitAnalysisItem(BaseModel):
    """Bit 分析项"""
    bit_position: int
    value: str
    description: str


class EnergyFocusItem(BaseModel):
    """能量聚焦"""
    focus_bit: int
    focus_description: str


class StressAnalysisItem(BaseModel):
    """受力分析"""
    stress_type: str
    analysis: str


class FSMAnalysis(BaseModel):
    """FSM 分析结果"""
    inner_system: str
    outer_system: str
    inner_bits: str
    outer_bits: str
    bit_analysis: list[BitAnalysisItem]
    energy_focus: EnergyFocusItem
    stress_analysis: StressAnalysisItem
    mutation_suggestion: str
    target_hexagram: str
    hexagram_reason: str
    referenced_yao: str
    yao_interpretation: str


class InferResponse(BaseModel):
    """POST /api/infer 响应"""
    fsm_analysis: FSMAnalysis
    retrieval_results: list[RetrievalResultItem]


# =============================================================================
# 工具函数
# =============================================================================

def _serialize_fsm(fsm) -> dict[str, Any]:
    """将 FSMOutput 序列化为可 JSON 化的字典"""
    return {
        "inner_system": fsm.inner_system,
        "outer_system": fsm.outer_system,
        "inner_bits": fsm.inner_bits,
        "outer_bits": fsm.outer_bits,
        "bit_analysis": [
            {
                "bit_position": b.bit_position,
                "value": b.value,
                "description": b.description,
            }
            for b in fsm.bit_analysis
        ] if fsm.bit_analysis else [],
        "energy_focus": {
            "focus_bit": fsm.energy_focus.focus_bit,
            "focus_description": fsm.energy_focus.focus_description,
        },
        "stress_analysis": {
            "stress_type": fsm.stress_analysis.stress_type,
            "analysis": fsm.stress_analysis.analysis,
        },
        "mutation_suggestion": fsm.mutation_suggestion,
        "target_hexagram": fsm.target_hexagram,
        "hexagram_reason": fsm.hexagram_reason,
        "referenced_yao": fsm.referenced_yao,
        "yao_interpretation": fsm.yao_interpretation,
    }


def _serialize_retrieval(results: list[dict]) -> list[dict]:
    """序列化检索结果，兼容不同字段名"""
    serialized = []
    for r in results:
        serialized.append({
            "hexagram_name": r.get("hexagram_name"),
            "text_type": r.get("text_type"),
            "context": r.get("context", r.get("content", "")),
            "content": r.get("content", r.get("context", "")),
            "distance": r.get("distance"),
        })
    return serialized


# =============================================================================
# 路由
# =============================================================================

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.post("/api/infer", response_model=InferResponse)
def infer(req: InferRequest):
    """
    核心推理接口

    接收用户输入，调用 IChingChain.run()，返回 FSM 分析结果和检索结果。
    """
    try:
        chain = get_chain()
        fsm_result, retrieval = chain.run(req.query)

        return InferResponse(
            fsm_analysis=FSMAnalysis(**_serialize_fsm(fsm_result)),
            retrieval_results=[RetrievalResultItem(**r) for r in _serialize_retrieval(retrieval)],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
