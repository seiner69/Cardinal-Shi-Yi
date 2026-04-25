"""
ChromaDB 客户端封装 - 《周易》知识库
Windows 兼容的本地向量数据库
"""

import os
# 使用国内镜像加速模型下载
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from typing import Optional, List
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

load_dotenv()

# 数据库存储路径
DB_PATH = "E:/pypy/史易枢机/shi_yi_backend/chroma_db"


class ChromaIChingClient:
    """
    《周易》知识库 ChromaDB 客户端

    使用 Chroma 作为向量数据库，Windows 兼容
    """

    COLLECTION_NAME = "iching_knowledge"

    def __init__(self, db_path: str = DB_PATH, embedding_model: str = "shibing624/text2vec-base-chinese"):
        """初始化客户端

        Args:
            db_path: 数据库存储路径
            embedding_model: Embedding 模型名称
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        self._client: Optional[Chroma] = None

    def _get_embedding_function(self) -> HuggingFaceEmbeddings:
        """获取 Embedding 函数"""
        return HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cpu'}
        )

    def _get_client(self) -> Chroma:
        """获取 Chroma 客户端"""
        if self._client is None:
            # 使用 Chroma 的持久化客户端
            # 禁用 HNSW 索引，使用 FLAT 索引（更稳定但稍慢）
            self._client = Chroma(
                persist_directory=self.db_path,
                embedding_function=self._get_embedding_function(),
                collection_name=self.COLLECTION_NAME,
                collection_metadata={
                    "hnsw:construction_ef": 128,
                    "hnsw:search_ef": 128,
                    "hnsw:M": 16,
                    # 设置为 null 禁用 HNSW，使用 FLAT
                    "index_type": "flat"
                }
            )
            print(f"[INFO] 已连接 ChromaDB: {self.db_path}")
        return self._client

    def connect(self) -> Chroma:
        return self._get_client()

    def disconnect(self) -> None:
        if self._client:
            self._client = None

    def create_collection(self, force_recreate: bool = False) -> None:
        """创建 Collection（使用 FLAT 索引）"""
        import chromadb

        # 使用原生客户端
        native_client = chromadb.PersistentClient(path=self.db_path)

        if force_recreate:
            try:
                native_client.delete_collection(self.COLLECTION_NAME)
                print(f"[INFO] 已删除旧 Collection")
            except:
                pass

        # 创建新 Collection，使用 FLAT 索引
        native_client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "l2"}
        )

        # 重置客户端
        self._client = None
        self._get_client()

        print(f"[INFO] ChromaDB Collection 已创建: {self.COLLECTION_NAME}")

    def get_collection(self):
        """获取 Collection"""
        return self._get_client()

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """添加文档

        Args:
            texts: 文本列表
            metadatas: 元数据列表
            ids: ID 列表

        Returns:
            生成的 ID 列表
        """
        client = self._get_client()
        result = client.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        print(f"[INFO] 已添加 {len(texts)} 条数据")
        return result

    def delete_collection(self) -> None:
        """删除 Collection"""
        try:
            client = self._get_client()
            client.delete_collection()
            print(f"[INFO] 已删除 ChromaDB Collection")
        except Exception as e:
            print(f"[INFO] 删除失败: {e}")
        self._client = None

    def search_iching_with_filter(
        self,
        query_embedding: list[float],
        filter_params: Optional[dict] = None,
        limit: int = 5,
    ) -> list[dict]:
        """混合检索 (兼容 Milvus 接口)

        注意: ChromaDB 使用文本查询而非向量，
        此处简化处理，直接使用文本查询

        Args:
            query_embedding: 查询向量 (此处未使用)
            filter_params: 过滤条件字典
            limit: 返回数量

        Returns:
            检索结果列表
        """
        # 提取文本查询（从 embedding 无法还原文本，所以用占位符）
        # 实际使用时建议用 search() 方法
        query_text = "卦"  # 默认查询

        # 转换 filter_params
        chroma_filter = None
        if filter_params:
            if hasattr(filter_params, 'hexagram_name') and filter_params.hexagram_name:
                hexagram = filter_params.hexagram_name
                chroma_filter = {"hexagram_name": hexagram}
            elif hasattr(filter_params, 'text_type') and filter_params.text_type:
                text_type = filter_params.text_type
                chroma_filter = {"text_type": text_type}

        return self.search_with_score(query=query_text, k=limit, filter=chroma_filter)

    def search(
        self,
        query: str,
        k: int = 10,
        filter: Optional[dict] = None,
    ) -> List[dict]:
        """相似性搜索

        Args:
            query: 查询文本
            k: 返回数量
            filter: 过滤条件

        Returns:
            检索结果列表
        """
        client = self._get_client()

        results = client.similarity_search(
            query=query,
            k=k,
            filter=filter
        )

        # 格式化结果
        hits = []
        for doc in results:
            hits.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "distance": getattr(doc, 'distance', None)
            })
        return hits

    def search_with_score(
        self,
        query: str,
        k: int = 10,
        filter: Optional[dict] = None,
    ) -> List[dict]:
        """带分数的相似性搜索"""
        client = self._get_client()

        results = client.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )

        hits = []
        for doc, score in results:
            hits.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "distance": score
            })
        return hits

    def get_count(self) -> int:
        """获取文档数量"""
        try:
            client = self._get_client()
            return client._collection.count()
        except Exception as e:
            print(f"[WARNING] 获取数量失败: {e}")
            return 0


def get_client() -> ChromaIChingClient:
    """获取默认客户端"""
    return ChromaIChingClient()
