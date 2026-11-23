# 思拆 v2 重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将「思拆」重构为 DeepSeek 驱动的模块化认知支架工作台，对话零打扰，复制时才触发微测试。

**Architecture:** 后端用「公共 Base + 模块基底 + 阶段指令」三层 system prompt 调 DeepSeek；代写诉求由确定性状态机升到 1–4 层；复制锁定按消息粒度存 `copy_unlocked`。前端改为启动封面 + 左右两栏 + 模块标签。

**Tech Stack:** FastAPI / Pydantic / httpx / DeepSeek Chat Completions；React 19 / TypeScript / Tailwind v4 / Vite。

---

## 文件结构

**后端**
- Modify `backend/app/config.py` — DeepSeek 配置
- Rewrite `backend/app/llm.py` — 真实 API 调用，删除 mock
- Create `backend/app/prompts.py` — Base / 模块 / 阶段 prompt
- Create `backend/app/rules/delegation.py` — 代写识别与阶段推进
- Modify `backend/app/rules/copy_lock.py` — 保留微测试规则
- Modify `backend/app/rules/growth.py` — 新统计口径
- Rewrite `backend/app/engine.py` — 会话、对话、复制、规划单
- Rewrite `backend/app/schemas.py`
- Modify `backend/app/main.py`
- Delete `backend/app/rules/thinking.py`、`risk.py`、`tasks.py`
- Rewrite `backend/tests/*`

**前端**
- Rewrite `frontend/src/types.ts`、`App.tsx`、`api.ts`、`pages/Workspace.tsx`
- Rewrite `frontend/src/components/AssistThread.tsx`、`Modals.tsx`
- Modify `TopBar.tsx`、`PlanningSheet.tsx`、`GrowthReport.tsx`、`index.css`
- Delete `pages/Home.tsx`、`components/ThinkingForm.tsx`、`components/TaskTree.tsx`

**文档/配置**
- Modify `.env.example`、`README.md`、`docs/PPT素材说明.md`

---

## Task 1: DeepSeek 配置与客户端

**Files:** `config.py`, `llm.py`, `.env.example`

- [ ] `Settings` 增加 `siche_deepseek_api_key`、`siche_deepseek_base_url`（默认 `https://api.deepseek.com`）、`siche_deepseek_model`（默认 `deepseek-chat`）、`siche_deepseek_timeout`（60）、`siche_history_limit`（12）；`llm_configured` property。
- [ ] `llm.py` 删除全部 mock 函数，仅保留 `LLMError`、`LLMNotConfigured`、`async chat_completion(messages, temperature=0.5, max_tokens=1800) -> str`。URL 为 `{base}/chat/completions`；超时/HTTP 错误转 `LLMError`。
- [ ] `.env.example` 改为三个 `SICHE_DEEPSEEK_*` 变量。
- [ ] 测试：`pytest backend/tests -q`（此时旧测试会因 mock 删除失败，Task 6 统一修复）。

## Task 2: 三层 Prompt

**Files:** `app/prompts.py`、`tests/test_prompts.py`

- [ ] 定义 `BASE_SYSTEM`（定位、禁止代写、文献待核验、拒绝套话、分层引导四层规则、结尾一个下一步问题）。
- [ ] 定义 `MODULES`：`general/question/literature/claim/evidence/logic`，每项含 `label`、`prompt`、`human_led`、`ai_assist`，文案按规格文档原文。
- [ ] 定义 `STAGE_INSTRUCTIONS = {1:...,2:...,3:...}`；`build_system_prompt(module, stage)` 返回 `base + module + stage`。
- [ ] 测试：文献模块 stage 2 含「文献」与「句式支架」；claim 模块不含「文献梳理」；stage 0 不含阶段指令。

## Task 3: 代写识别与阶段状态机

**Files:** `app/rules/delegation.py`、`tests/test_delegation.py`

- [ ] `DELEGATION_PATTERNS` 覆盖：不会做/帮我决定/直接给我/帮我写/替我写/据此写摘要/帮我概括/帮我写论点/直接出稿/完整论文/成品/代写等。
- [ ] `is_delegation_request(text)`、`advance_stage(session, text)`：命中且 <4 则 +1；非命中且 ≥8 字则归零；返回当前 stage。
- [ ] 测试：0→1→2→3→4；stage 4 不再增加；用户给出「我认为…因为…」后归零。

