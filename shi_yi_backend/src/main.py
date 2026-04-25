"""
史易枢机 - 入口脚本 / 测试演示
"""

import json
from src.llm.chain import IChingChain
from src.llm.prompts import get_system_prompt
from src.db.faiss_client import FAISSIChingClient
from src.pipeline.chunker import IChingStructuredChunker


def main():
    """演示入口"""
    print("=" * 50)
    print("史易枢机 - 历史与周易双知识库 RAG 后端")
    print("=" * 50)

    # 1. 展示 System Prompt
    print("\n[1] System Prompt 示例:")
    print("-" * 30)
    prompt = get_system_prompt(
        history_context="春秋战国时期，孔子周游列国",
        iching_context="乾卦九五：飞龙在天，利见大人"
    )
    print(prompt[:500] + "...")

    # 2. 展示 LLM Chain
    print("\n[2] LLM Chain (模拟模式):")
    print("-" * 30)
    chain = IChingChain()

    # 模拟运行（ChromaDB 使用文本查询，无需 embedding）
    history_input = "秦始皇统一六国，建立秦朝"

    result = chain.run(history_input)

    print(f"输入: {history_input}")
    print(f"\n输出:")
    print(f"  - 局势转译: {result.situation_translation}")
    print(f"  - 权力图景: {result.power_landscape}")
    print(f"  - 易理投射: {result.iching_projection}")
    print(f"  - 天道人事: {result.heaven_human}")
    print(f"  - 引用卦象: {result.referenced_hexagrams}")

    # 3. 展示分块器
    print("\n[3] 数据处理管道:")
    print("-" * 30)

    # Mock 数据
    mock_hexagram = {
        "卦名": "乾",
        "卦序": 1,
        "章节": "上经",
        "卦辞": "元亨利贞",
        "彖传": "大哉乾元，万物资始...",
        "爻": [
            {"位置": "初九", "爻辞": "潜龙勿用"},
            {"位置": "九五", "爻辞": "飞龙在天，利见大人"},
        ]
    }

    chunker = IChingStructuredChunker()
    chunks = chunker.parse_hexagram(mock_hexagram)

    print(f"输入: 乾卦")
    print(f"输出: {len(chunks)} 个语义块")
    for c in chunks[:3]:
        print(f"  - [{c.metadata.text_type}] {c.context[:30]}...")

    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()