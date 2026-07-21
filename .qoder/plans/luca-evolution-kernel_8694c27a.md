# luca_of_math_lean 实现计划

## 项目结构
```
luca_of_math_lean/
├── pyproject.toml
├── requirements.txt
├── luca/
│   ├── __init__.py
│   ├── config.py       # 超参数配置
│   ├── urn.py          # Pólya 瓮引擎 (带创新的非马尔可夫随机过程)
│   ├── grammar.py      # Lean 4 语法采样器与代码组装器
│   ├── syllogism.py    # Lean 代码 → 哲学三段论命题翻译器
│   ├── physics.py      # Lean 4 编译器沙箱 (subprocess 执行)
│   ├── pruner.py       # 代谢成本、去重、衰减机制
│   └── engine.py       # 主演化循环
└── main.py             # CLI 入口
```

## 1. `pyproject.toml` + `requirements.txt`
- Python 3.10+，依赖仅 `click`（CLI 框架）和 `rich`（终端彩色输出），其余全部标准库。

## 2. `luca/config.py` — 超参数中心
- `MAX_URN_SIZE`：瓮的最大 token 数量
- `INNOVATION_RATE`：新 token 初始权重
- `DECAY_RATE`：指数衰减率
- `CATASTROPHE_PROBABILITY`：天灾触发概率
- `LEAN_TIMEOUT`：Lean 编译超时（秒）
- `EVOLUTION_OUTPUT_FILE`：`evolved_library.lean` 路径
- `MAX_EXPRESSION_TOKENS`：单条表达式最多使用 token 数
- `MAX_DEFINITION_LENGTH`：生成的 Lean 代码最大长度
- 扩展初始 token 列表至 106 个（含类型、值、自然数/整数运算、布尔、列表、Option、积类型、逻辑、构造、策略词，覆盖 Lean 4 Init 库核心元素）

## 3. `luca/urn.py` — Pólya 瓮核心
- `PolyaUrn` 类，维护 `dict[str, float]`（token → 权重）
- 初始化时用一个大的初始 token 列表（含类型、值、运算、逻辑、构造、结构类 token），每个初始权重为 1.0
- `sample(k)`: 按权重无放回采样 k 个 token（或放回采样，取决于策略）
- `reinforce(tokens, count)`: 将使用过的 token 权重增加
- `innovate(new_name)`: 将新编译成功的定义作为新 token 加入，初始权重为 `INNOVATION_RATE`
- `decay(rate)`: 所有 token 权重乘以衰减因子；当超过 `MAX_URN_SIZE` 时，移除权重最低的 token
- `top(n)`: 返回权重最高的 n 个 token（用于日志展示）

## 4. `luca/syllogism.py` — 哲学三段论命题翻译器
- `SyllogismRenderer` 类，将生成的 Lean 代码还原为"大前提→小前提→结论"的三段论形式
- 核心映射规则（基于 token 语义的启发式翻译）：
  - `Nat.add a b` → "大前提: 自然数对加法封闭 / 小前提: a 与 b 皆为自然数 / 结论: gene_N 断言 a+b 为一自然数"
  - `Nat.mul a b` → "大前提: 自然数对乘法封闭 / 小前提: a 与 b 皆为自然数 / 结论: gene_N 断言 a*b 为一自然数"
  - `a = b` (等式) → "大前提: 等同性自反 / 小前提: a 与 b 在计算上归约至同一范式 / 结论: gene_N 断言 a 等于 b"
  - `And p q` → "大前提: 合取命题的真值条件 / 小前提: p 与 q 各自成立 / 结论: gene_N 断言 p 且 q 同时成立"
  - `Or p q` → "大前提: 析取命题的真值条件 / 小前提: p 或 q 至少其一成立 / 结论: gene_N 断言 p 或 q 成立"
  - `Not p` → "大前提: 否定命题的真值条件 / 小前提: p 导致矛盾 / 结论: gene_N 断言非 p"
  - `fun x => body` → "大前提: 函数类型的构造规则 / 小前提: 对任意 x，body 为合法项 / 结论: gene_N 定义了一个从 x 到 body 的映射"
  - `if cond then a else b` → "大前提: 排中律 / 小前提: cond 可判定 / 结论: gene_N 依 cond 在 a 与 b 间择一"
- `render(code, gene_name)` → 返回三段论字符串，用于日志输出
- 对无法翻译的 token 组合使用泛型模板："大前提: 类型论的基本构造法则 / 小前提: 所有子项类型良构 / 结论: gene_N 为合法 Lambda 项"

## 5. `luca/grammar.py` — 语法组装器
- `LeanAssembler` 类，负责从采样 token 组装合法的 Lean 4 表达式
- **模板系统**（随机选择）：
  - 简单值定义：`def gene_{N} : Nat := {expr}`
  - 函数定义：`def gene_{N} ({params}) : {ret_type} := {expr}`
  - 等式命题：`theorem gene_{N} : {lhs} = {rhs} := by rfl`
  - If-then-else 表达式
  - Lambda 表达式
