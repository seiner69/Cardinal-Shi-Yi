"""
LLM Chain - 基于 6-Bit FSM 架构的历史事件分析
"""

import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 尝试导入 Anthropic SDK (MiniMax)
try:
    import anthropic
except ImportError:
    anthropic = None

from src.models.schema import FSMOutput
from src.db.faiss_client import FAISSIChingClient
from .prompts import get_fsm_system_prompt, get_fsm_intent_rewrite_prompt

load_dotenv()


# 三爻卦到符号的映射
TRIGRAM_MAP = {
    "000": {"name": "坤", "symbol": "☷", "gua": "坤"},
    "001": {"name": "震", "symbol": "☳", "gua": "震"},
    "010": {"name": "坎", "symbol": "☵", "gua": "坎"},
    "011": {"name": "兑", "symbol": "☱", "gua": "兑"},
    "100": {"name": "巽", "symbol": "☴", "gua": "巽"},
    "101": {"name": "离", "symbol": "☲", "gua": "离"},
    "110": {"name": "艮", "symbol": "☶", "gua": "艮"},
    "111": {"name": "乾", "symbol": "☰", "gua": "乾"},
}

# 六爻卦查找表 (outer_bits + inner_bits -> 卦名)
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


def get_hexagram_info(inner_bits: str, outer_bits: str) -> Dict[str, Any]:
    """
    根据 6-Bit 代码获取卦象信息

    Args:
        inner_bits: 内系统3位代码 (Bit 1-3，对应下卦)
        outer_bits: 外系统3位代码 (Bit 4-6，对应上卦)

    Returns:
        包含卦名的字典
    """
    if len(inner_bits) != 3 or len(outer_bits) != 3:
        return {"hexagram": None, "inner_trigram": None, "outer_trigram": None}

    inner_gua = inner_bits  # Bit 1-3
    outer_gua = outer_bits  # Bit 4-6

    inner_trigram = TRIGRAM_MAP.get(inner_gua, {})
    outer_trigram = TRIGRAM_MAP.get(outer_gua, {})

    # 查找六爻卦 (外卦+内卦)
    key = (TRIGRAM_MAP.get(outer_gua, {}).get("name", "") +
           TRIGRAM_MAP.get(inner_gua, {}).get("name", ""))
    hexagram_name = HEXAGRAM_LOOKUP.get(key, key or None)

    return {
        "hexagram": hexagram_name,
        "inner_trigram": inner_trigram.get("name", ""),
        "outer_trigram": outer_trigram.get("name", ""),
        "inner_symbol": inner_trigram.get("symbol", "☷"),
        "outer_symbol": outer_trigram.get("symbol", "☰"),
        "inner_bits": inner_gua,
        "outer_bits": outer_gua,
    }



def derive_target_hexagram(
    inner_bits: str,
    outer_bits: str,
    stress_type: str,
    focus_bit: int
) -> Dict[str, str]:
    """
    根据 Bit 变化自动推导目标卦象

    规则：将指定Bit位翻转（1->0 或 0->1），计算新的6位代码对应的卦象

    Args:
        inner_bits: 内系统3位代码 (Bit1-Bit3，对应初爻到三爻)
        outer_bits: 外系统3位代码 (Bit4-Bit6，对应四爻到上爻)
        stress_type: 应力类型（向下断裂/向上撞墙/稳定）
        focus_bit: 能量聚焦的Bit位 (1-6)

    Returns:
        包含目标卦象和理由的字典
    """
    # 合并为6位代码 (Bit1在下，Bit6在上)
    full_bits = inner_bits + outer_bits  # 例如 "101111"

    if len(full_bits) != 6 or focus_bit < 1 or focus_bit > 6:
        return {"hexagram": "乾", "reason": "参数错误"}

    # 翻转指定Bit
    bit_list = list(full_bits)
    bit_idx = focus_bit - 1  # Bit1对应索引0
    bit_list[bit_idx] = "0" if bit_list[bit_idx] == "1" else "1"
    new_bits = "".join(bit_list)

    # 分离新的内卦和外卦
    new_inner_bits = new_bits[:3]  # Bit1-Bit3
    new_outer_bits = new_bits[3:]  # Bit4-Bit6

    # 获取新卦象
    new_hex_info = get_hexagram_info(new_inner_bits, new_outer_bits)
    target_hex = new_hex_info.get("hexagram", "")

    if not target_hex:
        return {"hexagram": "乾", "reason": "推导失败"}

    # 构建理由
    original_hex_info = get_hexagram_info(inner_bits, outer_bits)
    original_hex = original_hex_info.get("hexagram", "")
    changed_bit_name = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"][focus_bit - 1]
    original_val = full_bits[bit_idx]
    new_val = bit_list[bit_idx]

    if stress_type == "向下断裂":
        direction = "降维"
    elif stress_type == "向上撞墙":
        direction = "突围"
    else:
        direction = "调整"

    reason = f"{original_hex}卦({full_bits})的{changed_bit_name}从{original_val}变{new_val}，{direction}为{target_hex}卦({new_bits})"

    return {
        "hexagram": target_hex,
        "reason": reason
    }


