# 史易枢机 — 项目日志

## V11.1 — 2026-04-25

### 前端：SSOT物理仿真控制台重构

**问题诊断：**
- React检测到LeftPanel中Hook调用顺序变化（useEffect在条件return之后）
- TypeScript build失败：多组件存在未使用变量（TS6133）
- Vite代理端口错误：指向8000而非实际后端8001
- 前端设计与后端API不匹配：字段名不一致、缺少per-layer参数API

**修复内容：**
- 重构OverlayUI为三栏布局：LeftConsole + CenterOutput + RightConsole
- 新增6个组件：BitProgressBar、DeltaMDisplay、ConfidenceGauge、MonteCarloChart、TypewriterLog、LayerInputCard
- 重构3个组件：LeftConsole（替代LeftPanel）、CenterOutput、RightConsole（替代RightPanel）
- 修复React Hooks违规：调整useEffect调用顺序
- 修复TS6133错误：移除所有未使用变量和导入
- 更新vite.config.ts代理端口：8001
- 扩展useStore.ts：新增NodeInfo、typewriterLogs、isSimulating状态

**设计原则：**
- SSOT（单一事实来源）：所有物理参数以后端API为准
- 后端不动前端适配：不修改后端，前端适应现有API

---

## V11.0 — 2026-04-??

### 后端：离散自动机可证伪版

**重大升级：**
- E_i(t) = E_i(t-1) - R_i · α(B_down)，α严格={1.0, 2.0}
- P_i(t) = P_i(t-1) + C_i · B_up
- p维度（奇偶共振轴）{-1, 1}，e维度（能量耗散轴）[-1, 1]，t维度（时间消耗轴）[0, 1]
- Conf_M1 = 1 - max(U_E, U_P, U_R, U_τ)
- Monte Carlo扰动引擎 N=1000
- SSOT管线：raw physics inputs → fsm_kernel.py计算所有量

---

## V2.0 — 古典水墨重构

**视觉升级：**
- 彻底抛弃赛博朋克深色模式
- 切换为白纸黑字浓墨红印的古典画卷风格
- 3D模型改用贝塞尔曲线ExtrudeGeometry
- 模拟毛笔实笔/断笔形态

---

## V1.0 — 初始赛博朋克版

**初始版本：**
- 3D圆柱体爻 + EffectComposer Bloom
- 深色霓虹配色
