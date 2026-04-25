"""
全量语料清洗与灌入脚本
处理《资治通鉴》和《周易》，存入 ChromaDB
"""

import os
# 使用国内镜像加速模型下载
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import re
import uuid
from typing import Optional, List
from tqdm import tqdm

# 环境变量
from dotenv import load_dotenv
load_dotenv()

# LangChain 文本分割
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 本地 Embedding 模型
from langchain_huggingface import HuggingFaceEmbeddings

# ChromaDB 客户端
from src.db.faiss_client import FAISSIChingClient

# 项目根目录
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 文件路径
ZIZHI_PATH = os.path.join(_BASE_DIR, "资治通鉴 .txt")
ICHING_PATH = os.path.join(_BASE_DIR, "周易.md")
DB_PATH = os.path.join(_BASE_DIR, "faiss_db")

# Embedding 模型配置
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"


# ========== 1. 处理《资治通鉴》 ==========

def load_zizhi_text(path: str) -> str:
    """加载《资治通鉴》文本（全部）"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_zizhi_text(text: str) -> list[dict]:
    """使用 RecursiveCharacterTextSplitter 切分《资治通鉴》"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", "。", "！", "？", "；"]
    )

    chunks = splitter.split_text(text)

    result = []
    for i, chunk in enumerate(chunks):
        source = "zizhitongjian"
        volume = None

        # 尝试提取卷次信息
        match = re.search(r'卷[一二三四五六七八九十百千万]+', chunk[:100])
        if match:
            volume = match.group()

        result.append({
            "content": chunk,
            "source": source,
            "volume": volume,
            "chunk_index": i
        })

    return result


# ========== 2. 处理《周易》 ==========

