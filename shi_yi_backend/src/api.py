"""
史易枢机 — FastAPI 服务 (V11.0 离散自动机版)
/api/infer       : LLM 分析 + V11.0 确定性硬算
/api/simulate    : 6 种 Bit Flip 预览
/api/evolve      : 确定性演化（指定路径或自动路由）
/api/node        : 查询当前节点信息
"""

from __future__ import annotations

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from src.models.schema import FSMOutput, FSMNode, DeterministicResult
from src.fsm_kernel import (
    FSMKernel,
    FSMState,
    get_hexagram_name,
    get_hex_state,
    discrete_entropy,
    max_stress_trigger,
    route_evolution_path,
    simulate_all_flips,
    flip_bit,
    path1_max_stress,
    path2_hidden_core_exposure,
    path3_macro_entropy_decay,
    path4_meta_reset_or_invert,
    conf_m1,
    compute_system_confidence,
    MONTE_CARLO_N,
)
from src.llm.chain import IChingChain

app = FastAPI(title="史易枢机 V11.0", version="11.0.0")

# =============================================================================
# 请求/响应模型
# =============================================================================

class SimulateRequest(BaseModel):
    bits: str = Field(..., description="6位代码，如 '111000'")
    E0: float = Field(default=1.0, description="初始能量储备")
    P0: float = Field(default=0.0, description="初始压强")


class EvolveRequest(BaseModel):
    bits: str = Field(..., description="6位代码")
    path: Optional[int] = Field(default=None, description="演化路径 1/2/3/4，None=自动路由")
    delta_E_ext: float = Field(default=0.0, description="外部能量注入率")
    deadlock_flag: bool = Field(default=False, description="死锁标志位")
    time_in_state: int = Field(default=0, description="在当前状态的停留时间")


# =============================================================================
# 辅助函数
# =============================================================================

def state_to_fsm_node(state: FSMState) -> FSMNode:
    """FSMState → FSMNode"""
    hex_index, physics_name, physics_desc = get_hex_state(state)
    hexagram = get_hexagram_name(state.inner_bits(), state.outer_bits())
    return FSMNode(
        index=hex_index,
        name=hexagram,
        code=state.full_bits(),
        physics_description=physics_desc or physics_name,
        entropy_S=discrete_entropy(state),
        mass_M=state.mass_M(),
    )


