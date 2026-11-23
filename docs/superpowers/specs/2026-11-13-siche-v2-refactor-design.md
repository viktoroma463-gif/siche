# 思拆 v2 重构设计（2026-11-13）

## 目标

把「思拆」从「强制填表 + Mock 规则引擎 + 对话中途弹窗」的演示原型，重构为「DeepSeek 驱动 + 模块标签 + 自由对话 + 复制时审查」的轻量认知支架工作台。

核心基调不变：**先独立、后协作、再审查**；只做认知支架，不替用户完成写作与决策。

## 一、后端

### 1. LLM 接入

- 删除全部 mock 生成函数，`app/llm.py` 只保留真实 DeepSeek 调用。
- 配置（`app/config.py`）：
  - `SICHE_DEEPSEEK_API_KEY`（必有，缺失时健康检查 `configured=false`，发言返回 503）
  - `SICHE_DEEPSEEK_BASE_URL`，默认 `https://api.deepseek.com`
  - `SICHE_DEEPSEEK_MODEL`，默认 `deepseek-chat`
  - `SICHE_DEEPSEEK_TIMEOUT`，默认 60 秒
  - `SICHE_HISTORY_LIMIT`，默认 12 条
- 失败处理：超时 / 4xx / 5xx → 抛 `LLMError`，API 返回 502，前端显示可重试错误；**绝不静默回退模板**。
- 会话记忆：system prompt + 最近 N 条消息（单条截断 2000 字）+ 本轮用户消息。

### 2. System Prompt 三层拼接

```
[公共底层 Base] + [模块基底] + [阶段指令]
```

- **公共底层**（永久生效）：身份、定位、禁止代写、可做/不可做清单、文献一律【待核验】、禁止编造具体文献条目、拒绝套话、必须针对用户原文指出具体盲点、结尾给一个下一步问题、三层分层引导规则。
- **模块基底**：5 个模块 + 通用兜底，文案见 `app/prompts.py`：
  - `general` 通用学术思辨
  - `question` 确定研究问题
  - `literature` 文献线索与检索
  - `claim` 核心观点探讨
  - `evidence` 证据评判
  - `logic` 论证逻辑检查
- **阶段指令**：
  - `stage 0`：正常分析。
  - `stage 1`：只给 2–4 个贴合模块的思考角度 + 启发性反问。
  - `stage 2`：只给空白可填充的句式支架（【】占位），不带完整内容。
  - `stage 3`：只给一个 ≤120 字、标注【仅思路示范，禁止直接复用】的局部片段，严禁完整段落/摘要。
  - `stage 4`：不调用模型，固定返回两个选项（缩小问题 / 保存退出）。
- 模块基底始终保留，保证第 2/3 层引导也是模块专属，而非通用模板。

### 3. 分层引导状态机

- `app/rules/delegation.py` 识别代写/代做诉求：不会做、帮我决定、直接给我、帮我写、替我写、据此写摘要、帮我概括、帮我写论点、直接出稿、完整论文等。
- 会话字段 `delegation_stage`（0–4）：
  - 命中代写诉求且 stage < 4 → stage += 1，按新阶段生成。
  - 用户给出非代写的实质回复（≥8 字）→ 重置为 0。
  - stage = 4 → 不再生成任何支架内容，只给两个选项。
- 阶段 1–3 的内容由 DeepSeek 按当前模块生成；阶段 4 用固定文案，防止模型偷给成品。

### 4. 会话与消息模型

```python
session = {
  id, created_at, mode, mode_label, topic, task_type, task_type_label,
  current_module, messages[], growth, log, checklist,
  delegation_stage, last_substantive_id,
  ui: {show_growth, export_ready, copy_test_message_id, copy_lock_disclaimer}
}
message = {
  id, role, kind, content, ts,
  copyable: bool,          # 是否显示复制按钮
  substantive: bool,      # AI 实质性分析，复制需微测试
  copy_unlocked: bool,    # 该条是否已通过审查
  module, stage
}
```

