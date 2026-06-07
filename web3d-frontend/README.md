# 史易枢机前端

这是 `6-Bit FSM Topology Engine` 的 Web3D 前端。它使用 React、TypeScript、Vite、Zustand 和 Three.js，将后端的语义分析与物理状态机结果展示为两层界面。

## 两层模式

### 实用模式

默认入口，面向真实使用场景。用户输入一个历史事件、现实困局、项目状态或市场场景后，前端会展示：

- 当前局势
- 关键矛盾
- 下一步风险
- 建议动作
- 可信度
- 主要后继方向

这一层会隐藏 `E/P/R/tau/C/Rb` 等底层参数，把复杂模型翻译成可直接阅读的判断。

### 专家模式

保留完整工程调试能力，包含三个视图：

- **分析**：语义入卦、六层赋值依据、翻转预览
- **模拟**：B1-B6、E/P/R/tau/C/Rb、误差、死锁、外部注能
- **演化**：后继路径、张量、置信度、Monte Carlo 分布

## 本地启动

后端默认运行在 `127.0.0.1:8000`，前端默认运行在 `127.0.0.1:5173`。

```bash
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

生产构建：

```bash
npm run build
```

代码检查：

```bash
npm run lint
```

## API 代理

Vite 会把 `/api/*` 请求代理到后端：

```text
http://127.0.0.1:5173/api/* -> http://127.0.0.1:8000/api/*
```

核心链路：

```text
用户材料 -> /api/infer -> physics_seed -> /api/physics -> 实用层 / 专家层
```

## 主要目录

```text
src/
  components/
    PracticalView.tsx      # 默认实用模式
    AnalysisView.tsx       # 专家：语义分析
    SimulationView.tsx     # 专家：物理模拟
    EvolutionView.tsx      # 专家：演化分布
    PhysicsResultPanel.tsx # 专家结果面板
  store/
    useStore.ts            # Zustand 状态和 API 调用
  utils/
    physicsLabels.ts       # 物理事件/相位/TTL 中文标签
```