def build_deterministic_result(state: FSMState,
                                delta_E_ext: float = 0.0,
                                deadlock_flag: bool = False,
                                time_in_state: int = 0) -> DeterministicResult:
    """从当前状态构建完整的 V2.0 确定性硬算结果"""
    hex_index, physics_name, physics_desc = get_hex_state(state)
    hexagram = get_hexagram_name(state.inner_bits(), state.outer_bits())
    current_node = FSMNode(
        index=hex_index,
        name=hexagram,
        code=state.full_bits(),
        physics_description=physics_desc or physics_name,
        entropy_S=discrete_entropy(state),
        mass_M=state.mass_M(),
    )

    # Max-stress trigger (V11.0: no t parameter)
    focus_bit, stress_type = max_stress_trigger(state)

    # 路由判定
    route = route_evolution_path(state, delta_E_ext, deadlock_flag, time_in_state)
    path_number = route["path_number"]
    path_name = route["path_name"]

    # 所有可能翻转
    flips = simulate_all_flips(state)
    all_moves = []
    next_state_node = None

    if path_number == 1:
        r = route["result"]
        all_moves = [
            FSMNode(
                index=r_i.get("hex_index", 0),
                name=r_i.get("hexagram", ""),
                code=r_i.get("new_bits", ""),
                physics_description=r_i.get("physics_desc", ""),
                entropy_S=r_i.get("entropy_S", 0.0),
                mass_M=sum(int(b) for b in r_i.get("new_bits", "000000")),
            )
            for r_i in flips
        ]
        next_state_node = FSMNode(
            index=r.get("hex_index", 0),
            name=r.get("next_hexagram", ""),
            code=r.get("next_bits", ""),
            physics_description=r.get("physics_desc", ""),
            entropy_S=r.get("entropy_S", 0.0),
            mass_M=r.get("next_state", state).mass_M() if r.get("next_state") else 0,
        )

    elif path_number == 2:
        r = route["result"]
        ns = r.get("next_state")
        all_moves = [
            FSMNode(
                index=r_i.get("hex_index", 0),
                name=r_i.get("hexagram", ""),
                code=r_i.get("new_bits", ""),
                physics_description=r_i.get("physics_desc", ""),
                entropy_S=r_i.get("entropy_S", 0.0),
                mass_M=sum(int(b) for b in r_i.get("new_bits", "000000")),
            )
            for r_i in flips
        ]
        if ns:
            next_state_node = FSMNode(
                index=r.get("hex_index", 0),
                name=r.get("next_hexagram", ""),
                code=r.get("next_bits", ""),
                physics_description=r.get("physics_desc", ""),
                entropy_S=r.get("entropy_S", 0.0),
                mass_M=ns.mass_M(),
            )

    elif path_number == 3:
        chain = route["result"]
        all_moves = [
            FSMNode(
                index=step.get("hex_index", 0),
                name=step.get("hexagram", ""),
                code=step.get("bits", ""),
                physics_description="",
                entropy_S=step.get("entropy_S", 0.0),
                mass_M=sum(int(b) for b in step.get("bits", "000000")),
            )
            for step in chain
        ]
        if chain:
            last = chain[-1]
            last_state = FSMState.from_bits(last["bits"])
            next_state_node = FSMNode(
                index=last.get("hex_index", 0),
                name=last.get("hexagram", ""),
                code=last.get("bits", ""),
                physics_description="",
                entropy_S=last.get("entropy_S", 0.0),
                mass_M=last_state.mass_M(),
            )

    elif path_number == 4:
        all_moves = [
            FSMNode(
                index=0,
                name="错卦",
                code="全翻",
                physics_description="",
                entropy_S=0.0,
                mass_M=0,
            ),
            FSMNode(
                index=0,
                name="综卦",
                code="倒置",
                physics_description="",
                entropy_S=0.0,
                mass_M=0,
            ),
        ]

    return DeterministicResult(
        current_node=current_node,
        max_stress_bit=focus_bit,
        stress_type=stress_type,
        evolution_path=path_number,
        evolution_path_name=path_name,
        all_possible_moves=all_moves,
        next_state=next_state_node,
    )


# =============================================================================
# API 路由
# =============================================================================

@app.get("/")
def root():
    return {"message": "史易枢机 V11.0 — 影子协议离散自动机确定性演化引擎", "version": "11.0.0"}


@app.post("/api/infer")
def infer(query: str):
    """
    LLM 分析 + V11.0 确定性硬算叠加

    Step A: Intent rewrite
    Step B: Knowledge base search
    Step C: FSM analysis (LLM)
    Step D: V11.0 确定性硬算（叠加在 LLM 结果之上）
    """
    chain = IChingChain()

    # 运行 LLM 链路
    fsm_result, retrieval = chain.run(query)

    # 从 LLM 结果中提取 bits，构建 V2.0 硬算
    try:
        inner_bits = fsm_result.inner_bits or "000"
        outer_bits = fsm_result.outer_bits or "000"
        state = FSMState.from_bits(inner_bits + outer_bits)

        det_result = build_deterministic_result(state)

        # 将确定性结果注入 FSMOutput
        fsm_result.deterministic = det_result

    except Exception as e:
        # 容错：LLM 结果无法解析时跳过 V2.0
        pass

    return {
        "fsm_analysis": fsm_result.model_dump(mode="json"),
        "retrieval_results": retrieval,
    }


