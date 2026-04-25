"""
FAISS 向量数据库客户端 - 《周易》知识库
Windows 兼容的本地向量数据库
"""

import os
# 使用国内镜像加速模型下载
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import pickle
from typing import Optional, List
from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
import faiss
import numpy as np

load_dotenv()

# 数据库存储路径 (相对于项目根目录)
_DB_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_DB_BASE, "faiss_db")


class FAISSIChingClient:
    """
    《周易》知识库 FAISS 客户端

    使用 FAISS 作为向量数据库，Windows 兼容
    """

    COLLECTION_NAME = "iching_knowledge"
    VECTOR_DIM = 768  # text2vec-base-chinese 输出维度

    def __init__(self, db_path: str = None, embedding_model: str = "shibing624/text2vec-base-chinese"):
        """初始化客户端

        Args:
            db_path: 数据库存储路径
            embedding_model: Embedding 模型名称
        """
        self.db_path = db_path or DB_PATH
        self.embedding_model = embedding_model
        self._index: Optional[faiss.IndexFlatIP] = None
        self._documents: List[str] = []
        self._metadatas: List[dict] = []
        self._ids: List[str] = []
        self._embedding_function: Optional[HuggingFaceEmbeddings] = None

        # 确保目录存在
        os.makedirs(self.db_path, exist_ok=True)
        print(f"[INFO] FAISS 数据库路径: {self.db_path}")

    def _get_embedding_function(self) -> HuggingFaceEmbeddings:
        """获取 Embedding 函数"""
        if self._embedding_function is None:
            self._embedding_function = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'}
            )
        return self._embedding_function

    def connect(self):
        """加载已存在的索引"""
        index_path = os.path.join(self.db_path, "index.faiss")
        data_path = os.path.join(self.db_path, "data.pkl")

        # 加载索引
        if os.path.exists(index_path):
            self._index = faiss.read_index(index_path)
            print(f"[INFO] 已加载 FAISS 索引: {self._index.ntotal} 条记录")

        # 加载数据
        if os.path.exists(data_path):
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self._documents = data.get('documents', [])
                self._metadatas = data.get('metadatas', [])
                self._ids = data.get('ids', [])

    def _get_index(self) -> faiss.IndexFlatIP:
        """获取或创建索引"""
        if self._index is None:
            # 使用 Inner Product (余弦相似度需要归一化)
            self._index = faiss.IndexFlatIP(self.VECTOR_DIM)
            print(f"[INFO] 已创建 FAISS 索引 (维度: {self.VECTOR_DIM})")
        return self._index

    def create_collection(self, force_recreate: bool = False) -> None:
        """创建或清空 Collection"""
        if force_recreate:
            # 删除旧数据
            index_path = os.path.join(self.db_path, "index.faiss")
            data_path = os.path.join(self.db_path, "data.pkl")

            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(data_path):
                os.remove(data_path)

            self._index = None
            self._documents = []
            self._metadatas = []
            self._ids = []

            print(f"[INFO] 已清空 FAISS 数据库: {self.db_path}")
        else:
            self.connect()

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
        index = self._get_index()
        embeddings = self._get_embedding_function()

        # 生成向量
        vectors = embeddings.embed_documents(texts)

        # 归一化向量（用于余弦相似度）
        vectors = np.array(vectors).astype('float32')
        faiss.normalize_L2(vectors)

        # 添加到索引
        index.add(vectors)

        # 保存数据
        self._documents.extend(texts)
        self._metadatas.extend(metadatas or [{}] * len(texts))
        self._ids.extend(ids or [str(i) for i in range(len(texts))])

        # 持久化
        self._save()

        print(f"[INFO] 已添加 {len(texts)} 条数据")
        return ids or []

    def _save(self) -> None:
        """保存索引和数据"""
        index_path = os.path.join(self.db_path, "index.faiss")
        data_path = os.path.join(self.db_path, "data.pkl")

        # 保存索引
        if self._index:
            faiss.write_index(self._index, index_path)

        # 保存数据
        with open(data_path, 'wb') as f:
            pickle.dump({
                'documents': self._documents,
                'metadatas': self._metadatas,
                'ids': self._ids
            }, f)

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
            filter: 过滤条件（暂不支持）

        Returns:
            检索结果列表
        """
        embeddings = self._get_embedding_function()

        # 生成查询向量
        query_vector = np.array([embeddings.embed_query(query)]).astype('float32')
        faiss.normalize_L2(query_vector)

        # 搜索
        index = self._get_index()
        distances, indices = index.search(query_vector, k)

        # 格式化结果
        hits = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0:
                hits.append({
                    "content": self._documents[idx],
                    "metadata": self._metadatas[idx],
                    "distance": float(distances[0][i])
                })

        return hits

    def search_with_score(
        self,
        query: str,
        k: int = 10,
        filter: Optional[dict] = None,
    ) -> List[dict]:
        """带分数的相似性搜索"""
        return self.search(query=query, k=k, filter=filter)

    def get_count(self) -> int:
        """获取文档数量"""
        if self._index:
            return self._index.ntotal
        return 0

    def delete_collection(self) -> None:
        """删除 Collection"""
        index_path = os.path.join(self.db_path, "index.faiss")
        data_path = os.path.join(self.db_path, "data.pkl")

        if os.path.exists(index_path):
            os.remove(index_path)
        if os.path.exists(data_path):
            os.remove(data_path)

        self._index = None
        self._documents = []
        self._metadatas = []
        self._ids = []

        print(f"[INFO] 已删除 FAISS 数据库")


def get_client() -> FAISSIChingClient:
    """获取默认客户端"""
    return FAISSIChingClient()
