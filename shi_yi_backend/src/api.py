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
from fastapi import FastAPI, HTTPException
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
    physics_snapshot,
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


class InferRequest(BaseModel):
    query: str = Field(..., description="分析查询")


class PhysicsUncertainty(BaseModel):
    U_E: float = Field(default=0.0, ge=0.0, le=1.0, description="Energy measurement uncertainty")
    U_P: float = Field(default=0.0, ge=0.0, le=1.0, description="Pressure measurement uncertainty")
    U_R: float = Field(default=0.0, ge=0.0, le=1.0, description="Dissipation measurement uncertainty")
    U_tau: float = Field(default=0.0, ge=0.0, le=1.0, description="Yield threshold measurement uncertainty")


class PhysicsRequest(BaseModel):
    bits: str = Field(..., description="6-bit state, e.g. '111000'")
    E: list[float] = Field(..., description="Current fuel/energy per layer")
    P: list[float] = Field(..., description="Current pressure per layer")
    R: list[float] = Field(..., description="Dissipation rate per layer")
    tau: list[float] = Field(..., description="Yield threshold per layer")
    C: Optional[list[float]] = Field(default=None, description="Pressure accumulation rate per layer")
    E_initial: Optional[list[float]] = Field(default=None, description="Initial fuel/energy per layer")
    R_base: Optional[list[float]] = Field(default=None, description="Baseline dissipation per layer")
    U: Optional[PhysicsUncertainty] = Field(default=None, description="Input uncertainty")
    delta_E_ext: float = Field(default=0.0, description="External energy injection for route selection")
    deadlock_flag: bool = Field(default=False, description="Whether the system is in absolute deadlock")
    time_in_state: int = Field(default=0, ge=0, description="Ticks spent in current state")
    monte_carlo_N: int = Field(default=MONTE_CARLO_N, ge=1, le=10000)


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


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def build_physics_seed(fsm_result: FSMOutput, query: str) -> dict:
    """
    Build a conservative raw-physics estimate from semantic analysis.

    This is not measurement truth. It gives the frontend a coherent starting
    point so /api/physics can run the real ADC/TTL/tensor pipeline immediately.
    """
    bits = (fsm_result.inner_bits or "000") + (fsm_result.outer_bits or "000")
    if len(bits) != 6 or any(c not in "01" for c in bits):
        bits = "000000"

    E = []
    P = []
    R = []
    tau = [1.0] * 6
    C = []
    E_initial = [1.0] * 6
    R_base = [0.1] * 6

    pressure_terms = ("压", "债", "KPI", "监管", "冲突", "阻力", "危机", "堵", "闭塞", "过载", "挤压", "爆")
    depletion_terms = ("耗", "亏空", "枯竭", "干涸", "断供", "透支", "衰退", "崩", "断裂", "燃料")
    support_terms = ("现金", "粮", "资源", "支撑", "储备", "资本", "兵", "算力", "财政")

    bit_text = {item.bit_position: item.description for item in fsm_result.bit_analysis}
    stress_text = f"{fsm_result.stress_analysis.stress_type} {fsm_result.stress_analysis.analysis}"
    deadlock_text = f"{query} {stress_text} {fsm_result.mutation_suggestion}"
    focus_bit = fsm_result.energy_focus.focus_bit

    for bit_index, char in enumerate(bits, start=1):
        is_active = char == "1"
        text = f"{query} {bit_text.get(bit_index, '')}"

        energy = 0.74 if is_active else 0.9
        pressure = 0.18 if is_active else 0.32
        dissipation = 0.11 if is_active else 0.08
        compression = 0.15

        pressure_hits = sum(1 for term in pressure_terms if term in text)
        depletion_hits = sum(1 for term in depletion_terms if term in text)
        support_hits = sum(1 for term in support_terms if term in text)

        pressure += 0.08 * pressure_hits
        compression += 0.015 * pressure_hits
        energy -= 0.1 * depletion_hits
        dissipation += 0.025 * depletion_hits
        energy += 0.04 * support_hits

        if bit_index == focus_bit:
            if any(term in stress_text for term in ("断裂", "燃料", "耗尽", "坍塌")):
                energy = min(energy, 0.22)
                dissipation = max(dissipation, 0.17)
            elif any(term in stress_text for term in ("撞墙", "压强", "爆破", "挤压")):
                pressure = max(pressure, 0.86)
                compression = max(compression, 0.2)
            else:
                energy = min(energy, 0.55)
                pressure = max(pressure, 0.5)

        E.append(round(clamp(energy, 0.05, 1.0), 3))
        P.append(round(clamp(pressure, 0.0, 0.98), 3))
        R.append(round(clamp(dissipation, 0.02, 0.25), 3))
        C.append(round(clamp(compression, 0.05, 0.3), 3))

    uncertainty = 0.22
    if not fsm_result.bit_analysis:
        uncertainty = 0.35
    if not fsm_result.inner_system and not fsm_result.outer_system:
        uncertainty = max(uncertainty, 0.42)

    return {
        "bits": bits,
        "E": E,
        "P": P,
        "R": R,
        "tau": tau,
        "C": C,
        "E_initial": E_initial,
        "R_base": R_base,
        "U": {
            "U_E": uncertainty,
            "U_P": uncertainty,
            "U_R": min(0.5, uncertainty + 0.05),
            "U_tau": min(0.5, uncertainty + 0.08),
        },
        "delta_E_ext": 0.0,
        "deadlock_flag": any(term in deadlock_text for term in ("死锁", "闭塞", "僵化", "通道全部闭塞")),
        "time_in_state": 0,
        "monte_carlo_N": MONTE_CARLO_N,
    }


