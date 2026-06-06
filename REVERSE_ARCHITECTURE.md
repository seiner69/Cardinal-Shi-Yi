# 系统逆向解剖原本 (Reverse Architecture Report)

> **解剖者（AI）声明**：本报告提取自代码库当前的真实物理状态，不包含任何未来的假设与规划。代码即事实。

## 一、 物理拓扑与基础算力耗散 (Physical Topology)

- **运行容器/进程节点**：
  - Backend: Python FastAPI (shi_yi_backend/src/main.py), port 8000
  - Frontend: Node.js React + Vite (web3d-frontend), dev server with proxy to 127.0.0.1:8000
  - UI: Streamlit (shi_yi_backend/src/app.py) — 另一套 UI 入口
  - VectorDB: ChromaDB (chroma_db/) 或 FAISS (faiss_db/) — 本地持久化向量存储
  - **无 Docker Compose — 未容器化**

- **核心第三方依赖网络**：
  - **MiniMax API** — 通过 Anthropic SDK 兼容接口调用 (MiniMax-M2.7)
  - **HuggingFace Embeddings** — 模型 `shibing624/text2vec-base-chinese` (768维)
  - **ChromaDB** — 向量数据库
  - **FAISS** — 备选向量索引

- **环境变量控制面 (Env Vars)**：
  - `MINIMAX_API_KEY` — **强制要求**（无值时降级为 Mock 模式）
  - `HF_ENDPOINT` — **硬编码为 `https://hf-mirror.com`**（不可配置）
  - `.env.example` 中有 OpenAI/DeepSeek 配置占位符，但**代码中未使用**

---

## 二、 领域本体与真理源 (Ontology & Single Source of Truth)

### 2.1 核心数据表 (Core Tables)

- **无 SQL 数据库** — 系统无任何关系型数据库依赖
- **无 Migrations/Schema 文件** — 所有状态均为内存计算
- **FSMState 数据结构**（fsm_kernel.py:159-185）:
  - `B[6]` — 6位布尔数组，取值0或1
  - `E[6]` — 各节点当前能量储备
  - `P[6]` — 各节点当前承受的外部压强
  - `E_initial[6]` — 各节点初始能量基准
  - `R[6]` — 各节点基础耗散率
  - `R_base[6]` — 各节点基准耗散率
  - `tau[6]` — 各节点材料屈服阈值
  - `C[6]` — 各节点压强累积率

### 2.2 状态驻留点 (State Persistence)

- **数据库 (DB)**：
  - ChromaDB Collection `iching_knowledge` — 存储《周易》语义块
  - FAISS Index — 备选向量索引，存储路径 `faiss_db/index.faiss` + `faiss_db/data.pkl`
  - **无状态表** — 系统状态（FSMState）纯内存，不持久化

- **缓存 (Cache/Redis)**：无

- **向量库 (VectorDB)**：
  - ChromaDB metadata 结构：`{"hexagram_name": str, "text_type": str}`
  - FAISS metadata：pickle 序列化存储 `{"documents": [], "metadatas": [], "ids": []}`

---

## 三、 边界与海关 (API Boundaries)

### 3.1 鉴权防腐层 (Auth Layer)

- **代码物理实现**：`无鉴权`
  - FastAPI 无任何中间件拦截
  - 所有 API endpoint 公开访问
  - Streamlit UI 无登录机制

### 3.2 核心暴露接口 (Core APIs)

- **`POST /api/infer`**
  - 触发条件：前端 AnalysisView 调用
  - 实际入参：`{"query": string}`
  - 副作用：
    1. 调用 MiniMax API（若配置）
    2. 查询 ChromaDB/FAISS 知识库
    3. 返回 LLM FSM 分析结果 + 确定性硬算叠加

- **`GET /api/simulate`**
  - 触发条件：前端 SimulationView 调用
  - 实际入参：`bits=6位字符串`, `E0=float`, `P0=float`
  - 副作用：无持久化，纯计算返回6种Bit Flip预览

- **`GET /api/evolve`**
  - 触发条件：前端 EvolutionView 调用
  - 实际入参：`bits`, `path`(可选1-4), `delta_E_ext`, `deadlock_flag`, `time_in_state`
  - 副作用：无持久化，执行确定性演化路径判定

- **`GET /api/node`**
  - 触发条件：前端获取节点完整物理状态
  - 实际入参：`bits=6位字符串`
  - 副作用：无

---

## 四、 核心因果链与暗流 (Causality & Dark Flows)

### 4.1 异步任务与定时器 (Cron & Background Jobs)

