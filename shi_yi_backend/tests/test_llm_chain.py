"""
测试 LLM Chain 和 Prompts
"""

import pytest
import json
from src.llm.prompts import get_system_prompt, get_intent_rewrite_prompt
from src.llm.chain import IChingChain, derive_target_hexagram


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
        assert chain.model == "deepseek-v4-flash"

    def test_mock_response(self):
        """测试模拟响应"""
        chain = IChingChain()
        # 测试 format_search_results 方法存在
        assert hasattr(chain, '_format_search_results')

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

    def test_llm_call_falls_back_when_provider_fails(self):
        """供应商 API 失败时降级为模拟响应"""
        class BrokenMessages:
            def create(self, **kwargs):
                raise RuntimeError("provider unavailable")

        class BrokenClient:
            messages = BrokenMessages()

        chain = IChingChain()
        chain.client = BrokenClient()
        chain._has_api_key = True

        response = chain._call_llm([{"role": "user", "content": "测试"}])
        data = json.loads(response)

        assert data["inner_bits"] == "100"

    def test_run_tolerates_empty_predicted_hexagrams(self):
        """意图重写没有预测卦象时仍可继续检索和分析"""
        chain = IChingChain()
        chain._has_api_key = False
        chain.client = None
        chain.rewrite_intent = lambda history_input: {
            "keywords": [],
            "predicted_hexagrams": [],
            "possible_line_positions": [],
            "rewritten_query": history_input,
        }

        fsm_result, retrieval = chain.run("测试历史事件")

        assert fsm_result.inner_bits
        assert isinstance(retrieval, list)

    def test_stable_stress_does_not_create_false_mutation(self):
        result = derive_target_hexagram(
            inner_bits="100",
            outer_bits="010",
            stress_type="稳定",
            focus_bit=1,
        )

        assert result["hexagram"] == "屯"
        assert "不制造假变爻" in result["reason"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
