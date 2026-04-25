"""
《周易》数据处理管道 - 语义块分块器
将嵌套 JSON 解析为最细粒度的独立语义单元
"""

import json
import uuid
from typing import Any, Optional
from src.models.schema import (
    IChingMetadata,
    ProcessedChunk,
    Literal,
)


# 八卦符号映射
HEXAGRAM_SYMBOLS = {
    "乾": "☰", "兑": "☱", "离": "☲", "震": "☳",
    "巽": "☴", "坎": "☵", "艮": "☶", "坤": "☷"
}

# 先天八卦序（用于确定符号）
HEXAGRAM_ORDER = {
    "乾": 1, "兑": 2, "离": 3, "震": 4,
    "巽": 5, "坎": 6, "艮": 7, "坤": 8
}

# 元素类型映射（根据卦名确定五行）
# 乾兑属金，离属火，震巽属木，坎属水，艮坤属土
ELEMENT_MAPPING = {
    "乾": "金", "兑": "金", "离": "火", "震": "木",
    "巽": "木", "坎": "水", "艮": "土", "坤": "土"
}

# 阴阳映射：阳爻用 九，阴爻用 六
YIN_YANG_MAPPING = {
    "九": "阳", "六": "阴"
}


class IChingStructuredChunker:
    """
    《周易》结构化分块器

    将《周易》的嵌套 JSON 格式解析为最细粒度的独立语义单元：
    - 卦辞（整个卦的象辞）
    - 彖传（解释卦辞的传文）
    - 爻辞（每一爻的占辞）
    - 象传（解释爻辞的传文）
    - 大象传（解释卦象的整体传文）
    """

    def __init__(self):
        self.hexagram_cache: dict[str, dict] = {}

    def _get_element(self, hexagram_name: str) -> str:
        """获取卦象的五行属性"""
        base_hexagram = hexagram_name[0] if len(hexagram_name) > 0 else hexagram_name
        return ELEMENT_MAPPING.get(base_hexagram, "土")

    def _get_symbol(self, hexagram_name: str) -> Optional[str]:
        """获取卦象符号"""
        base_hexagram = hexagram_name[0] if len(hexagram_name) > 0 else hexagram_name
        return HEXAGRAM_SYMBOLS.get(base_hexagram)

    def _get_yin_yang(self, line_position: str) -> str:
        """根据爻位判断阴阳（九=阳，六=阴）"""
        if not line_position:
            return "阳"  # 默认为阳
        # 检查是否包含"九"（阳）或"六"（阴）
        if "九" in line_position:
            return "阳"
        if "六" in line_position:
            return "阴"
        return "阳"

    def _parse_line_position(self, line_data: dict) -> Optional[str]:
        """解析爻位信息"""
        if "位置" in line_data:
            return line_data["位置"]
        return None

    def parse_hexagram(self, hexagram_data: dict) -> list[ProcessedChunk]:
        """
        解析单个卦的数据，产出语义块列表

        Args:
            hexagram_data: 包含卦名、卦辞、爻辞等信息的字典

        Returns:
            ProcessedChunk 列表
        """
        chunks = []
        hexagram_name = hexagram_data.get("卦名", "")
        hexagram_index = hexagram_data.get("卦序", 0)
        element_type = self._get_element(hexagram_name)
        symbol = self._get_symbol(hexagram_name)

        # === 1. 解析卦辞 ===
        if "卦辞" in hexagram_data:
            context = f"{hexagram_name}卦卦辞：{hexagram_data['卦辞']}"
            chunks.append(ProcessedChunk(
                chunk_id=str(uuid.uuid4()),
                content=hexagram_data["卦辞"],
                context=context,
                metadata=IChingMetadata(
                    hexagram_name=hexagram_name,
                    hexagram_index=hexagram_index,
                    element_type=element_type,  # type: ignore
                    line_position=None,
                    yin_yang="阳",  # 卦辞整体为阳
                    symbol=symbol,
                    text_type="卦辞",
                    chapter=hexagram_data.get("章节")
                )
            ))

        # === 2. 解析彖传 ===
        if "彖传" in hexagram_data:
            context = f"{hexagram_name}卦彖传：{hexagram_data['彖传']}"
            chunks.append(ProcessedChunk(
                chunk_id=str(uuid.uuid4()),
                content=hexagram_data["彖传"],
                context=context,
                metadata=IChingMetadata(
                    hexagram_name=hexagram_name,
                    hexagram_index=hexagram_index,
                    element_type=element_type,  # type: ignore
                    line_position=None,
                    yin_yang="阳",
                    symbol=symbol,
                    text_type="彖传",
                    chapter=hexagram_data.get("章节")
                )
            ))

        # === 3. 解析大象传 ===
        if "大象传" in hexagram_data:
            context = f"{hexagram_name}卦大象传：{hexagram_data['大象传']}"
            chunks.append(ProcessedChunk(
                chunk_id=str(uuid.uuid4()),
                content=hexagram_data["大象传"],
                context=context,
                metadata=IChingMetadata(
                    hexagram_name=hexagram_name,
                    hexagram_index=hexagram_index,
                    element_type=element_type,  # type: ignore
                    line_position=None,
                    yin_yang="阳",
                    symbol=symbol,
                    text_type="大象传",
                    chapter=hexagram_data.get("章节")
                )
            ))

        # === 4. 解析爻辞 ===
        if "爻" in hexagram_data:
            for line in hexagram_data["爻"]:
                line_position = self._parse_line_position(line)
                yin_yang = self._get_yin_yang(line_position or "")

                # 4.1 爻辞
                if "爻辞" in line:
                    context = f"{hexagram_name}-{line_position}爻辞：{line['爻辞']}"
                    chunks.append(ProcessedChunk(
                        chunk_id=str(uuid.uuid4()),
                        content=line["爻辞"],
                        context=context,
                        metadata=IChingMetadata(
                            hexagram_name=hexagram_name,
                            hexagram_index=hexagram_index,
                            element_type=element_type,  # type: ignore
                            line_position=line_position,
                            yin_yang=yin_yang,  # type: ignore
                            symbol=symbol,
                            text_type="爻辞",
                            chapter=hexagram_data.get("章节")
                        )
                    ))

                # 4.2 象传（每爻的象传）
                if "象传" in line:
                    context = f"{hexagram_name}-{line_position}象传：{line['象传']}"
                    chunks.append(ProcessedChunk(
                        chunk_id=str(uuid.uuid4()),
                        content=line["象传"],
                        context=context,
                        metadata=IChingMetadata(
                            hexagram_name=hexagram_name,
                            hexagram_index=hexagram_index,
                            element_type=element_type,  # type: ignore
                            line_position=line_position,
                            yin_yang=yin_yang,  # type: ignore
                            symbol=symbol,
                            text_type="象传",
                            chapter=hexagram_data.get("章节")
                        )
                    ))

        return chunks

    def parse_corpus(self, corpus_data: list[dict]) -> list[ProcessedChunk]:
        """
        解析整个《周易》语料库

        Args:
            corpus_data: 包含多个卦的列表

        Returns:
            所有语义块的列表
        """
        all_chunks = []
        for hexagram in corpus_data:
            chunks = self.parse_hexagram(hexagram)
            all_chunks.extend(chunks)
        return all_chunks

    def parse_json_file(self, file_path: str) -> list[ProcessedChunk]:
        """
        从 JSON 文件加载并解析

        Args:
            file_path: JSON 文件路径

        Returns:
            语义块列表
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.parse_corpus(data)