"""
测试 IChingStructuredChunker
"""

import pytest
from src.pipeline.chunker import IChingStructuredChunker
from src.models.schema import IChingMetadata


# Mock 数据：乾卦和坤卦
MOCK_HEXAGRAM_DATA = [
    {
        "卦名": "乾",
        "卦序": 1,
        "章节": "上经",
        "卦辞": "元亨利贞",
        "彖传": "大哉乾元，万物资始，乃统天。云行雨施，品物流形。大明始终，六位时成，时乘六龙以御天。乾道变化，各正性命，保合大和，乃利贞。首出庶物，万国咸宁。",
        "大象传": "天行健，君子以自强不息",
        "爻": [
            {
                "位置": "初九",
                "爻辞": "潜龙勿用",
                "象传": "潜龙勿用，阳在下也"
            },
            {
                "位置": "九二",
                "爻辞": "见龙在田，利见大人",
                "象传": "见龙在田，德施普也"
            },
            {
                "位置": "九三",
                "爻辞": "君子终日乾乾，夕惕若厉，无咎",
                "象传": "终日乾乾，反复道也"
            },
            {
                "位置": "九四",
                "爻辞": "或跃在渊，无咎",
                "象传": "或跃在渊，进无咎也"
            },
            {
                "位置": "九五",
                "爻辞": "飞龙在天，利见大人",
                "象传": "飞龙在天，大人造也"
            },
            {
                "位置": "上九",
                "爻辞": "亢龙有悔",
                "象传": "亢龙有悔，盈不可久也"
            }
        ]
    },
    {
        "卦名": "坤",
        "卦序": 2,
        "章节": "上经",
        "卦辞": "元亨，利牝马之贞。君子有攸往，先迷后得主，利西南得朋，东北丧朋。安贞吉。",
        "彖传": "至哉坤元，万物资生，乃顺承天。坤厚载物，德合无疆。含弘光大，品物咸亨。牝马地类，行地无疆，柔顺利贞。君子攸行，先迷失道，后顺得常。西南得朋，乃与类行。东北丧朋，乃终有庆。安贞之吉，应地无疆。",
        "大象传": "地势坤，君子以厚德载物",
        "爻": [
            {
                "位置": "初六",
                "爻辞": "履霜，坚冰至",
                "象传": "履霜坚冰，阴始凝也。驯致其道，至坚冰也"
            },
            {
                "位置": "六二",
                "爻辞": "直方大，不习无不利",
                "象传": "直方大，不习无不利，地道光也"
            },
            {
                "位置": "六三",
                "爻辞": "含章可贞，或从王事，无成有终",
                "象传": "含章可贞，以时发也。或从王事，知光大也"
            },
            {
                "位置": "六四",
                "爻辞": "括囊，无咎无誉",
                "象传": "括囊无咎，慎不害也"
            },
            {
                "位置": "六五",
                "爻辞": "黄裳，元吉",
                "象传": "黄裳元吉，文在中也"
            },
            {
                "位置": "上六",
                "爻辞": "龙战于野，其血玄黄",
                "象传": "龙战于野，其道穷也"
            }
        ]
    }
]


class TestIChingStructuredChunker:
    """测试《周易》分块器"""

    def test_parse_hexagram(self):
        """测试解析单个卦"""
        chunker = IChingStructuredChunker()
        chunks = chunker.parse_hexagram(MOCK_HEXAGRAM_DATA[0])  # 乾卦

        # 验证产出的块数量
        # 1 卦辞 + 1 彖传 + 1 大象传 + 6 爻辞 + 6 象传 = 15
        assert len(chunks) == 15

        # 验证第一个块（卦辞）
        assert chunks[0].content == "元亨利贞"
        assert chunks[0].metadata.hexagram_name == "乾"
        assert chunks[0].metadata.hexagram_index == 1
        assert chunks[0].metadata.text_type == "卦辞"
        assert chunks[0].context == "乾卦卦辞：元亨利贞"

    def test_parse_yao_ci(self):
        """测试解析爻辞"""
        chunker = IChingStructuredChunker()
        chunks = chunker.parse_hexagram(MOCK_HEXAGRAM_DATA[0])  # 乾卦

        # 找到初九爻辞
        yao_chunks = [c for c in chunks if c.metadata.text_type == "爻辞"]
        assert len(yao_chunks) == 6

        # 验证初九
        first_yao = yao_chunks[0]
        assert first_yao.metadata.line_position == "初九"
        assert first_yao.metadata.yin_yang == "阳"  # 九 = 阳
        assert first_yao.content == "潜龙勿用"

    def test_parse_corpus(self):
        """测试解析整个语料库"""
        chunker = IChingStructuredChunker()
        chunks = chunker.parse_corpus(MOCK_HEXAGRAM_DATA)

        # 乾卦 15 + 坤卦 15 = 30
        assert len(chunks) == 30

    def test_element_and_symbol(self):
        """测试元素类型和符号映射"""
        chunker = IChingStructuredChunker()

        # 乾卦 - 金
        chunks = chunker.parse_hexagram(MOCK_HEXAGRAM_DATA[0])
        assert chunks[0].metadata.element_type == "金"
        assert chunks[0].metadata.symbol == "☰"

        # 坤卦 - 土
        chunks = chunker.parse_hexagram(MOCK_HEXAGRAM_DATA[1])
        assert chunks[0].metadata.element_type == "土"
        assert chunks[0].metadata.symbol == "☷"

    def test_yin_yang_detection(self):
        """测试阴阳检测"""
        chunker = IChingStructuredChunker()

        # 乾卦初九 - 阳爻
        chunks = chunker.parse_hexagram(MOCK_HEXAGRAM_DATA[0])
        yao_chunks = [c for c in chunks if c.metadata.text_type == "爻辞"]
        assert yao_chunks[0].metadata.yin_yang == "阳"  # 初九

        # 坤卦初六 - 阴爻
        chunks = chunker.parse_hexagram(MOCK_HEXAGRAM_DATA[1])
        yao_chunks = [c for c in chunks if c.metadata.text_type == "爻辞"]
        assert yao_chunks[0].metadata.yin_yang == "阴"  # 初六


if __name__ == "__main__":
    pytest.main([__file__, "-v"])