- **任务数量：0**
  - 代码中无 `schedule`、`cron`、`Celery`、`APScheduler` 等定时任务库
  - 无后台任务队列

### 4.2 第三方 API 调用链 (External API Integration)

- **目标：MiniMax API (MiniMax-M2.7)**
  - 调用入口：`src/llm/chain.py:295-301`
  - 调用方式：`anthropic.Anthropic.messages.create()`
  - 触发节点：`POST /api/infer` → `IChingChain.run()` → Step C: `generate_fsm_analysis()`
  - **真实容错逻辑**：
    - 若 `MINIMAX_API_KEY` 未配置或为 placeholder → 降级为 `_mock_fsm_response()` 返回硬编码 JSON
    - JSON 解析失败 → 打印 Warning，返回默认值 `inner_bits="000", outer_bits="000"`
    - **无重试机制，无指数退避，无状态标记**

- **目标：HuggingFace Embedding API**
  - 调用入口：`ChromaIChingClient._get_embedding_function()` 或 `FAISSIChingClient._get_embedding_function()`
  - 模型：`shibing624/text2vec-base-chinese`
  - **容错逻辑**：无（直接 raise exception）

---

## 五、 技术债与硬编码规则 (Technical Debt & Hardcoded Reality)

- **硬编码的魔法数字 (Magic Numbers)**：
  - `DEFAULT_R = 0.1` — 基础耗散率 (fsm_kernel.py:143)
  - `DEFAULT_C = 0.15` — 压强累积率 (fsm_kernel.py:144)
  - `DEFAULT_TAU = 1.0` — 材料屈服阈值 (fsm_kernel.py:145)
  - `DEFAULT_E0 = 1.0` — 初始能量储备 (fsm_kernel.py:146)
  - `DEFAULT_P0 = 0.0` — 初始压强 (fsm_kernel.py:147)
  - `K = 3` — 内外系统分界 (fsm_kernel.py:148)
  - `M_THRESHOLD = 4` — 路径三巨型系统判定 (fsm_kernel.py:149)
  - `T_MASK = 5` — 路径二潜伏超时阈值 (fsm_kernel.py:150)
  - `MONTE_CARLO_N = 1000` — Monte Carlo 采样次数 (fsm_kernel.py:151)
  - `U_INPUT = 0.1` — 默认输入不确定性 (fsm_kernel.py:152)
  - `VECTOR_DIM = 768` — text2vec-base-chinese 输出维度 (faiss_client.py:33)

- **潜在的系统单点/瓶颈**：
  - 无 API Key 时系统降级为 Mock — 业务逻辑静默失败，用户无法感知
  - HuggingFace Embedding 模型下载走 hf-mirror.com — 国内镜像可用但不可配置
  - ChromaDB/FAISS 二选一 — 代码中 `IChingChain` 固定使用 `FAISSIChingClient`，ChromaDB 实际未被调用
  - `HF_ENDPOINT` 在 `api.py` 和 `faiss_client.py` 两处硬编码 — 环境变量覆盖机制缺失

- **路径判定阈值**：
  - 路径四触发：`deadlock_flag=True` 或 `delta_E_ext < -1000.0 * M` (fsm_kernel.py:873)
  - 路径三触发：`M > 4` 且 `delta_E_ext <= 0` (fsm_kernel.py:883)
  - 路径二触发：`(B[0]^B[1] == 1 or B[5]^B[4] == 1)` 且 `time_in_state > 5` (fsm_kernel.py:895)

---

## 附录：代码与文件物理拓扑

| 文件路径 | 职责 |
|---|---|
| `shi_yi_backend/src/api.py` | FastAPI HTTP 入口，硬编码 HF_ENDPOINT |
| `shi_yi_backend/src/fsm_kernel.py` | V11.0 离散自动机内核，所有物理计算 |
| `shi_yi_backend/src/llm/chain.py` | LLM Chain编排，Mock降级，JSON解析容错 |
| `shi_yi_backend/src/llm/prompts.py` | System Prompt 模板 (~330行) |
| `shi_yi_backend/src/models/schema.py` | Pydantic 请求/响应模型，FSMOutput结构 |
| `shi_yi_backend/src/db/chroma_client.py` | ChromaDB客户端，metadata仅支持hexagram_name/text_type |
| `shi_yi_backend/src/db/faiss_client.py` | FAISS客户端，硬编码HF_ENDPOINT |
| `shi_yi_backend/src/app.py` | Streamlit UI入口 |
| `web3d-frontend/src/store/useStore.ts` | Zustand状态管理，前端API调用 |
| `web3d-frontend/vite.config.ts` | Vite代理配置，将/api/*转发到127.0.0.1:8000 |