def load_iching_md(path: str) -> str:
    """加载《周易》Markdown"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_iching_md(text: str) -> list[dict]:
    """解析《周易》Markdown"""
    # 过滤图片标签
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    chunks = []
    current_hexagram = None
    current_index = 0
    current_symbol = None

    HEXAGRAM_SYMBOLS = {
        "乾": "☰", "兑": "☱", "离": "☲", "震": "☳",
        "巽": "☴", "坎": "☵", "艮": "☶", "坤": "☷"
    }

    ELEMENT_MAPPING = {
        "乾": "金", "兑": "金", "离": "火", "震": "木",
        "巽": "木", "坎": "水", "艮": "土", "坤": "土"
    }

    LINE_PATTERN = re.compile(r'^(初九|九二|九三|九四|九五|上九|初六|六二|六三|六四|六五|上六)[:：]')

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测卦名标题
        hexagram_match = re.match(r'^#*\s*[０１2３４５６７８９零一二三四五六七八九十百]+[．.]([坤乾兑离震巽坎艮])', line)
        if hexagram_match:
            current_hexagram = hexagram_match.group(1)
            idx_match = re.search(r'卦([一二三四五六七八九十百]+)', line)
            current_index = 1
            current_symbol = HEXAGRAM_SYMBOLS.get(current_hexagram, "")
            continue

        # 检测卦辞
        gua_ci_match = re.match(r'^《(.+)》[:：](.+)', line)
        if gua_ci_match and current_hexagram:
            gua_ci = gua_ci_match.group(2)
            chunks.append({
                "content": gua_ci,
                "hexagram_name": current_hexagram,
                "hexagram_index": current_index,
                "text_type": "卦辞",
                "line_position": None,
                "yin_yang": "阳",
                "element_type": ELEMENT_MAPPING.get(current_hexagram, "土"),
                "symbol": current_symbol,
                "context": f"{current_hexagram}卦卦辞：{gua_ci}"
            })
            continue

        # 检测爻位
        yao_match = LINE_PATTERN.match(line)
        if yao_match and current_hexagram:
            line_position = yao_match.group(1)
            yao_content = line.split('：', 1)[-1].split(':', 1)[-1].strip()
            yin_yang = "阳" if "九" in line_position else "阴"

            chunks.append({
                "content": yao_content,
                "hexagram_name": current_hexagram,
                "hexagram_index": current_index,
                "text_type": "爻辞",
                "line_position": line_position,
                "yin_yang": yin_yang,
                "element_type": ELEMENT_MAPPING.get(current_hexagram, "土"),
                "symbol": current_symbol,
                "context": f"{current_hexagram}-{line_position}：{yao_content}"
            })
            continue

        # 检测彖传
        tuan_match = re.match(r'^《彖》[:：](.+)', line)
        if tuan_match and current_hexagram:
            chunks.append({
                "content": tuan_match.group(1),
                "hexagram_name": current_hexagram,
                "hexagram_index": current_index,
                "text_type": "彖传",
                "line_position": None,
                "yin_yang": "阳",
                "element_type": ELEMENT_MAPPING.get(current_hexagram, "土"),
                "symbol": current_symbol,
                "context": f"{current_hexagram}卦彖传：{tuan_match.group(1)}"
            })
            continue

        # 检测象传
        xiang_match = re.match(r'^《象》[:：](.+)', line)
        if xiang_match and current_hexagram:
            chunks.append({
                "content": xiang_match.group(1),
                "hexagram_name": current_hexagram,
                "hexagram_index": current_index,
                "text_type": "象传",
                "line_position": None,
                "yin_yang": "阳",
                "element_type": ELEMENT_MAPPING.get(current_hexagram, "土"),
                "symbol": current_symbol,
                "context": f"{current_hexagram}卦象传：{xiang_match.group(1)}"
            })
            continue

    return chunks


# ========== 3. 灌入脚本 ==========

def get_embeddings() -> HuggingFaceEmbeddings:
    """获取本地 Embedding 模型"""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )


def ingest_data():
    """执行全量灌入"""
    print("=" * 50)
    print("开始全量语料灌入 (ChromaDB)")
    print("=" * 50)

    # 1. 初始化 ChromaDB 客户端
    client = FAISSIChingClient(db_path=DB_PATH, embedding_model=EMBEDDING_MODEL)

    # 2. 清空旧数据并创建 Collection
    print("\n[1] 清空旧数据并创建 Collection...")
    client.create_collection(force_recreate=True)

    # 4. 获取 Embeddings
    print("\n[3] 初始化 Embedding 模型...")
    print(f"    模型: {EMBEDDING_MODEL}")
    embeddings = get_embeddings()

    # ========== 处理《资治通鉴》 ==========
    print("\n[4] 处理《资治通鉴》(全量)...")
    zizhi_text = load_zizhi_text(ZIZHI_PATH)
    zizhi_chunks = split_zizhi_text(zizhi_text)
    print(f"    切分得到 {len(zizhi_chunks)} 个片段")

    # 分批添加到 ChromaDB
    batch_size = 100
    zizhi_count = 0
    for i in range(0, len(zizhi_chunks), batch_size):
        batch = zizhi_chunks[i:i+batch_size]
        texts = [c["content"] for c in batch]
        metadatas = [{
            "source": c["source"],
            "volume": c.get("volume", ""),
            "hexagram_name": c["source"],
            "hexagram_index": 0,
            "element_type": c["source"],
            "line_position": c.get("volume", ""),
            "yin_yang": c["source"],
            "text_type": "正文"
        } for c in batch]
        ids = [str(uuid.uuid4()) for _ in batch]

        client.add_documents(texts=texts, metadatas=metadatas, ids=ids)
        zizhi_count += len(batch)
        print(f"    [进度] 已完成 {zizhi_count}/{len(zizhi_chunks)}...")

    print(f"    已插入 {len(zizhi_chunks)} 个《资治通鉴》片段")

    # ========== 处理《周易》 ==========
    print("\n[5] 处理《周易》(完整)...")
    iching_md = load_iching_md(ICHING_PATH)
    iching_chunks = parse_iching_md(iching_md)
    print(f"    解析得到 {len(iching_chunks)} 个爻位/卦辞")

    # 分批添加到 ChromaDB
    iching_count = 0
    for i in range(0, len(iching_chunks), batch_size):
        batch = iching_chunks[i:i+batch_size]
        texts = [c["content"] for c in batch]
        metadatas = [{
            "hexagram_name": c["hexagram_name"],
            "hexagram_index": c["hexagram_index"],
            "element_type": c["element_type"],
            "line_position": c["line_position"] or "",
            "yin_yang": c["yin_yang"],
            "text_type": c["text_type"],
            "symbol": c.get("symbol", ""),
            "context": c.get("context", "")
        } for c in batch]
        ids = [str(uuid.uuid4()) for _ in batch]

        client.add_documents(texts=texts, metadatas=metadatas, ids=ids)
        iching_count += len(batch)
        print(f"    [进度] 已完成 {iching_count}/{len(iching_chunks)}...")

    print(f"    已插入 {len(iching_chunks)} 个《周易》爻位/卦辞")

    # 5. 统计
    total_count = client.get_count()

    print("\n" + "=" * 50)
    print("灌入完成!")
    print("=" * 50)
    print(f"《资治通鉴》片段: {zizhi_count}")
    print(f"《周易》爻位/卦辞: {iching_count}")
    print(f"总计: {total_count}")
    print(f"数据库: {DB_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    # 默认处理前 100 行
    ingest_data()
