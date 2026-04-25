"""
测试 LLM Chain 和 Prompts
"""

import pytest
import json
from src.llm.prompts import get_system_prompt, get_intent_rewrite_prompt
from src.llm.chain import IChingChain


class TestPrompts:
    """测试 Prompt 管理"""

    def test_get_system_prompt_empty(self):
        """测试空参数的 System Prompt"""
        prompt = get_system_prompt()
        # 空参数时，填充默认值
        assert "[未提供历史背景]" in prompt
        assert "[未提供周易相关内容]" in prompt

    def test_get_system_prompt_with_context(self):
        """测试填充后的 System Prompt"""
        history = "春秋时期，孔子周游列国"
        iching = "乾卦九五：飞龙在天"

        prompt = get_system_prompt(history_context=history, iching_context=iching)

        assert history in prompt
        assert iching in prompt
        assert "{{history_context}}" not in prompt

    def test_get_intent_rewrite_prompt(self):
        """测试意图重写 Prompt"""
        history = "秦始皇统一六国"
        prompt = get_intent_rewrite_prompt(history)

        assert history in prompt
        assert "keywords" in prompt
        assert "predicted_hexagrams" in prompt


class TestIChingChain:
    """测试 LLM Chain"""

    def test_chain_init_without_api_key(self):
        """测试不带 API Key 初始化"""
        chain = IChingChain()
        assert chain.model == "gpt-4o"
        assert chain._has_api_key is False

    def test_mock_response(self):
        """测试模拟响应"""
        chain = IChingChain()
        response = chain._mock_response([])
        data = json.loads(response)

        assert "mapping_analysis" in data
        assert "situation_translation" in data
        assert "referenced_hexagrams" in data

    def test_format_search_results(self):
        """测试检索结果格式化"""
        chain = IChingChain()

        results = [
            {"context": "乾卦卦辞：元亨利贞", "hexagram_name": "乾", "text_type": "卦辞"},
            {"context": "坤卦卦辞：元亨", "hexagram_name": "坤", "text_type": "卦辞"},
        ]

        formatted = chain._format_search_results(results)
        assert "1. [乾]卦辞" in formatted
        assert "2. [坤]卦辞" in formatted

    def test_format_empty_results(self):
        """测试空结果格式化"""
        chain = IChingChain()
        formatted = chain._format_search_results([])
        assert "未检索到相关内容" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])