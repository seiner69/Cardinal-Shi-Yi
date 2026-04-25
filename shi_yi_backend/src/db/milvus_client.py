"""
Milvus Lite 客户端封装 - 《周易》知识库
强制使用本地 SQLite 模式 (./milvus_shiyi.db)
"""

import os
from typing import Optional
from dotenv import load_dotenv

from pymilvus import (
    MilvusClient,
    DataType,
    utility,
)

from src.models.schema import SearchFilter

load_dotenv()

# 强制使用本地数据库文件
DB_PATH = "./milvus_shiyi.db"


class MilvusIChingClient:
    """
    《周易》知识库 Milvus Lite 客户端
    强制使用本地 SQLite 模式，无需 Docker
    """

    COLLECTION_NAME = "iching_knowledge"
    VECTOR_DIM = 768  # 与 embedding 模型维度一致

    def __init__(self, db_path: str = DB_PATH, vector_dim: int = 768):
        """初始化客户端

        Args:
            db_path: 强制使用本地数据库文件路径
            vector_dim: 向量维度，默认 768
        """
        self.db_path = db_path
        self.VECTOR_DIM = vector_dim
        self._client: Optional[MilvusClient] = None

    def _get_client(self) -> MilvusClient:
        """获取 MilvusClient (本地 SQLite 模式)"""
        if self._client is None:
            # pymilvus 2.4+ 会自动检测 .db 文件并激活本地 SQLite 模式
            self._client = MilvusClient(uri=self.db_path)
            print(f"[INFO] 已连接 Milvus Lite: {self.db_path}")
        return self._client

    def connect(self) -> MilvusClient:
        """连接 Milvus Lite"""
        return self._get_client()

    def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            self._client = None

    def _build_schema(self) -> dict:
        """构建 Collection Schema"""
        fields = [
            {"name": "chunk_id", "dtype": DataType.VARCHAR, "max_length": 64, "is_primary": True},
            {"name": "content", "dtype": DataType.VARCHAR, "max_length": 4096},
            {"name": "context", "dtype": DataType.VARCHAR, "max_length": 4096},
            {"name": "hexagram_name", "dtype": DataType.VARCHAR, "max_length": 32},
            {"name": "hexagram_index", "dtype": DataType.INT64},
            {"name": "element_type", "dtype": DataType.VARCHAR, "max_length": 16},
            {"name": "line_position", "dtype": DataType.VARCHAR, "max_length": 16},
            {"name": "yin_yang", "dtype": DataType.VARCHAR, "max_length": 8},
            {"name": "text_type", "dtype": DataType.VARCHAR, "max_length": 16},
            {"name": "embedding", "dtype": DataType.FLOAT_VECTOR, "dim": self.VECTOR_DIM},
        ]
        return fields

    def create_collection(self, force_recreate: bool = False) -> None:
        """创建 Collection"""
        client = self._get_client()

        if utility.has_collection(client, self.COLLECTION_NAME):
            if force_recreate:
                utility.drop_collection(client, self.COLLECTION_NAME)
                print(f"[INFO] 已删除旧 Collection")
            else:
                print(f"[INFO] Collection 已存在")
                return

        schema = self._build_schema()
        client.create_collection(
            collection_name=self.COLLECTION_NAME,
            schema=schema,
        )
        print(f"[INFO] 已创建 Collection: {self.COLLECTION_NAME}")
        self._create_index()

    def _create_index(self) -> None:
        """创建向量索引"""
        client = self._get_client()
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTO_INDEX",
            metric_type="COSINE"
        )
        client.create_index(
            collection_name=self.COLLECTION_NAME,
            index_params=index_params
        )
        print("[INFO] 已创建向量索引")

    def get_collection(self):
        return self._get_client()

    def insert(
        self,
        chunk_ids: list[str],
        contents: list[str],
        contexts: list[str],
        hexagram_names: list[str],
        hexagram_indices: list[int],
        element_types: list[str],
        line_positions: list[str],
        yin_yangs: list[str],
        text_types: list[str],
        embeddings: list[list[float]],
    ) -> list[int]:
        """批量插入数据"""
        client = self._get_client()

        data = [
            {
                "chunk_id": chunk_ids[i],
                "content": contents[i],
                "context": contexts[i],
                "hexagram_name": hexagram_names[i],
                "hexagram_index": hexagram_indices[i],
                "element_type": element_types[i],
                "line_position": line_positions[i],
                "yin_yang": yin_yangs[i],
                "text_type": text_types[i],
                "embedding": embeddings[i],
            }
            for i in range(len(chunk_ids))
        ]

        result = client.insert(collection_name=self.COLLECTION_NAME, data=data)
        print(f"[INFO] 已插入 {len(chunk_ids)} 条数据")
        return result.get("ids", [])

    def flush(self) -> None:
        """刷新数据到磁盘"""
        client = self._get_client()
        client.flush(collection_name=self.COLLECTION_NAME)

    def _build_filter_expr(self, filter_params: SearchFilter) -> Optional[str]:
        """构建过滤表达式"""
        conditions = []
        if filter_params.hexagram_name:
            conditions.append(f'hexagram_name == "{filter_params.hexagram_name}"')
        if filter_params.hexagram_index is not None:
            conditions.append(f"hexagram_index == {filter_params.hexagram_index}")
        if filter_params.element_type:
            conditions.append(f'element_type == "{filter_params.element_type}"')
        if filter_params.yin_yang:
            conditions.append(f'yin_yang == "{filter_params.yin_yang}"')
        if filter_params.text_type:
            conditions.append(f'text_type == "{filter_params.text_type}"')
        return " and ".join(conditions) if conditions else None

    def search_iching_with_filter(
        self,
        query_embedding: list[float],
        filter_params: Optional[SearchFilter] = None,
        limit: int = 10,
        output_fields: Optional[list[str]] = None,
    ) -> list[dict]:
        """混合检索"""
        client = self._get_client()

        if output_fields is None:
            output_fields = ["chunk_id", "content", "context", "hexagram_name", "hexagram_index", "text_type", "line_position"]

        search_params = {"metric": "COSINE", "limit": limit}
        filter_expr = self._build_filter_expr(filter_params) if filter_params else None

        results = client.search(
            collection_name=self.COLLECTION_NAME,
            data=[query_embedding],
            anns_field="embedding",
            search_params=search_params,
            filter=filter_expr,
            output_fields=output_fields,
            limit=limit,
        )

        hits = []
        for hits_per_query in results:
            for hit in hits_per_query:
                record = {"distance": hit.get("distance", 0)}
                for field in output_fields:
                    record[field] = hit.get("entity", {}).get(field)
                hits.append(record)
        return hits

    def delete_by_ids(self, chunk_ids: list[str]) -> None:
        """根据 ID 删除"""
        client = self._get_client()
        client.delete(collection_name=self.COLLECTION_NAME, filter=f'chunk_id in {chunk_ids}')

    def get_collection_stats(self) -> dict:
        """获取统计信息"""
        client = self._get_client()
        stats = client.get_collection_stats(collection_name=self.COLLECTION_NAME)
        return {"name": self.COLLECTION_NAME, "num_entities": stats.get("row_count", 0)}

    def has_collection(self) -> bool:
        """检查 Collection 是否存在"""
        client = self._get_client()
        return utility.has_collection(client, self.COLLECTION_NAME)


def get_client() -> MilvusIChingClient:
    """获取默认客户端"""
    return MilvusIChingClient()