## Task 4: 引擎重写

**Files:** `app/engine.py`、`app/schemas.py`、`app/main.py`

- [ ] 新会话结构：`current_module`、`delegation_stage`、`messages[{substantive,copy_unlocked,module,stage}]`、`ui.copy_test_message_id`。
- [ ] `create_session`：通用任务，welcome 说明新流程。
- [ ] `assist`：设置模块 → 模式检测 → 主题兜底 → 特殊指令（成长报告/导出）→ 记录独立思考 → 阶段推进 → stage4 固定两选项 → 否则拼 history + DeepSeek → 追加实质消息。
- [ ] `request_copy` / `submit_micro_test` / `refuse_micro_test`：按消息粒度解锁；80–300 字 + 套话过滤。
- [ ] `build_planning_sheet`：个人思考留存 + 当前模块边界 + 五项清单。
- [ ] `growth_report` / `export_log`：新统计口径。
- [ ] `main.py` 路由：health 返回 `configured`；assist 捕获 `LLMNotConfigured→503`、`LLMError→502`；新增 copy-request / micro-test / refuse；删除 thinking/confirm/subtask。
- [ ] 测试：`test_engine.py` monkeypatch `app.llm.chat_completion`，覆盖正常对话、stage 升级、复制解锁。

## Task 5: 复制锁定规则适配

**Files:** `app/rules/copy_lock.py`、`tests/test_copy_lock.py`

- [ ] 保留 `evaluate_micro_test`、`OPTIONS`、`COPY_LOCK_DISCLAIMER`；删去与全局锁定相关的注释。
- [ ] 测试：79 字拒绝、200 字套话追问、具体 200 字解锁。

## Task 6: 后端测试全量修复

**Files:** `tests/conftest.py`、`tests/test_mode.py`、`tests/test_logs.py`，删除 `test_thinking_gate.py`、`test_risk.py`

- [ ] 模式测试适配新会话结构（`create_session("general", "这是课程实验…")`）。
- [ ] 日志测试覆盖 export 字段。
- [ ] 运行 `pytest -q` 全绿。

## Task 7: 前端类型与 API

**Files:** `types.ts`、`api.ts`

- [ ] 新类型：`ModuleKey`、`ModuleMeta`、`Message.copy_unlocked/substantive/module/stage/options`、`Session.modules/runtime.configured`。
- [ ] `api.create()` 无参数；`assist(id,message,module)`；`copyRequest`、`microTest`（返回 `{session,result}`）、`refuseMicroTest`、`setModule`。

## Task 8: 启动封面与主界面

**Files:** `App.tsx`、`pages/Workspace.tsx`、`index.css`

- [ ] 删除 Home；1s logo 淡入淡出；优先恢复 cached session，否则创建。
- [ ] Workspace 左右两栏：左 PlanningSheet + 清单；右 AssistThread。
- [ ] 删除 ThinkingForm / TaskTree / RiskModal。

## Task 9: 协作区与复制弹窗

**Files:** `AssistThread.tsx`、`Modals.tsx`、`TopBar.tsx`、`PlanningSheet.tsx`、`GrowthReport.tsx`

- [ ] 输入框上方 6 个模块标签；默认通用；切换即传 module。
- [ ] 消息气泡显示模块标签；AI 实质消息可点「复制」。
- [ ] 点击复制 → copy-request → 直接复制或弹 `CopyTestModal`（局限声明 + 微测试）。
- [ ] 微测试通过自动复制；拒绝保持锁定；对话零弹窗。
- [ ] stage4 消息渲染两个按钮。
- [ ] 构建：`npm run build` + `npm run lint`。

## Task 10: 文档、联调与打包

- [ ] 更新 README 运行/配置/演示路径；更新 `.env.example`。
- [ ] 配置真实 key 后启动，验证概念/文献/代写三类消息与复制流程。
- [ ] 备份旧版为 `siche-backup-20261113`，重新打包 `siche.zip`（排除 node_modules/dist/.env/缓存）。
- [ ] 更新 `docs/PPT素材说明.md`，标注旧截图待重拍。