@app.get("/api/simulate")
def simulate(bits: str, E0: float = 1.0, P0: float = 0.0):
    """
    给定 6 位代码，返回全部 6 种 Bit Flip 预览
    """
    try:
        state = FSMState.from_bits(bits, E0=E0, P0=P0)
    except Exception:
        return {"error": f"Invalid bits: {bits}, must be 6 characters of 0/1"}

    flips = simulate_all_flips(state)
    hex_index, physics_name, physics_desc = get_hex_state(state)
    current_hex = get_hexagram_name(state.inner_bits(), state.outer_bits())

    return {
        "current": {
            "bits": bits,
            "hexagram": current_hex,
            "index": hex_index,
            "physics_name": physics_name,
            "physics_desc": physics_desc,
            "entropy_S": discrete_entropy(state),
            "mass_M": state.mass_M(),
            "conf_m1": conf_m1(state),
        },
        "flips": [
            {
                "bit": f["bit"],
                "old_val": f["old_val"],
                "new_val": f["new_val"],
                "new_bits": f["new_bits"],
                "hexagram": f["hexagram"],
                "hex_index": f["hex_index"],
                "physics_name": f["physics_name"],
                "physics_desc": f["physics_desc"],
                "entropy_S": f["entropy_S"],
            }
            for f in flips
        ],
    }


@app.get("/api/evolve")
def evolve(bits: str,
           path: Optional[int] = None,
           delta_E_ext: float = 0.0,
           deadlock_flag: bool = False,
           time_in_state: int = 0):
    """
    确定性演化

    - path=None: 自动路由（四路径判定）
    - path=1: 路径一 Max-Stress Trigger
    - path=2: 路径二 互卦
    - path=3: 路径三 熵增 DAG 链
    - path=4: 路径四 全翻/倒置
    """
    try:
        state = FSMState.from_bits(bits)
    except Exception:
        return {"error": f"Invalid bits: {bits}"}

    current_node = state_to_fsm_node(state)

    if path is None:
        route = route_evolution_path(state, delta_E_ext, deadlock_flag, time_in_state)
        return {
            "current": current_node.model_dump(mode="json"),
            "route": {
                "path_number": route["path_number"],
                "path_name": route["path_name"],
                "description": route["description"],
                "result": route["result"],
            },
        }

    # 指定路径
    if path == 1:
        result = path1_max_stress(state)
        next_state = result["next_state"]
        return {
            "current": current_node.model_dump(mode="json"),
            "path": 1,
            "path_name": "微观单点击穿",
            "triggered_bit": result["triggered_bit"],
            "stress_type": result["stress_type"],
            "next_state": state_to_fsm_node(next_state).model_dump(mode="json"),
        }

    elif path == 2:
        result = path2_hidden_core_exposure(state)
        next_state = result["next_state"]
        return {
            "current": current_node.model_dump(mode="json"),
            "path": 2,
            "path_name": "隐性内核暴露",
            "operation": result["operation"],
            "next_state": state_to_fsm_node(next_state).model_dump(mode="json"),
        }

    elif path == 3:
        chain = path3_macro_entropy_decay(state)
        return {
            "current": current_node.model_dump(mode="json"),
            "path": 3,
            "path_name": "宏观热力学衰变",
            "entropy_chain": chain,
        }

    elif path == 4:
        result = path4_meta_reset_or_invert(state)
        return {
            "current": current_node.model_dump(mode="json"),
            "path": 4,
            "path_name": "元级别重置与倒置",
            "operations": result,
        }

    return {"error": f"Unknown path: {path}, must be 1/2/3/4"}


@app.get("/api/node")
def node(bits: str):
    """查询当前节点信息"""
    try:
        state = FSMState.from_bits(bits)
    except Exception:
        return {"error": f"Invalid bits: {bits}"}

    hex_index, physics_name, physics_desc = get_hex_state(state)
    hexagram = get_hexagram_name(state.inner_bits(), state.outer_bits())

    return {
        "bits": state.full_bits(),
        "inner_bits": state.inner_bits(),
        "outer_bits": state.outer_bits(),
        "hexagram": hexagram,
        "hex_index": hex_index,
        "physics_name": physics_name,
        "physics_desc": physics_desc,
        "entropy_S": discrete_entropy(state),
        "mass_M": state.mass_M(),
        "B": state.B,
        "E": state.E,
        "E_initial": state.E_initial,
        "R": state.R,
        "R_base": state.R_base,
        "P": state.P,
        "conf_m1": conf_m1(state),
    }