# =============================================================================
# API 路由
# =============================================================================

@app.get("/")
def root():
    return {"message": "史易枢机 V11.0 — 影子协议离散自动机确定性演化引擎", "version": "11.0.0"}


@app.post("/api/infer")
def infer(body: InferRequest):
    """
    LLM 分析 + V11.0 确定性硬算叠加

    Step A: Intent rewrite
    Step B: Knowledge base search
    Step C: FSM analysis (LLM)
    Step D: V11.0 确定性硬算（叠加在 LLM 结果之上）
    """
    chain = IChingChain()

    # 运行 LLM 链路
    fsm_result, retrieval = chain.run(body.query)

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

    physics_seed = build_physics_seed(fsm_result, body.query)

    return {
        "fsm_analysis": fsm_result.model_dump(mode="json"),
        "retrieval_results": retrieval,
        "physics_seed": physics_seed,
    }


@app.post("/api/physics")
def physics(body: PhysicsRequest):
    """
    Physics-first SSOT pipeline:
    raw layer inputs -> ADC phases/TTL -> hard interrupt -> tensor -> MC distribution.
    """
    try:
        state = FSMState.from_physics(
            bits=body.bits,
            E=body.E,
            P=body.P,
            R=body.R,
            tau=body.tau,
            C=body.C,
            E_initial=body.E_initial,
            R_base=body.R_base,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    U = body.U.model_dump() if body.U else None
    return physics_snapshot(
        state,
        U=U,
        mc_N=body.monte_carlo_N,
        delta_E_ext=body.delta_E_ext,
        deadlock_flag=body.deadlock_flag,
        time_in_state=body.time_in_state,
    )


@app.get("/api/simulate")
def simulate(bits: str, E0: float = 1.0, P0: float = 0.0):
    """
    给定 6 位代码，返回全部 6 种 Bit Flip 预览
    """
    try:
        state = FSMState.from_bits(bits, E0=E0, P0=P0)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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

    raise HTTPException(status_code=400, detail=f"Unknown path: {path}, must be 1/2/3/4")


@app.get("/api/node")
def node(bits: str):
    """查询当前节点信息"""
    try:
        state = FSMState.from_bits(bits)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
        "tau": state.tau,
        "conf_m1": conf_m1(state),
    }
