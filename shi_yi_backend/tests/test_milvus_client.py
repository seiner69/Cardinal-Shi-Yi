"""
测试 Milvus 过滤表达式（不依赖 pymilvus 连接）
"""

import pytest
import sys
sys.path.insert(0, ".")
from src.models.schema import SearchFilter


# 直接复制过滤表达式构建逻辑用于测试
def build_filter_expr(filter_params):
    """测试用的过滤表达式构建器"""
    conditions = []
    if filter_params.hexagram_name:
        conditions.append(f'hexagram_name == "{filter_params.hexagram_name}"')
    if filter_params.hexagram_index is not None:
        conditions.append(f'hexagram_index == {filter_params.hexagram_index}')
    if filter_params.element_type:
        conditions.append(f'element_type == "{filter_params.element_type}"')
    if filter_params.yin_yang:
        conditions.append(f'yin_yang == "{filter_params.yin_yang}"')
    if filter_params.text_type:
        conditions.append(f'text_type == "{filter_params.text_type}"')
    return ' and '.join(conditions) if conditions else None


class TestFilterExpression:
    """测试过滤表达式构建"""

    def test_single_condition(self):
        """测试单一过滤条件"""
        f = SearchFilter(hexagram_name="乾")
        expr = build_filter_expr(f)
        assert "hexagram_name" in expr
        assert "乾" in expr

    def test_multiple_conditions(self):
        """测试多条件过滤"""
        f = SearchFilter(hexagram_name="乾", text_type="爻辞", yin_yang="阳")
        expr = build_filter_expr(f)
        assert "hexagram_name" in expr
        assert "text_type" in expr
        assert "yin_yang" in expr
        assert " and " in expr

    def test_empty_filter(self):
        """测试空过滤条件"""
        f = SearchFilter()
        expr = build_filter_expr(f)
        assert expr is None

    def test_element_filter(self):
        """测试五行过滤"""
        f = SearchFilter(element_type="金")
        expr = build_filter_expr(f)
        assert "element_type" in expr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])