### 5. API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 返回 `configured`、模型名 |
| POST | `/api/sessions` | 创建会话，无表单，默认通用任务 |
| GET | `/api/sessions/{id}` | 读取会话 |
| POST | `/api/sessions/{id}/module` | 切换当前模块（可选，assist 也可带） |
| POST | `/api/sessions/{id}/assist` | `{message, module}`，核心对话 |
| POST | `/api/sessions/{id}/messages/{mid}/copy-request` | 点复制时调用，返回是否需微测试 |
| POST | `/api/sessions/{id}/messages/{mid}/micro-test` | 提交 80–300 字三选一 |
| POST | `/api/sessions/{id}/messages/{mid}/micro-test/refuse` | 暂不测试 |
| GET | `/api/sessions/{id}/growth` | 成长报告 |
| GET | `/api/sessions/{id}/export-log` | 仅模式 B 可导出 |
| POST | `/api/sessions/{id}/checklist` | 五项审查清单 |
| POST | `/api/sessions/{id}/planning/view` | 规划单查阅记录 |

删除：thinking、confirm-thinking、subtask、assist 内的风险干预、全局 micro-test。

### 6. 成长报告与日志

- 统计：独立思考次数与字数、质疑次数、分层引导触发次数、复制微测试完成次数、复制解锁次数、模块使用分布、任务进度（已探索模块 / 5）。
- 不打能力分、不做等级。
- 导出日志字段改为：①索要成品频次 ②独立思考文本与长度 ③质疑次数 ④分层引导触发次数 ⑤模块使用记录 ⑥复制微测试 ⑦成长快照。

### 7. 规划单（左栏）

- 模块 1：个人思考留存（从用户发言抽取最近 3 条，只追加不覆盖）。
- 模块 2：当前模块的 AI 边界说明（人类主导 / AI 可辅助）。
- 模块 3：五项风险审查清单。

## 二、前端

### 1. 启动

- 删除 `Home.tsx` 与选题表单。
- `App.tsx`：极简「思拆」封面，1 秒淡入淡出，无文字表单/按钮 → 自动恢复上次会话或创建新会话 → 主界面。
- 恢复失败或创建失败：显示错误 + 重试按钮。

### 2. 布局

左右两栏。左栏：人机协作规划单、五项审查清单、成长报告入口、模式与导出。右栏：模块标签行（6 个）+ 消息流 + 输入框。

删除 `ThinkingForm.tsx`、`TaskTree.tsx`、`RiskModal`。

### 3. 模块标签

- 单选，默认「通用思辨」。
- 标签文案与后端 `MODULES` 一致，点击即切换，不中断对话。
- 当前模块在消息上以小标签显示。

### 4. 复制流程

- 每条 AI 实质性消息右上角「复制」。
- 点击 → `copy-request`：
  - 无需审查 → 直接写剪贴板。
  - 需要审查 → 弹窗：局限声明 + 80–300 字三选一微测试。
    - 通过 → 解锁该条 → 自动复制，关闭弹窗。
    - 不合格 → 显示原因/追问，保持弹窗。
    - 拒绝 → 关闭弹窗，保持锁定，可继续对话。
- 对话过程中不弹任何思考闸门或风险干预。
- 剪贴板写入失败时用隐藏 textarea + `execCommand` 兜底。

### 5. 对话中的特殊入口

- 用户输入「查看我的成长报告」→ 打开成长报告。
- 用户输入「导出测评日志」→ 模式 B 准备导出，模式 A 提示只能看成长报告。
- stage 4 消息附「缩小问题 / 保存进度退出」两个按钮。

## 三、错误处理

- 无密钥：顶部提示 + 发言按钮禁用 + 健康检查状态。
- DeepSeek 超时/报错：错误条 + 重试，不生成假内容。
- 微测试：80–300 字，套话过滤；第一次不合格追问一次，仍不合格保持锁定。
- 会话存内存；刷新用 localStorage 恢复。

## 四、测试

- pytest：模块 prompt 拼接、代写意图识别、stage 0→1→2→3→4 与重置、按消息解锁、模式切换、导出。
- 测试中 fake DeepSeek 传输层；运行时无 mock。
- 前端 `npm run build` + `oxlint`。
- 真实联调：配置密钥后发概念/文献/代写三类消息，走通复制→微测试→解锁。

## 五、交付

1. 旧版备份为 `siche-backup-20261113`。
2. 原地改造 `Desktop\siche`。
3. 更新 README、`.env.example`、`docs/PPT素材说明.md`。
4. 重新打包 `siche.zip`，排除 `node_modules`、`dist`、`__pycache__`、`.env`、缓存。
5. 旧界面截图与新界面不符，重新截图（可选，最后确认）。
