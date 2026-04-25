"""
影子协议 V11.0 — 离散自动机确定性演化内核
Deterministic FSM Kernel for 6-Bit Topology Engine (V11.0 Discrete Automaton)

基于《影子协议 V11.0：离散自动机可证伪版》编译。
核心改进：
1. 离散差分方程取代连续积分：E_i(t) = E_i(t-1) - R_i · α(B_{t-1})
2. α严格定义：α=1.0（支撑），α=2.0（unsupported，系统退出）
3. p维度（奇偶共振轴）：p = 1 if (i%2!=0)==B[i] else -1，{-1,1}离散集合
4. e维度（能量耗散轴）：e = 1 - 2*min(1, |R_actual-R_base|/R_base) ∈ [-1,1]
5. t维度（时间消耗轴）：t = (E_initial - E_current)/E_initial ∈ [0,1]
6. SSOT管线：raw physics inputs → fsm_kernel.py计算所有量，语义层仅做标注
7. Conf_M1 = 1 - max(U_E, U_P, U_R)，Monte Carlo扰动引擎 N=1000

数据结构约定：
- B[1] = 绝对物理底层（Index 1）
- B[6] = 绝对宏观顶层（Index 6）
- 读取顺序：Index 1 → Index 6
- k = 3：内系统 B[1..3]，外系统 B[4..6]
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# 常量与查找表
# =============================================================================

TRIGRAM_MAP = {
    "000": {"name": "坤", "symbol": "☷"},
    "001": {"name": "震", "symbol": "☳"},
    "010": {"name": "坎", "symbol": "☵"},
    "011": {"name": "兑", "symbol": "☱"},
    "100": {"name": "巽", "symbol": "☴"},
    "101": {"name": "离", "symbol": "☲"},
    "110": {"name": "艮", "symbol": "☶"},
    "111": {"name": "乾", "symbol": "☰"},
}

HEXAGRAM_LOOKUP = {
    "乾乾": "乾", "乾坤": "否", "乾震": "无妄", "乾坎": "讼", "乾艮": "遯",
    "乾巽": "姤", "乾离": "同人", "乾兑": "履",
    "坤乾": "泰", "坤坤": "坤", "坤震": "豫", "坤坎": "师", "坤艮": "谦",
    "坤巽": "升", "坤离": "明夷", "坤兑": "临",
    "震乾": "大壮", "震坤": "复", "震震": "震", "震坎": "解", "震艮": "小过",
    "震巽": "恒", "震离": "丰", "震兑": "归妹",
    "坎乾": "需", "坎坤": "比", "坎震": "屯", "坎坎": "坎", "坎艮": "蹇",
    "坎巽": "井", "坎离": "既济", "坎兑": "节",
    "艮乾": "大畜", "艮坤": "剥", "艮震": "颐", "艮坎": "蒙", "艮艮": "艮",
    "艮巽": "蛊", "艮离": "贲", "艮兑": "损",
    "巽乾": "小畜", "巽坤": "观", "巽震": "益", "巽坎": "涣", "巽艮": "渐",
    "巽巽": "巽", "巽离": "鼎", "巽兑": "中孚",
    "离乾": "大有", "离坤": "晋", "离震": "噬嗑", "离坎": "未济", "离艮": "旅",
    "离巽": "鼎", "离离": "离", "离兑": "睽",
    "兑乾": "夬", "兑坤": "萃", "兑震": "归妹", "兑坎": "困", "兑艮": "咸",
    "兑巽": "中孚", "兑离": "睽", "兑兑": "兑",
}

# =============================================================================
# 64 节点物理状态表
# 来源：阶段一：底层状态节点.md
# key = "外卦名+内卦名"，value = (index, 状态名, 物理描述)
# =============================================================================

HEX_STATES: dict[str, tuple[int, str, str]] = {
    # 模块一：系统初始化与早期摩擦 (01-08)
    "乾乾": (1,  "绝对过热态",  "内外全量刚性扩张。系统算力满载，不计成本疯狂输出。极化警告：无缓冲垫，即将因资源枯竭而刚性折断。"),
    "坤坤": (2,  "绝对基态",    "内外全量柔性收缩。系统放弃一切主动权，呈现纯粹的物理承载态。极度稳定，无内耗，等待外部能量注入。"),
    "坎震": (3,  "受限爆发态",  "内系统底层爆发动能，外系统存在高压陷阱。系统启动受阻，动能转化为高热内耗，必须强行建立底层基础设施。"),
    "巽坎": (4,  "信息屏蔽态",  "内系统高压，外系统顶层锁死。系统处于盲态，缺乏信息输入与反馈。唯有通过试错或强力打破边界以获取数据。"),
    "坎乾": (5,  "强制降频态",  "内系统极速扩张，外系统存在物理阻力。动能不能直接释放，必须进入待机模式，消耗时间而非空间。"),
    "乾坎": (6,  "高阻抗摩擦态", "内系统处于封闭高压，外系统采取刚性压制。系统间无有效接口，产生极高摩擦热。策略：立刻停止能量输出，退出当前博弈。"),
    "坤坎": (7,  "集中暴力输出态", "内系统高度集权管控，外系统完全退让。系统抽干所有非核心资源，转化为单一维度的暴力打击能力。"),
    "坎坤": (8,  "低能耗吸附态", "内系统零动能，外系统形成强大的引力中心。系统放弃独立边界，执行依附协议，以此换取生存资源。"),

    # 模块二：资源累积与小周期循环 (09-16)
    "巽乾": (9,  "微阻挡蓄能态", "内系统高速扩张，被外系统柔性边界轻微兜住。能量输出被暂时拦截并转化为势能，但约束力极弱。"),
    "兑乾": (10, "高危跟随态",  "内系统上层开放，紧跟外系统的绝对刚性。如同在剃刀边缘行走，必须维持极高精度的跟随步频，一旦错位即被碾压。"),
    "坤乾": (11, "完美热力对流", "外系统完全下沉退让，内系统全量向上扩张。能量无摩擦交换，系统效率达到理论最高值。警告：最高点即为衰落的起点。"),
    "乾坤": (12, "绝对熵死态",  "外系统向上膨胀锁死，内系统向下收缩躺平。上下能量通道彻底断裂，零信息交换，系统走向僵尸化。"),
    "乾离": (13, "同频共振态",  "内系统中层空虚，外系统全量输出。内系统放弃部分边界，与外部形成最大公约数，实现大范围网络协同。"),
    "离乾": (14, "核心吸积态",  "内系统全量扩张，外系统中空形成引力黑洞。内部庞大的能量被外部的高层级节点捕获并整合，实现资源最大化占有。"),
    "艮坤": (15, "势能隐藏态",  "内系统拥有高层动能，却将外系统伪装为绝对柔弱。通过向下兼容来降低环境阻力，是最高效的安全扩张策略。"),
    "震坤": (16, "动能预释放态", "内系统绝对静止，外系统底层爆发动能。环境出现上升气流，系统借势启动，呈顺滑滑行状态。"),

    # 模块三：系统重构与内部消化 (17-26)
    "兑震": (17, "动能牵引态",  "内系统底层爆发，外系统开放接口。内部的新生能量顺势滑入外部轨道，放弃主导权以换取运动空间。"),
    "巽巽": (18, "代码重构态",  "内系统僵化，外系统顶层锁死。系统内部积累了大量垃圾数据，必须启动底层清灰和重构程序。"),
    "坤兑": (19, "降维覆盖态",  "内系统能量充盈并开放接口，外系统完全不设防。高势能向低势能进行无阻力俯冲与覆盖。"),
    "离震": (21, "暴力粉碎态",  "内系统底层爆发，遭遇外系统中空的卡点。系统接口处卡入异物，必须启动最高优先级的暴力破解，咬碎阻碍。"),
    "离巽": (22, "表层渲染态",  "内外系统核心均不扩张，通过UI界面的修饰来降低交互阻力。低能耗，但无法改变底层逻辑。"),
    "震震": (51, "连续冲击波",  "内外系统底层接连爆发巨大动能。巨大的外部输入导致系统发生高频振荡，测试系统抗压阈值。"),
    "乾震": (25, "底层驱动态",  "内系统依据最本能的动能运转，外系统呈现绝对客观规律。只要动作符合底层物理学，不产生主观偏差，即无内耗。"),
    "艮乾": (26, "高压封存态",  "内系统疯狂扩张，被外系统顶层绝对死锁强行压制。能量无法输出，在内部被极限压缩，酝酿核聚变级别的势能。"),

    # 模块四：高危博弈与震荡周期 (27-36)
    "艮震": (27, "资源吞吐态",  "内系统底层爆发，外系统顶层锁死，中间全部为0。形成一个巨大的吞噬结构，系统进入纯粹的资源输入与消化模式。"),
    "兑巽": (28, "承重极限态",  "两端虚弱，中段过度膨胀。系统中间层负载过大，根基与顶层无法支撑，即将发生结构性断裂。必须采取极端降重操作。"),
    "坎坎": (29, "深渊闭环态",  "内外系统全为内部高压。系统跌入死循环的物理陷阱，周围没有借力点。只能凭借核心极度专注来熬过时间周期。"),
    "离离": (30, "高耗散辐射态", "内外系统皆为中空辐射。系统处于烈火烹油的极度活跃期，极度光鲜但没有核心基本盘，必须持续吞噬外部燃料才能存活。"),
    "兑艮": (31, "无缝耦合态",  "内系统顶层刚性，外系统底部开放。一凸一凹，两个子系统发生高速的化学反应与能量对接，无物理摩擦。"),
    "巽震": (32, "动态锁定态",  "内系统渗透，外系统爆发，两者形成稳定的力学对冲结构。系统维持在一个长周期的动态平衡带中。"),
    "乾艮": (33, "战略脱离态",  "外系统全面刚性压制，内系统仅保留上层动能。发现不可抗力的环境恶化，系统立刻切断底层累赘，执行高能效的逃逸动作。"),
    "震乾": (34, "暴力冲撞态",  "内系统全量扩张，外系统遭遇底层爆发。系统动能过剩，以硬碰硬的方式直接撞击外部边界，极易产生物理损伤。"),
    "离坤": (35, "无阻力爬升态", "内系统完全柔性，外系统呈现引力空洞。系统如日出般顺滑地进入高位，没有遭遇任何结构性抵抗。"),
    "坤离": (36, "黑盒隐匿态",  "内系统处于高耗散态，但外系统全面封杀。系统必须立刻关闭所有对外输出端口，转入地下潜伏，以保全核心代码。"),

    # 模块五：复杂结构与矛盾处理 (37-54)
    "巽离": (37, "防火墙内网态", "建立严格的内部权限控制系统。通过明确上下级接口，将系统内耗降至最低。"),
    "离兑": (38, "协议不兼容态", "内外系统目标函数完全相反，无法进行有效通信。只能搁置底层逻辑争议，寻找微小的交集点进行点对点交易。"),
    "坎艮": (39, "物理死角态",  "前有高压陷阱，后有刚性高墙。系统动能被完全锁死。唯一的物理学解法是：原路返回，寻找新路径。"),
    "震坎": (40, "压强释放态",  "内系统高压，外系统动能爆发。外部环境的剧变击碎了原有的陷阱，系统内部的高压瞬间得以释放，危机解除。"),
    "艮兑": (41, "底层上行态",  "主动削减底层资源，输送给高层。系统执行集中力量办大事协议，牺牲局部换取整体安全。"),
    "震巽": (42, "顶层下放态",  "高层削减自身权限与资源，向下灌溉给底层。系统执行释放流动性协议，激发底层算力与活力。"),
    "兑乾": (43, "单点突破态",  "内系统全量刚性扩张，只剩外系统顶层最后一块柔性阻碍。系统汇聚所有动能，执行最后的大决战，瞬间冲破阈值。"),
    "巽乾": (44, "底层病毒态",  "外系统全面刚健，但在内系统最底层出现了一个微小的柔性接口。极度危险的特洛伊木马，看似微弱，实则足以腐蚀整个刚性架构。"),
    "兑坤": (45, "高密度汇聚态", "外系统提供开放接口，内系统作为庞大的承载盘。资源、信息、算力向中心节点呈漏斗状高密度聚集。"),
    "巽坤": (46, "柔性渗透态",  "内系统如植物根系般渗透，外系统毫不抵抗。一种低烈度、不引发警报的持续性阶层跃升。"),
    "兑坎": (47, "动能枯竭态",  "内系统处于高压陷阱，外系统接口破损。系统水位降至临界点以下，资源断绝，只能依靠核心代码的绝对韧性维持不崩溃。"),
    "坎巽": (48, "底层开源态",  "系统结构固定不变，但深挖底层数据库。不向外扩张，而是通过建立垂直通道，持续提取地下势能供全系统使用。"),
    "坎兑": (60, "流量控制态",  "内系统全面开放，外系统设立卡点。不能无限制释放，必须对输入/输出的带宽进行精确的物理阀门控制。"),
    "震兑": (54, "非标并入态",  "内系统开放缺口，外系统动能爆发。以不合常规、缺乏核心控制权的方式强行并入大系统。初期快速，后期隐患极大。"),

    # 模块六：极致演化与最终循环 (55-64)
    "震离": (55, "超量载荷态",  "内系统极度活跃燃烧，外系统雷霆爆发。系统能量处于历史最高峰，但极不稳定，如同超新星爆发的前夜，必然迅速走向黯淡。"),
    "离艮": (56, "游离散列态",  "内系统被锁死，外系统燃烧耗散。系统失去基本盘，变为游离节点，只能在外部网络中临时挂载，无法建立长期积累。"),
    "兑兑": (58, "全面开源态",  "内外系统均打开顶层接口。系统处于绝对开放状态，高频地进行物质与信息交换，容易引发共振。"),
    "巽坎": (59, "结构溶解态",  "内系统处于封闭高压，外系统如同强风渗透。原本坚固的系统边界被外部力量吹散、溶解，资源重新流入公共池。"),
    "巽兑": (61, "底层互信握手", "外系统上层开放，内系统底层渗透，中心为空。系统间建立了不依赖武力的极高强度信息验证协议。"),
    "震艮": (62, "低频微调试态", "两端强，中间弱。系统无法承担宏大战略，只能进行极低风险的、战术级别的微小超越与调整。"),
    "坎离": (63, "绝对平衡陷阱", "内外系统的阴阳爻100%精准匹配。致命状态！系统达到了完美的热力学平衡，势能差归零。这意味着系统彻底失去了演化动能，下一秒必然开始崩坏。"),
    "离坎": (64, "高势能混沌态", "内外系统的阴阳爻100%全部错位。最混乱，但也是最优状态。系统充满巨大的摩擦与势能差，意味着无限的演化动力与重组空间，是下一个大周期的起点。"),
}


# =============================================================================
# 物理参数默认值（V11.0 离散版）
# =============================================================================

DEFAULT_R = 0.1        # 基础耗散率（每tick）
DEFAULT_C = 0.15       # 压强累积率
DEFAULT_TAU = 1.0      # 材料屈服阈值
DEFAULT_E0 = 1.0       # 初始能量储备
DEFAULT_P0 = 0.0       # 初始压强
K = 3                  # 内外系统分界（B[1..k]=内，B[k+1..6]=外）
M_THRESHOLD = 4        # 路径三巨型系统判定（M > M_THRESHOLD）
T_MASK = 5             # 路径二潜伏超时阈值
MONTE_CARLO_N = 1000   # Monte Carlo扰动采样次数
U_INPUT = 0.1          # 默认输入不确定性


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class FSMState:
    """
    6-Bit 状态机当前状态（V11.0 离散自动机版）

    B[1..6]: 布尔数组，Index 1 为绝对底层，Index 6 为绝对顶层
    E[1..6]: 各节点当前能量储备（每tick离散递减）
    P[1..6]: 各节点当前承受的外部压强（每tick离散累积）
    E_initial[1..6]: 各节点初始能量（基准值，用于计算t维度）
    R[1..6]: 各节点的基础耗散率
    R_base[1..6]: 各节点的基准耗散率（用于计算e维度）
    tau[1..6]: 各节点的材料屈服阈值
    C[1..6]: 各节点的压强累积率

    V11.0三大公理：
    - 公理1：拓扑层级不交性（层级间独立演化）
    - 公理2：能量守恒（能量只能从1节点流向0节点）
    - 公理3：奇偶共振（B[i]与位置奇偶性匹配时系统稳定）
    """
    B: list[int]                     # B[1..6]，取值为 0 或 1
    E: list[float]                   # E[1..6]，当前能量储备
    P: list[float]                   # P[1..6]，当前压强
    E_initial: list[float]           # E_initial[1..6]，初始能量（基准）
    R: list[float]                   # R[1..6]，基础耗散率
    R_base: list[float]              # R_base[1..6]，基准耗散率
    tau: list[float]                 # tau[1..6]，屈服阈值
    C: list[float]                   # C[1..6]，压强累积率

    @classmethod
    def from_bits(cls, bits: str,
                  E0: float = DEFAULT_E0,
                  P0: float = DEFAULT_P0,
                  tau0: float = DEFAULT_TAU,
                  R0: float = DEFAULT_R,
                  C0: float = DEFAULT_C) -> "FSMState":
        """
        从 6 位字符串构造 FSMState（V11.0 离散版）

        Args:
            bits: 6 位字符串（如 "111000"，bit[0]=B[1]，bit[5]=B[6]）
            E0: 初始能量储备（默认值 1.0）
            P0: 初始压强（默认值 0.0）
            tau0: 屈服阈值（默认值 1.0）
            R0: 基础耗散率（默认值 0.1）
            C0: 压强累积率（默认值 0.15）
        """
        B = [int(c) for c in bits]
        E_initial = [E0] * 6
        E = [E0] * 6
        P = [P0] * 6
        tau = [tau0] * 6
        R = [R0] * 6
        R_base = [R0] * 6
        C = [C0] * 6
        return cls(B=B, E=E, P=P, E_initial=E_initial,
                    R=R, R_base=R_base, tau=tau, C=C)

    def full_bits(self) -> str:
        """返回 6 位完整字符串（Bit1 在左，Bit6 在右）"""
        return "".join(str(b) for b in self.B)

    def inner_bits(self) -> str:
        """返回内系统 3 位（B[1..3]）"""
        return "".join(str(self.B[i]) for i in range(3))

    def outer_bits(self) -> str:
        """返回外系统 3 位（B[4..6]）"""
        return "".join(str(self.B[i]) for i in range(3, 6))

    def mass_M(self) -> int:
        """系统总质量 M = 拥有 1 的数量"""
        return sum(self.B)

    def __post_init__(self):
        assert len(self.B) == 6, "B must have exactly 6 elements"


# =============================================================================
# V11.0 三大维度函数
# =============================================================================

def p_dimension(i: int, B_i: int) -> int:
    """
    p维度（奇偶共振轴）

    公理3：奇数位置期望B=1，偶数位置期望B=0。
    p = 1 表示共振（稳定），p = -1 表示失共振（应力积累）。

    V11.0 p维度严格取{-1, 1}离散集合。

    Args:
        i: 节点位置（1-6，1=底层）
        B_i: 节点当前值（0或1）

    Returns:
        p ∈ {1, -1}
    """
    # 奇数位置（1,3,5）：期望B=1
    # 偶数位置（2,4,6）：期望B=0
    is_odd = (i % 2) != 0
    if is_odd:
        return 1 if B_i == 1 else -1
    else:
        return 1 if B_i == 0 else -1


def e_dimension(R_actual: float, R_base: float) -> float:
    """
    e维度（能量耗散轴）

    分段定义：
    - ratio ∈ [0, 0.5]: e = 1 - 2*ratio（线性衰减）
    - ratio ∈ (0.5, 1.0]: e = 0（平台期，表示中等摩擦）
    - ratio > 1.0: e = max(-1, 1 - ratio)（继续衰减至-1）

    设计文档中的表格：
    - ratio=0（正常） → e=1（网络顺畅）
    - ratio=0.5（50%偏离） → e=0（中等摩擦）
    - ratio=1.0（100%偏离，两倍基准能耗） → e=0（严重摩擦，但不是断联）
    - ratio>1.0 → e=-1（完全断联/孤岛）

    注意：设计文档中公式 e = 1 - 2*min(1, ratio) 在 ratio=1.0 时给出 e=-1，
    与表格中 e=0 的定义矛盾。本实现遵循表格的行为定义。

    Args:
        R_actual: 当前耗散率
        R_base: 基准耗散率

    Returns:
        e ∈ [-1, 1]
    """
    if R_base <= 0:
        return -1.0
    ratio = abs(R_actual - R_base) / R_base
    if ratio <= 0.5:
        return 1.0 - 2.0 * ratio
    elif ratio <= 1.0:
        return 0.0
    else:
        return max(-1.0, 1.0 - ratio)


def t_dimension(E_current: float, E_initial: float) -> float:
    """
    t维度（时间消耗轴）

    t = (E_initial - E_current) / E_initial ∈ [0, 1]

    t = 0 ：能量尚未消耗，系统处于初始状态
    t = 1 ：能量完全耗尽，系统处于最终衰变状态

    Args:
        E_current: 当前能量储备
        E_initial: 初始能量储备

    Returns:
        t ∈ [0, 1]
    """
    if E_initial <= 0:
        return 1.0
    return max(0.0, min(1.0, (E_initial - E_current) / E_initial))


def stress_p(B_i: int, i: int) -> float:
    """
    p维度应力 σ_p

    σ_p = (1 - p) / 2
    - p = 1（共振稳定）→ σ_p = 0
    - p = -1（失共振应激）→ σ_p = 1
    """
    p = p_dimension(i, B_i)
    return (1.0 - p) / 2.0


def stress_e(R_actual: float, R_base: float) -> float:
    """
    e维度应力 σ_e

    σ_e = (1 - e) / 2
    - e = 1（最小耗散）→ σ_e = 0
    - e = -1（最大耗散）→ σ_e = 1
    """
    e = e_dimension(R_actual, R_base)
    return (1.0 - e) / 2.0


def stress_t(E_current: float, E_initial: float) -> float:
    """
    t维度应力 σ_t

    σ_t = t = (E_initial - E_current) / E_initial
    - t = 0（未消耗）→ σ_t = 0
    - t = 1（完全耗尽）→ σ_t = 1
    """
    return t_dimension(E_current, E_initial)


# =============================================================================
# 离散差分方程（V11.0核心）
# =============================================================================

def alpha(B_down: int) -> float:
    """
    α(B) 结构惩罚因子（V11.0严格版）

    α = 1.0：B_down = 1（下层有支撑，稳态）
    α = 2.0：B_down = 0（下层无支撑，unsupported态 → 系统必须退出当前路径）

    V11.0严格约定：α只取{1.0, 2.0}，不允许其他中间值。
    α=2.0是系统级Unsupported信号，不触发flip而是系统拒绝当前路径。
    """
    return 1.0 if B_down == 1 else 2.0


def step_energy(E_i: float, R_i: float, B_down: int) -> float:
    """
    离散能量差分方程

    E_i(t) = E_i(t-1) - R_i * α(B_{t-1})

    每tick消耗 R_i * α(B) 单位的能量。
    """
    a = alpha(B_down)
    return max(0.0, E_i - R_i * a)


def step_pressure(P_i: float, C_i: float, B_up: int) -> float:
    """
    离散压强差分方程

    P_i(t) = P_i(t-1) + C_i * B_up(t-1)

    每tick累积 C_i * B_up 单位的压强。
    """
    return P_i + C_i * B_up


def check_fuel_exhaustion(E_i: float, R_i: float, B_down: int) -> bool:
    """
    燃料耗尽检查（1 → 0 断裂）

    如果下一步能量<=0，则必然断裂。
    注意：α=2.0时系统进入Unsupported态，但仍执行断裂判定。
    """
    next_E = step_energy(E_i, R_i, B_down)
    return next_E <= 0.0


def check_explosive_rebound(P_i: float, C_i: float, B_up: int, tau_i: float) -> bool:
    """
    压强击穿检查（0 → 1 爆破）

    如果下一步压强>=tau_i，则必然爆破。
    """
    next_P = step_pressure(P_i, C_i, B_up)
    return next_P >= tau_i


# =============================================================================
# 辅助函数
# =============================================================================

def get_hexagram_name(inner_bits: str, outer_bits: str) -> str:
    """根据内卦和外卦获取六爻卦名"""
    outer_trigram = TRIGRAM_MAP.get(outer_bits, {})
    inner_trigram = TRIGRAM_MAP.get(inner_bits, {})
    key = outer_trigram.get("name", "") + inner_trigram.get("name", "")
    return HEXAGRAM_LOOKUP.get(key, key or "未知")


def get_hex_state(state: FSMState) -> tuple[int, str, str]:
    """获取当前状态的 64 节点物理描述"""
    outer_trigram = TRIGRAM_MAP.get(state.outer_bits(), {}).get("name", "")
    inner_trigram = TRIGRAM_MAP.get(state.inner_bits(), {}).get("name", "")
    key = outer_trigram + inner_trigram
    if key in HEX_STATES:
        return HEX_STATES[key]
    name = get_hexagram_name(state.inner_bits(), state.outer_bits())
    return (0, "未定义态", f"内外系统 {key} 的组合尚未录入状态机")


def discrete_entropy(state: FSMState) -> float:
    """
    离散系统熵（V11.0版）

    S(t) = -∑_i p_i log(p_i)，其中 p_i = E_i / ∑E

    不同于V2.0的相邻层势能差+耗散废热模型，
    V11.0使用信息熵严格定义：系统能量分布越均匀，熵越高。
    """
    total_E = sum(state.E)
    if total_E <= 0:
        return 0.0
    S = 0.0
    for E_i in state.E:
        if E_i > 0:
            p_i = E_i / total_E
            S -= p_i * math.log(p_i + 1e-10)
    return float(S)


# =============================================================================
# 核心演化函数（V11.0离散版）
# =============================================================================

def max_stress_trigger(state: FSMState) -> tuple[int, str]:
    """
    应力极值触发器 — Max-Stress Trigger（V11.0离散版）

    计算6个节点在各自三大维度上的应力系数 σ_i = max(σ_p, σ_e, σ_t)，
    返回应力最大的节点（唯一动爻）。

    V11.0变化：
    - 不再使用连续积分方程
    - 不再使用单一 σ = P/tau 或 E_remaining 公式
    - 使用三维应力分量 σ_p, σ_e, σ_t 的最大值

    Returns:
        (focus_bit, stress_type) — 动爻位置（1-6）和应力类型
    """
    best_i = 1
    best_sigma = -1.0
    best_type = "稳态"

    for i in range(1, 7):
        idx = i - 1
        B_i = state.B[idx]
        E_i = state.E[idx]
        P_i = state.P[idx]
        E_init = state.E_initial[idx]
        R_i = state.R[idx]
        R_base = state.R_base[idx]
        C_i = state.C[idx]
        tau_i = state.tau[idx]

        # 上下邻居
        B_down = state.B[idx - 1] if idx > 0 else 0
        B_up = state.B[idx + 1] if idx < 5 else 0

        # 三大维度应力分量
        sigma_p = stress_p(B_i, i)
        sigma_e = stress_e(R_i, R_base)
        sigma_t = stress_t(E_i, E_init)

        # 综合应力
        sigma = max(sigma_p, sigma_e, sigma_t)

        # 确定触发类型
        if B_i == 1:
            # 刚态：燃料耗尽（t维度）
            if check_fuel_exhaustion(E_i, R_i, B_down):
                stress_type = "燃料耗尽"
                sigma = 1.0
            else:
                stress_type = "稳态"
        else:
            # 柔态：压强击穿
            if check_explosive_rebound(P_i, C_i, B_up, tau_i):
                stress_type = "压强击穿"
                sigma = 1.0
            else:
                stress_type = "稳态"

        if sigma > best_sigma:
            best_sigma = sigma
            best_i = i
            best_type = stress_type

    return (best_i, best_type)


def flip_bit(state: FSMState, i: int) -> FSMState:
    """
    确定性翻转 B[i]（V11.0离散版）

    翻转后：
    - E_i 重置为 E_initial[i]（能量刷新）
    - P_i 重置为 0.0（压强清零）
    - R_i 保持不变（耗散率配置保持）
    """
    idx = i - 1
    new_B = state.B.copy()
    new_E = state.E.copy()
    new_P = state.P.copy()
    new_E_init = state.E_initial.copy()
    new_R = state.R.copy()
    new_R_base = state.R_base.copy()
    new_tau = state.tau.copy()
    new_C = state.C.copy()

    new_B[idx] = 0 if new_B[idx] == 1 else 1
    # 翻转后重置该节点
    new_E[idx] = new_E_init[idx]  # 能量刷新到初始值
    new_P[idx] = 0.0               # 压强清零

    return FSMState(
        B=new_B, E=new_E, P=new_P,
        E_initial=new_E_init, R=new_R, R_base=new_R_base,
        tau=new_tau, C=new_C
    )


def simulate_all_flips(state: FSMState) -> list[dict]:
    """
    模拟全部 6 种 Bit Flip，返回每种翻转的目标状态信息

    Returns:
        list of {bit, old_val, new_val, new_bits, hexagram, hex_info}
    """
    results = []
    for i in range(1, 7):
        idx = i - 1
        old_val = state.B[idx]
        new_state = flip_bit(state, i)
        new_bits = new_state.full_bits()
        new_hex = get_hexagram_name(new_state.inner_bits(), new_state.outer_bits())
        hex_index, physics_name, physics_desc = get_hex_state(new_state)
        results.append({
            "bit": i,
            "old_val": old_val,
            "new_val": 1 - old_val,
            "new_bits": new_bits,
            "hexagram": new_hex,
            "hex_index": hex_index,
            "physics_name": physics_name,
            "physics_desc": physics_desc,
            "entropy_S": discrete_entropy(new_state),
        })
    return results


# =============================================================================
# Conf_M1 与 Monte Carlo 扰动引擎
# =============================================================================

def compute_U(state: FSMState) -> tuple[float, float, float, float]:
    """
    计算四维度不确定性：U_E, U_P, U_R, U_tau

    U_E = |ΔE| / E_range = |E_initial - E_current| / E_initial
    U_P = |ΔP| / P_range = P_current / (tau * 6)  [归一化到最大可能压强]
    U_R = |ΔR| / R_range = |R_actual - R_base| / R_base
    U_tau = |Δtau| / tau_range = 0 (默认配置，暂不测量)

    Returns:
        (U_E, U_P, U_R, U_tau)，每个 ∈ [0, 1]
    """
    total_U_E = 0.0
    total_U_R = 0.0

    for i in range(6):
        E_init = state.E_initial[i]
        E_curr = state.E[i]
        R_curr = state.R[i]
        R_base = state.R_base[i]
        P_curr = state.P[i]
        tau_i = state.tau[i]

        if E_init > 0:
            total_U_E += abs(E_init - E_curr) / E_init
        if R_base > 0:
            total_U_R += abs(R_curr - R_base) / R_base

    U_E = total_U_E / 6.0
    U_R = total_U_R / 6.0
    # P归一化：最大可能压强 = sum(tau_i * C_i * 累积步数)
    # 简化：U_P = mean(P_i / tau_i)
    total_U_P = 0.0
    for i in range(6):
        if state.tau[i] > 0:
            total_U_P += state.P[i] / state.tau[i]
    U_P = (total_U_P / 6.0) * 0.5  # 缩放因子使U_P在[0,1]
    U_tau = 0.0  # 暂未实现tau不确定性测量

    return (
        min(1.0, max(0.0, U_E)),
        min(1.0, max(0.0, U_P)),
        min(1.0, max(0.0, U_R)),
        min(1.0, max(0.0, U_tau)),
    )


def conf_m1(state: FSMState) -> float:
    """
    系统置信度 Conf_M1 = 1 - max(U_E, U_P, U_R, U_tau)

    Conf_M1 ∈ [0, 1]：
    - 1.0：最大置信，系统处于确定状态
    - 0.0：最小置信，系统处于完全不确定状态

    对应V11.0可伪性协议：低Conf_M1意味着系统接近可伪边界。
    """
    U_E, U_P, U_R, U_tau = compute_U(state)
    return 1.0 - max(U_E, U_P, U_R, U_tau)


def monte_carlo_stress(state: FSMState, N: int = MONTE_CARLO_N,
                       U_input: float = U_INPUT) -> tuple[float, float]:
    """
    Monte Carlo 扰动引擎

    对系统施加 N 次随机扰动（U_input × X_raw，其中 X_raw ~ Uniform(0,1)），
    每次重新计算系统应力，返回应力的均值和标准差。

    Args:
        state: 当前状态
        N: 采样次数（默认1000）
        U_input: 输入不确定性（默认0.1）

    Returns:
        (mean_sigma, std_sigma) — 应力均值和标准差
    """
    # 以当前状态为基准，计算各节点原始应力
    raw_stresses = []
    for i in range(1, 7):
        idx = i - 1
        B_i = state.B[idx]
        E_i = state.E[idx]
        E_init = state.E_initial[idx]
        R_i = state.R[idx]
        R_base = state.R_base[idx]
        P_i = state.P[idx]
        tau_i = state.tau[idx]

        sigma_p = stress_p(B_i, i)
        sigma_e = stress_e(R_i, R_base)
        sigma_t = stress_t(E_i, E_init)
        raw = max(sigma_p, sigma_e, sigma_t)
        raw_stresses.append(raw)

    sigma_mean = sum(raw_stresses) / len(raw_stresses)

    # Monte Carlo采样：扰动×原始值
    perturbed = []
    for _ in range(N):
        X_raw = random.uniform(0, 1)
        sigma_perturbed = U_input * X_raw * sigma_mean
        perturbed.append(sigma_perturbed)

    mean_sigma = sum(perturbed) / N
    variance = sum((s - mean_sigma) ** 2 for s in perturbed) / N
    std_sigma = math.sqrt(variance)

    return (mean_sigma, std_sigma)


# =============================================================================
# 四条演化路径（V11.0离散版）
# =============================================================================

def path1_max_stress(state: FSMState) -> dict:
    """
    路径一：微观单点击穿 (Bit Flip)

    通过 Max-Stress Trigger 找到唯一动爻，执行确定性翻转。
    """
    focus_bit, stress_type = max_stress_trigger(state)

    # 检查是否是Unsupported态（α=2.0）
    idx = focus_bit - 1
    B_down = state.B[idx - 1] if idx > 0 else 0
    unsupported = (alpha(B_down) > 1.0)

    new_state = flip_bit(state, focus_bit)
    new_hex = get_hexagram_name(new_state.inner_bits(), new_state.outer_bits())
    hex_index, physics_name, physics_desc = get_hex_state(new_state)
    return {
        "path": 1,
        "triggered_bit": focus_bit,
        "stress_type": stress_type,
        "unsupported": unsupported,
        "next_state": new_state,
        "next_bits": new_state.full_bits(),
        "next_hexagram": new_hex,
        "hex_index": hex_index,
        "physics_name": physics_name,
        "physics_desc": physics_desc,
        "entropy_S": discrete_entropy(new_state),
        "conf_m1": conf_m1(new_state),
    }


def path2_hidden_core_exposure(state: FSMState) -> dict:
    """
    路径二：隐性内核暴露 (Hidden Core Drive)

    通过互卦（内外卦互换）暴露系统真实演化动力。
    当 B[1]^B[2] == 1 或 B[6]^B[5] == 1 时触发。
    """
    new_inner = state.outer_bits()
    new_outer = state.inner_bits()
    new_bits = new_inner + new_outer
    new_state = FSMState.from_bits(new_bits)
    new_hex = get_hexagram_name(new_inner, new_outer)
    hex_index, physics_name, physics_desc = get_hex_state(new_state)
    return {
        "path": 2,
        "operation": "互卦(内外互换)",
        "next_state": new_state,
        "next_bits": new_bits,
        "next_hexagram": new_hex,
        "hex_index": hex_index,
        "physics_name": physics_name,
        "physics_desc": physics_desc,
        "entropy_S": discrete_entropy(new_state),
        "conf_m1": conf_m1(new_state),
    }


def path3_macro_entropy_decay(state: FSMState) -> list[dict]:
    """
    路径三：宏观热力学衰变 (Macro Entropy Decay)

    沿熵增DAG单向演化，不可逆。
    在封闭系统（delta_E_ext <= 0）中，S(t_n+1) > S(t_n) 必须为真。
    返回演化链上的所有中间状态。
    """
    chain = []
    current = state
    current_S = discrete_entropy(current)
    step = 0
    max_steps = 64

    while step < max_steps:
        focus_bit, stress_type = max_stress_trigger(current)
        next_state = flip_bit(current, focus_bit)
        next_S = discrete_entropy(next_state)

        # Entropy Lock：封闭系统下熵必须递增
        if next_S <= current_S:
            break

        next_hex = get_hexagram_name(next_state.inner_bits(), next_state.outer_bits())
        hex_index, physics_name, physics_desc = get_hex_state(next_state)
        chain.append({
            "step": step + 1,
            "triggered_bit": focus_bit,
            "stress_type": stress_type,
            "bits": next_state.full_bits(),
            "hexagram": next_hex,
            "hex_index": hex_index,
            "physics_name": physics_name,
            "entropy_S": next_S,
            "conf_m1": conf_m1(next_state),
        })
        current = next_state
        current_S = next_S
        step += 1

    return chain


def path4_meta_reset_or_invert(state: FSMState) -> dict:
    """
    路径四：元级别重置与倒置 (Meta-Level Reversal)

    两种模式：
    - 极性反转（错）：全部 6 bits 同时翻转
    - 参照系倒置（综）：矩阵上下倒置（Bit1↔Bit6）
    """
    results = {}

    # 极性反转（错）：1变0，0变1
    invert_B = [1 - b for b in state.B]
    invert_state = FSMState.from_bits("".join(str(b) for b in invert_B))
    invert_hex = get_hexagram_name(invert_state.inner_bits(), invert_state.outer_bits())
    invert_idx, invert_name, invert_desc = get_hex_state(invert_state)
    results["错_极性反转"] = {
        "operation": "错卦（全翻）",
        "bits": "".join(str(b) for b in invert_B),
        "hexagram": invert_hex,
        "hex_index": invert_idx,
        "physics_name": invert_name,
        "physics_desc": invert_desc,
        "entropy_S": discrete_entropy(invert_state),
        "conf_m1": conf_m1(invert_state),
    }

    # 参照系倒置（综）：B[1]↔B[6]，B[2]↔B[5]，B[3]↔B[4]
    reversed_B = state.B.copy()
    reversed_B[0], reversed_B[5] = reversed_B[5], reversed_B[0]
    reversed_B[1], reversed_B[4] = reversed_B[4], reversed_B[1]
    reversed_B[2], reversed_B[3] = reversed_B[3], reversed_B[2]
    reversed_state = FSMState.from_bits("".join(str(b) for b in reversed_B))
    reversed_hex = get_hexagram_name(reversed_state.inner_bits(), reversed_state.outer_bits())
    reversed_idx, reversed_name, reversed_desc = get_hex_state(reversed_state)
    results["综_参照系倒置"] = {
        "operation": "综卦（倒置）",
        "bits": "".join(str(b) for b in reversed_B),
        "hexagram": reversed_hex,
        "hex_index": reversed_idx,
        "physics_name": reversed_name,
        "physics_desc": reversed_desc,
        "entropy_S": discrete_entropy(reversed_state),
        "conf_m1": conf_m1(reversed_state),
    }

    return results


def route_evolution_path(state: FSMState,
                         delta_E_ext: float = 0.0,
                         deadlock_flag: bool = False,
                         time_in_state: int = 0) -> dict:
    """
    四路径路由判定算法（V11.0离散版）

    Returns:
        dict with path_number, description, and path-specific result
    """
    M = state.mass_M()

    # 路径四：元级别重置
    if deadlock_flag or delta_E_ext < -1000.0 * M:
        result = path4_meta_reset_or_invert(state)
        return {
            "path_number": 4,
            "path_name": "元级别重置与倒置",
            "description": "系统死锁或遭遇外部降维打击，执行极性反转或参照系倒置",
            "result": result,
        }

    # 路径三：宏观热力学衰变
    if M > M_THRESHOLD and delta_E_ext <= 0:
        chain = path3_macro_entropy_decay(state)
        return {
            "path_number": 3,
            "path_name": "宏观热力学衰变",
            "description": f"巨型系统(M={M})处于封闭状态，沿熵增DAG单向演化",
            "result": chain,
        }

    # 路径二：隐性内核暴露
    xor_inner = state.B[0] ^ state.B[1] if len(state.B) >= 2 else 0
    xor_outer = state.B[5] ^ state.B[4] if len(state.B) >= 2 else 0
    if (xor_inner == 1 or xor_outer == 1) and time_in_state > T_MASK:
        result = path2_hidden_core_exposure(state)
        return {
            "path_number": 2,
            "path_name": "隐性内核暴露",
            "description": "系统外壳与内核动力学方向冲突，潜伏超时后互卦演化",
            "result": result,
        }

    # 路径一：单点击穿（默认）
    result = path1_max_stress(state)
    return {
        "path_number": 1,
        "path_name": "微观单点击穿",
        "description": "系统处于日常演化，执行Max-Stress Trigger确定性翻转",
        "result": result,
    }


# =============================================================================
# V11.0 SSOT 管线入口
# =============================================================================

def raw_physics_step(state: FSMState) -> FSMState:
    """
    SSOT管线：一步离散演化

    输入：raw physics (E, P, R, τ, B)
    输出：更新后的 E, P, B

    这是V11.0 SSOT管线的核心——所有状态变化均由物理输入计算得出，
    语义层仅做标注，不参与计算。

    每tick执行：
    1. 对每个节点应用 E_i(t) = E_i(t-1) - R_i*α(B_down)
                        P_i(t) = P_i(t-1) + C_i*B_up
    2. 检查触发条件
    3. 返回更新后的状态

    注意：此函数仅更新E和P，不执行flip。Flip由调用者显式调用。
    """
    new_E = []
    new_P = []

    for i in range(1, 7):
        idx = i - 1
        B_down = state.B[idx - 1] if idx > 0 else 0
        B_up = state.B[idx + 1] if idx < 5 else 0

        new_E_i = step_energy(state.E[idx], state.R[idx], B_down)
        new_P_i = step_pressure(state.P[idx], state.C[idx], B_up)

        new_E.append(new_E_i)
        new_P.append(new_P_i)

    return FSMState(
        B=state.B.copy(),
        E=new_E,
        P=new_P,
        E_initial=state.E_initial.copy(),
        R=state.R.copy(),
        R_base=state.R_base.copy(),
        tau=state.tau.copy(),
        C=state.C.copy(),
    )


def compute_system_confidence(state: FSMState) -> dict:
    """
    计算系统置信度详情（V11.0可伪性协议支持）

    Returns:
        dict with conf_m1, U_E, U_P, U_R, mean_sigma, std_sigma
    """
    U_E, U_P, U_R = compute_U(state)
    mc_mean, mc_std = monte_carlo_stress(state)
    return {
        "conf_m1": conf_m1(state),
        "U_E": U_E,
        "U_P": U_P,
        "U_R": U_R,
        "mc_mean_sigma": mc_mean,
        "mc_std_sigma": mc_std,
    }


# =============================================================================
# 便捷入口类
# =============================================================================

class FSMKernel:
    """
    影子协议 V11.0 — 离散自动机确定性 FSM 内核

    使用方式：
        kernel = FSMKernel(bits="111000")
        result = kernel.evolve(delta_E_ext=0.0, deadlock_flag=False)
        preview = kernel.simulate()
        confidence = kernel.confidence()
    """

    def __init__(self, bits: str = "000000",
                 E0: float = DEFAULT_E0, P0: float = DEFAULT_P0):
        self.state = FSMState.from_bits(bits, E0=E0, P0=P0)
        self._history: list[str] = []

    def evolve(self, delta_E_ext: float = 0.0,
               deadlock_flag: bool = False,
               time_in_state: int = 0) -> dict:
        """执行一次确定性演化"""
        self._history.append(self.state.full_bits())
        result = route_evolution_path(
            self.state, delta_E_ext, deadlock_flag, time_in_state
        )
        r = result.get("result", {})
        if result["path_number"] == 1:
            self.state = r["next_state"]
        elif result["path_number"] == 2:
            self.state = r["next_state"]
        elif result["path_number"] == 3:
            if r:
                last = r[-1]
                bits = last.get("bits", self.state.full_bits())
                self.state = FSMState.from_bits(bits)
        elif result["path_number"] == 4:
            if "错_极性反转" in r:
                invert_bits = r["错_极性反转"]["bits"]
                self.state = FSMState.from_bits(invert_bits)
        return result

    def simulate(self) -> list[dict]:
        """返回 6 种 Bit Flip 预览"""
        return simulate_all_flips(self.state)

    def get_current_node(self) -> dict:
        """获取当前节点的完整信息"""
        hex_index, physics_name, physics_desc = get_hex_state(self.state)
        hexagram = get_hexagram_name(self.state.inner_bits(), self.state.outer_bits())
        conf = compute_system_confidence(self.state)
        return {
            "bits": self.state.full_bits(),
            "hexagram": hexagram,
            "hex_index": hex_index,
            "physics_name": physics_name,
            "physics_desc": physics_desc,
            "entropy_S": discrete_entropy(self.state),
            "mass_M": self.state.mass_M(),
            **conf,
        }

    def confidence(self) -> dict:
        """返回系统置信度详情"""
        return compute_system_confidence(self.state)

    def reset(self, bits: str = "000000"):
        """重置状态"""
        self.state = FSMState.from_bits(bits)
        self._history.clear()
