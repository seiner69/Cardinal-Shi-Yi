"""
《周易》元数据结构定义 - Pydantic Models
定义卦象、爻位、元素类型等核心元数据
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class IChingMetadata(BaseModel):
    """《周易》语义单元的元数据"""

    # 卦名：如"乾"、"坤"、"屯"等
    hexagram_name: str = Field(..., description="卦名")

    # 卦序号：1-64
    hexagram_index: int = Field(..., ge=1, le=64, description="卦序(1-64)")

    # 元素类型：五行属性
    element_type: Literal["木", "火", "土", "金", "水"] = Field(
        ..., description="五行属性"
    )

    # 爻位：初九、九二、九三、九四、九五、上九；初六、六二、六三、六四、六五、上六
    # 格式：line_position (如 "九二")
    line_position: Optional[str] = Field(
        default=None,
        description="爻位标识(如初九、九二、六五等)"
    )

    # 阴阳属性
    yin_yang: Literal["阳", "阴"] = Field(..., description="阴阳属性")

    # 卦象符号表示（可选，用于可视化）
    symbol: Optional[str] = Field(
        default=None,
        description="卦象符号(如☰、☵等)"
    )

    # 文本类型：卦辞、彖传、爻辞、象传、大象传等
    text_type: Literal["卦辞", "彖传", "爻辞", "象传", "大象传", "文言"] = Field(
        ..., description="文本类型"
    )

    # 所属章节/卷次（可选）
    chapter: Optional[str] = Field(
        default=None,
        description="所属章节"
    )


class SearchFilter(BaseModel):
    """Milvus 检索的过滤条件"""

    hexagram_name: Optional[str] = Field(default=None, description="卦名过滤")
    hexagram_index: Optional[int] = Field(default=None, ge=1, le=64, description="卦序过滤")
    element_type: Optional[str] = Field(default=None, description="五行过滤")
    yin_yang: Optional[str] = Field(default=None, description="阴阳过滤")
    text_type: Optional[str] = Field(default=None, description="文本类型过滤")


class ProcessedChunk(BaseModel):
    """处理后的语义块"""

    # 块 ID
    chunk_id: str = Field(..., description="唯一标识符")

    # 块文本内容
    content: str = Field(..., description="文本内容")

    # 完整上下文（如"乾卦-初九爻辞：潜龙勿用"）
    context: str = Field(..., description="完整上下文")

    # 元数据
    metadata: IChingMetadata = Field(..., description="元数据")

    # 向量维度（嵌入后由外部填充）
    embedding: Optional[list[float]] = Field(default=None, description="向量嵌入")


class HistoryContext(BaseModel):
    """历史片段输入"""

    # 历史文本
    text: str = Field(..., description="历史片段文本")

    # 时间朝代（如"春秋"、"战国"）
    dynasty: Optional[str] = Field(default=None, description="所属朝代")

    # 关键人物（如"孔子"、"秦始皇"）
    key_persons: Optional[list[str]] = Field(default=None, description="关键人物")

    # 事件类型
    event_type: Optional[str] = Field(default=None, description="事件类型")


class SystemDefinition(BaseModel):
    """系统界定"""
    primary_system: str = Field(..., description="主分析系统")
    secondary_systems: list[str] = Field(default_factory=list, description="次级系统列表")
    system_relationship: str = Field(..., description="系统间关系描述")


class HexagramReference(BaseModel):
    """卦象引用（含系统标注）"""
    hexagram: str = Field(..., description="卦名")
    system: str = Field(..., description="所属系统")
    reason: str = Field(default="", description="引用原因")


# ==============================================================================
# 6-Bit FSM 分析模型
# ==============================================================================

class BitAnalysis(BaseModel):
    """单Bit分析结果"""
    bit_position: int = Field(..., description="Bit位置 (1-6)")
    value: Literal["0", "1"] = Field(..., description="赋值")
    description: str = Field(..., description="该Bit的事实依据")


class EnergyFocus(BaseModel):
    """能量聚焦层（执行指针）"""
    focus_bit: int = Field(..., description="聚焦的Bit位 (1-6)")
    focus_description: str = Field(..., description="核心焦虑描述")


class StressAnalysis(BaseModel):
    """受力分析"""
    stress_type: Literal["向下断裂", "向上撞墙", "稳定"] = Field(..., description="应力类型")
    analysis: str = Field(..., description="受力分析详情")


class FSMNode(BaseModel):
    """当前节点快照 — V2.0 确定性硬算"""
    index: int = Field(..., description="节点序号 1-64，0=未定义")
    name: str = Field(..., description="卦名")
    code: str = Field(..., description="6位代码")
    physics_description: str = Field(..., description="物理状态描述")
    entropy_S: float = Field(..., description="系统总熵")
    mass_M: int = Field(..., description="系统总质量（1的数量）")


class DeterministicResult(BaseModel):
    """V2.0 确定性硬算结果"""
    current_node: FSMNode = Field(..., description="当前节点快照")
    max_stress_bit: int = Field(..., description="唯一动爻 Bit 位（1-6）")
    stress_type: str = Field(..., description="应力类型：燃料耗尽/压强击穿/稳态")
    evolution_path: int = Field(..., description="演化路径：1/2/3/4")
    evolution_path_name: str = Field(..., description="演化路径名称")
    all_possible_moves: list[FSMNode] = Field(default_factory=list, description="6种Bit Flip预览")
    next_state: Optional[FSMNode] = Field(default=None, description="确定性下一状态")


class FSMOutput(BaseModel):
    """6-Bit FSM 分析输出"""
    # Step 1: 参照系
    inner_system: str = Field(..., description="内系统定义")
    outer_system: str = Field(..., description="外系统定义")

    # Step 2: 6-Bit 代码
    inner_bits: str = Field(..., description="内系统3位代码，如 '100'")
    outer_bits: str = Field(..., description="外系统3位代码，如 '010'")
    bit_analysis: list[BitAnalysis] = Field(..., description="每位赋值的事实依据")

    # Step 3: 执行指针
    energy_focus: EnergyFocus = Field(..., description="能量聚焦位置")

    # Step 4: 物理力学硬算
    stress_analysis: StressAnalysis = Field(..., description="受力分析结果")

    # Step 5: 变爻建议
    mutation_suggestion: str = Field(..., description="变爻建议（降维或升维）")
    target_hexagram: str = Field(..., description="目标卦象")
    hexagram_reason: str = Field(..., description="卦象选择理由")

    # 辅助：调用的周易爻辞
    referenced_yao: str = Field(..., description="调用的爻辞原文")
    yao_interpretation: str = Field(..., description="爻辞的物理学翻译")

    # V2.0 确定性硬算层（可选，LLM模式时为空）
    deterministic: Optional[DeterministicResult] = Field(default=None, description="V2.0 确定性硬算结果")


class FinalAnalysis(BaseModel):
    """最终输出结构化解析"""

    # 系统界定
    system_definition: SystemDefinition = Field(..., description="系统界定")

    # 历史-易理映射分析
    mapping_analysis: str = Field(..., description="历史与易理的映射分析")

    # 局势转译
    situation_translation: str = Field(..., description="局势转译")

    # 权力图景
    power_landscape: str = Field(..., description="权力图景")

    # 易理投射
    iching_projection: str = Field(..., description="易理投射")

    # 天道人事
    heaven_human: str = Field(..., description="天道人事")

    # 参考的卦象/爻位（含系统标注）
    referenced_hexagrams: list[HexagramReference] = Field(
        default_factory=list,
        description="引用的卦象列表（含系统标注）"
    )