class IChingChain:
    """
    史易枢机 LLM Chain - 6-Bit FSM 分析引擎

    编排流程：
    1. 意图重写 - 提取关键词，预测卦象/爻位
    2. 知识库检索 - 在 FAISS 中检索周易知识库
    3. FSM 生成 - 调用大模型生成 6-Bit FSM 分析结果
    """

    def __init__(
        self,
        milvus_client: Optional[FAISSIChingClient] = None,
        model: str = "MiniMax-M2.7",
    ):
        """初始化 Chain"""
        self.milvus_client = milvus_client or FAISSIChingClient()
        self.model = model

        # 优先使用 MiniMax API
        minimax_key = os.getenv("MINIMAX_API_KEY")
        if minimax_key and minimax_key != "your_minimax_api_key_here":
            self.client = anthropic.Anthropic(api_key=minimax_key)
            self._has_api_key = True
        else:
            self.client = None
            self._has_api_key = False
            print("[WARNING] 未配置 API Key，将使用模拟模式")

    def _call_llm(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """
        调用大模型 (MiniMax-M2.7)

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大输出token数

        Returns:
            模型输出文本
        """
        if not self._has_api_key:
            return self._mock_fsm_response(messages)

        # 转换 messages 格式为 Anthropic format
        # system 字段提取
        system_content = ""
        anthropic_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
            else:
                anthropic_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_content,
            messages=anthropic_messages,
            temperature=temperature,
        )

        # 收集文本输出
        text_output = ""
        for block in response.content:
            if block.type == "text":
                text_output += block.text
            elif block.type == "thinking":
                # 可选：存储 thinking 输出
                pass
        return text_output

    def _mock_fsm_response(self, messages: list[dict]) -> str:
        """Mock LLM FSM response for testing"""
        return json.dumps({
            "inner_system": "Target: Han Xin, military genius",
            "outer_system": "Political environment: Empress Lu + Liu Bang",
            "inner_bits": "100",
            "outer_bits": "110",
            "bit_analysis": [
                {"bit_position": 1, "value": "1", "description": "Han Xin still has military power"},
                {"bit_position": 2, "value": "0", "description": "Han Xin has no official position"},
                {"bit_position": 3, "value": "0", "description": "Han Xin just wants to survive"},
                {"bit_position": 4, "value": "1", "description": "Face physical threat from Empress Lu"},
                {"bit_position": 5, "value": "1", "description": "Founding generals will be purged"},
                {"bit_position": 6, "value": "0", "description": "Liu Bang exists but cannot control Empress Lu"}
            ],
            "energy_focus": {
                "focus_bit": 1,
                "focus_description": "Core anxiety: military support being undermined"
            },
            "stress_analysis": {
                "stress_type": "向下断裂",
                "analysis": "Energy focused on Bit1 (military) with no support below, collapse inevitable"
            },
            "mutation_suggestion": "Surrender remaining military power, transform from 1 to 0",
            "target_hexagram": "坤",
            "hexagram_reason": "Kun represents complete surrender and承载",
            "referenced_yao": "六五：黄裳，元吉",
            "yao_interpretation": "After collapse, remain low and humble to survive"
        }, ensure_ascii=False, indent=2)

    def rewrite_intent(self, history_input: str) -> dict:
        """
        Step A: Intent rewrite

        Args:
            history_input: User input historical fragment

        Returns:
            Dict with keywords, predicted hexagrams, rewritten query
        """
        prompt = get_fsm_intent_rewrite_prompt(history_input)
        messages = [
            {"role": "system", "content": "You are an assistant skilled at understanding user intent."},
            {"role": "user", "content": prompt}
        ]

        response = self._call_llm(messages)

        # Parse JSON
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "keywords": [],
                "predicted_hexagrams": [],
                "possible_line_positions": [],
                "rewritten_query": history_input
            }

    def search_knowledge_base(
        self,
        query_text: str = "",
        hexagram_filter: Optional[str] = None,
        text_type_filter: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Step B: 知识库检索 (适配 ChromaDB)

        Args:
            query_text: 查询文本
            hexagram_filter: 卦名过滤（如"乾"）
            text_type_filter: 文本类型过滤（如"爻辞"）
            limit: 返回数量

        Returns:
            检索结果列表
        """
        # ChromaDB 使用文本查询
        if not query_text:
            query_text = "历史 周易"

        # 构建 ChromaDB 过滤条件
        chroma_filter = None
        if hexagram_filter:
            chroma_filter = {"hexagram_name": hexagram_filter}
        elif text_type_filter:
            chroma_filter = {"text_type": text_type_filter}

        try:
            results = self.milvus_client.search_with_score(
                query=query_text,
                k=limit,
                filter=chroma_filter
            )
            return results
        except Exception as e:
            print(f"[ERROR] 知识库检索失败: {e}")
            return []

    def generate_fsm_analysis(
        self,
        history_context: str,
        iching_context: str,
    ) -> FSMOutput:
        """
        Step C: FSM 分析生成

        Args:
            history_context: 历史背景
            iching_context: 周易相关内容

        Returns:
            FSMOutput 结构化输出
        """
        # 获取填充后的 FSM System Prompt
        system_prompt = get_fsm_system_prompt(
            history_context=history_context,
            iching_context=iching_context
        )

        user_prompt = """请根据上述历史背景，输出 6-Bit FSM 结构化分析。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self._call_llm(messages)

        # 解析 JSON 响应
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response)

            # 容错处理 stress_type
            stress_type = data.get("stress_analysis", {}).get("stress_type", "稳定")
            if "断裂" in stress_type:
                stress_type = "向下断裂"
            elif "撞墙" in stress_type:
                stress_type = "向上撞墙"
            else:
                stress_type = "稳定"
            data["stress_analysis"]["stress_type"] = stress_type

            return FSMOutput(**data)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[WARNING] 解析 LLM 响应失败: {e}")
            # 返回默认结构
            return FSMOutput(
                inner_system="解析失败",
                outer_system="",
                inner_bits="000",
                outer_bits="000",
                bit_analysis=[],
                energy_focus={"focus_bit": 0, "focus_description": "解析失败"},
                stress_analysis={"stress_type": "稳定", "analysis": "解析失败"},
                mutation_suggestion="",
                target_hexagram="",
                hexagram_reason="",
                referenced_yao="",
                yao_interpretation=""
            )

    def run(
        self,
        history_input: str,
    ) -> tuple[FSMOutput, list[dict]]:
        """
        运行完整的 6-Bit FSM Chain

        Args:
            history_input: 用户输入的历史片段

        Returns:
            (FSMOutput 结构化输出, 检索结果列表)
        """
        # Step A: Intent rewrite
        print("[INFO] Step A: Intent rewrite...")
        intent_result = self.rewrite_intent(history_input)

        # Step B: Knowledge base search
        print("[INFO] Step B: Knowledge base search...")
        hexagram = intent_result.get("predicted_hexagrams", [None])[0]
        text_type = intent_result.get("text_type", None)
        query_text = intent_result.get("rewritten_query", history_input)

        search_results = self.search_knowledge_base(
            query_text=query_text,
            hexagram_filter=hexagram,
            text_type_filter=text_type,
            limit=5
        )

        # Format search results as context
        iching_context = self._format_search_results(search_results)

        # Step C: FSM analysis generation
        print("[INFO] Step C: FSM analysis generation...")
        analysis = self.generate_fsm_analysis(
            history_context=history_input,
            iching_context=iching_context
        )

        # Step D: Auto-derive target hexagram if not provided or override
        derived = derive_target_hexagram(
            inner_bits=analysis.inner_bits,
            outer_bits=analysis.outer_bits,
            stress_type=analysis.stress_analysis.stress_type,
            focus_bit=analysis.energy_focus.focus_bit
        )

        # Override with auto-derived values
        analysis.target_hexagram = derived["hexagram"]
        analysis.hexagram_reason = derived["reason"]

        return analysis, search_results

    def _format_search_results(self, results: list[dict]) -> str:
        """格式化检索结果为文本"""
        if not results:
            return "未检索到相关内容"

        lines = []
        for i, r in enumerate(results, 1):
            context = r.get("context", r.get("content", ""))
            hexagram = r.get("hexagram_name", "")
            text_type = r.get("text_type", "")
            lines.append(f"{i}. [{hexagram}]{text_type}: {context}")

        return "\n".join(lines)


# 便捷函数
def get_chain() -> IChingChain:
    """获取默认 Chain"""
    return IChingChain()