- 用启发式方法确保括号匹配、类型一致性（不要求完全正确，因为 Lean 编译器会验证）
- `assemble(tokens)` → 返回 (code_string, gene_name) 的候选个体

## 6. `luca/physics.py` — Lean 4 沙箱
- `LeanSandbox` 类
- 在 `.luca_tmp/` 下创建隔离的临时 Lean 文件
- 每次验证时将代码写入临时文件并调用 `lean` CLI
- 使用 `subprocess.run` 执行，带超时控制
- 返回 `(alive: bool, stdout: str, stderr: str)`
- 启动时检查 `lean` 是否可用，不可用则优雅报错

## 7. `luca/pruner.py` — 代谢与剪枝
- `Pruner` 类
- `metabolic_penalty(code)`: 根据代码长度计算代谢惩罚（长代码权重加成更少）
- `is_duplicate(code, history)`: 基于代码字符串哈希判断是否重复
- `apply_decay(urn, rate)`: 对瓮中所有权重施加指数衰减
- `prune_urn(urn, max_size)`: 当瓮超过上限时，移除权重最低的 token

## 8. `luca/engine.py` — 主演化循环
- `EvolutionEngine` 类
- 主循环流程：
  1. 从瓮中采样 token
  2. 组装 Lean 候选代码
  3. 去重检查
  4. Lean 编译器验证
  5. 若通过：强化 token → 创新（注册新基因）→ 用 SyllogismRenderer 翻译为哲学三段论并输出 → 记录到 `evolved_library.lean` → 代谢惩罚 → 剪枝
  6. 若失败：丢弃，轻微调整权重
  7. 随机触发天灾事件
- 使用 `rich` 库实现彩色终端输出，格式与设计文档一致

## 9. `main.py` — CLI 入口
- 使用 `click` 提供命令行接口
- 支持参数：`--max-generations`、`--timeout`、`--output`
- 启动时检查 Lean 环境，打印欢迎信息

## 10. 天灾系统 (Catastrophes)
- 设计 6 种天灾类型，随机触发 + 生态位固化检测双重机制：
  - **质量灭绝** (`mass_extinction`)：移除瓮中 80%-90% 的低权重 token（大灭绝——校准要求须彻底）
  - **中等灭绝** (`moderate_extinction`)：移除 40%-60% 的低权重 token + 幸存者权重增强 1.1-1.5x（生态收缩与选择压力）
  - **基因漂变** (`genetic_drift`)：所有权重向均值回归 30%（模拟种群瓶颈）
  - **寒武纪大爆发** (`cambrian_explosion`)：从存活基因中两两组合生成新的复合 token（模拟共生/杂交）
  - **小行星撞击** (`asteroid_impact`)：随机删除 50% 的 token，但幸存者权重翻倍（模拟极端选择压力）
  - **冰河期** (`ice_age`)：所有 token 权重减半，但 `fun`/`λ` 等抽象构造 token 获得抗冻加成
- 触发条件：
  - **定时触发**：每 50-200 代随机触发一次
  - **停滞触发**：超过 100 代无存活基因 + 瓮容量 ≥ 80% MAX_URN_SIZE → 识别为"生态位固化"，强制触发天灾

## 11. 数据持久化
- 成功编译的 Lean 定义追加写入 `evolved_library.lean`
- 定期保存瓮的状态到 JSON（支持断点续跑），包含进化事件追踪器
- 演化日志保存到 `evolution_log.jsonl`

## 12. 进化事件追踪
- **多细胞化检测**：新基因引用其他 `gene_N` 时，终端输出 `🧬 多细胞化!` 及共生基因列表
- **纪元系统**：追踪五个演化纪元，每次天灾后检测是否满足切换条件
  - 太古宙 → 原初汤时代（首次多细胞化 + 基因 token ≥ 3）
  - 原初汤时代 → 大氧化时代（sorry 占比 > 50% + 多细胞 ≥ 2）
  - 大氧化时代 → 真核时代（sorry 占比 < 20% + 基因 token ≥ 10）
  - 真核时代 → 多细胞时代（多细胞事件 ≥ 10 + 基因 token ≥ 30）
- **Sorry 占比追踪**：监控 sorry 在瓮中的权重占比，用于检测大氧化事件
- 所有事件状态随 `urn_state.json` 持久化，支持断点续跑后恢复

## 实现顺序
1. `pyproject.toml` / `requirements.txt`
2. `luca/config.py`
3. `luca/urn.py`
4. `luca/pruner.py`
5. `luca/physics.py`
6. `luca/grammar.py`
7. `luca/syllogism.py`
8. `luca/engine.py`
9. `main.py`
10. `luca/__init__.py`
