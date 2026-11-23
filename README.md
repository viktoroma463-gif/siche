# 思拆（Siche）

学术写作认知支架智能体。**先独立、后协作、再审查。** 不默认代写；满足条件才生成局部参考草稿；复制操作绑定批判性反思；支持导出完整过程档案用于课程作业提交。

**统一版本**：不再区分「自发个体」与「高校教育 / 测评」模式，所有用户拥有完整功能。

> 产品与功能总览见 [`docs/产品与功能总览.md`](docs/产品与功能总览.md)；完整操作说明见 [`docs/使用说明.md`](docs/使用说明.md)。绿色版解压后同目录也有这两份文档。

## 启动流程

1. 打开页面，先显示 3 秒闪屏：亚麻浅米色背景，正中间是砖红色方框「思拆」logo。
2. 无按钮、无输入框、无多余文字；淡入后停留 3 秒，再淡出。
3. 自动进入左右分栏主协作界面。
4. 上次会话会自动恢复；会话数据持久化在本地 SQLite。

## 核心机制

### 1. 五个模块视角

顶部标签：确定研究问题｜文献线索与检索｜核心观点探讨｜证据评判｜论证逻辑检查。

- 自由点击切换，无强制顺序；再次点击已选模块可取消。
- 不选模块时使用「通用学术思辨」兜底。
- 切换模块只改变后续分析视角，不清空历史对话。

### 2. AI 消息类型与复制行为

| content_type | 含义 | 复制行为 |
|---|---|---|
| `guide` | 纯引导、反问、思考角度 | 直接复制，无弹窗 |
| `scaffold` | 句式支架、要点清单、带警告的局部示范 | 点击复制触发微测试 |
| `generated_draft` | 满足条件后生成的草稿 / 润色参考片段 | 强制触发微测试，不可跳过 |

### 3. 草稿生成四项条件

必须同时满足：

1. 用户已经输出本人思考：草稿、观点判断、自我推理、取舍倾向；多轮自主修改稿也算。
2. 完成一轮思辨来回：AI 已给角度 / 反问 / 提示，用户给出自己的反馈；仅回复「好的、明白了」不算。
3. 用户明确请求：参考片段、改写、整理、润色类写作素材。
4. 不是整篇论文或完整大章节，只允许局部片段。

满足后生成 `generated_draft`，开头强制警告：

> 【⚠️以下为AI参考草稿素材，仅用于写作参照，不能直接复制提交作业，需要你结合自身研究重新改写】

末尾追加：`⚠️已生成AI参考草稿，请查阅左侧风险审查清单开展自我核查`，并触发左侧清单 2 秒浅砖红闪烁。

### 4. 分层引导

用户要求直接代写 / 代做时：

1. 第一层：2–4 个思考角度 + 启发性反问；
2. 第二层：空白可填充的句式支架（【】占位）；
3. 第三层：标注【仅思路示范，禁止直接复用】的局部小片段；
4. 仍坚持：只给「缩小问题」或「保存进度退出」两个选项，并提示「如果你把你的想法、草稿写出来给到我，我就可以尝试为你生成一份仅供参考的草稿片段」。

特殊润色：用户提交两轮以上自己修改后的草稿后，明确提出润色参考版本，可进入 `generated_draft`。

### 5. 复制前批判性微测试

- 对话过程中**不弹任何窗**；只有点击 AI 消息下方的复制按钮才触发。
- 弹窗内容：局限声明 + 80–300 字三选一（接受并微调 / 补充对立思考 / 指出适用边界）。
- **只校验字数与选项，不校验作答对错**；敷衍内容原样保存并导出。
- 提交后解锁本条复制；不提交无法复制。
- 浏览器手动选中、截图无法拦截，也不记入日志。
- 微测试作答持久入库，关闭重开不丢失。

### 6. 左侧栏

- **个人思想留存区**：自动保存用户全部发言，固定高度、内部滚动，带时间戳。
- **研究规划单**：点击标题滑出抽屉，仅覆盖左侧，不遮挡右侧聊天；4 个可编辑栏目（我的问题 / 当前已有的证据 / 尚存疑点 / 下一步打算做什么）；失去焦点自动保存；支持「从对话提取思考预填充」，只提取用户发言，已有内容时确认后追加。
- **风险审查清单**：常驻，无需勾选或提交，纯自我反思。

### 7. 会话导出

一次导出两份文件：

- `siche-<id>.html`：可读过程档案，浏览器直接打开；
- `siche-<id>.json`：原始备份。

包含：会话元信息、完整对话流水（含 content_type）、研究规划单、复制与微测试事件日志、全局备注、完整风险审查清单。HTML 中复制日志默认折叠。导出不包含 API Key、后端配置等敏感信息。

## 运行

需要 **Python 3.10+** 和 **Node.js 18+**。

```powershell
cd siche
Copy-Item .env.example .env
# 编辑 .env，填写 SICHE_DEEPSEEK_API_KEY
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dev.ps1
```

打开 http://127.0.0.1:5174/。API 在 http://127.0.0.1:8010/（健康检查 `/api/health`）。

macOS / Linux：

```bash
cd siche
cp .env.example .env
# 编辑 .env
chmod +x scripts/dev.sh
./scripts/dev.sh
```

## 配置

```env
SICHE_DEEPSEEK_API_KEY=sk-...
SICHE_DEEPSEEK_BASE_URL=https://api.deepseek.com
SICHE_DEEPSEEK_MODEL=deepseek-flash
SICHE_DEEPSEEK_TIMEOUT=60
SICHE_DEEPSEEK_MAX_TOKENS=3000
SICHE_HISTORY_LIMIT=12
```

- 默认 `deepseek-flash`，实测约 10 秒/次；会返回 `reasoning_content`，应用只取正文。
- DeepSeek 官方 API 不带联网搜索；文献线索由模型知识生成，一律标注【待核验】。
- 未配置密钥时界面可打开，但发送按钮禁用。
- 调用失败返回明确错误并允许重试，不回退到本地模板。

## 数据持久化

- 会话、消息、规划单、复制与微测试事件保存在项目根目录 `siche.db`（SQLite）。
- 绿色版保存在 exe 同目录的 `siche.db`。
- 前端用 localStorage 缓存最近会话 id，刷新或重新打开会恢复。

## 开发与测试

```bash
cd backend
python -m pytest -q

cd ../frontend
npm run build
npm run lint
```

## 绿色版

```powershell
.\scripts\build-portable.ps1
```

生成 `dist\思拆\思拆.exe` 与 `Desktop\思拆-绿色版.zip`。接收方解压整个文件夹，把 `.env.example` 复制为 `.env` 并填入自己的密钥，双击 `思拆.exe`。

## Windows 安装包

在开发机上用 Inno Setup 6 编译 `installer\思拆.iss`：

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" ".\installer\思拆.iss"
```

输出 `Desktop\思拆-安装包.exe`。安装到 `%LOCALAPPDATA%\Programs\思拆`，无需管理员权限；安装时填写 DeepSeek Key，写入安装目录 `.env`；创建桌面和开始菜单快捷方式，并带卸载程序。

## 目录

```
backend/app/
  prompts.py          公共 Prompt + 模块视角 + 阶段/草稿许可
  engine.py           会话、content_type、草稿门、复制事件、规划单、导出
  llm.py              DeepSeek 客户端
  store.py            SQLite 会话持久化
  rules/
    delegation.py     代写识别与四层阶段推进
    draft_gate.py     草稿四项条件与润色迭代
    copy_lock.py      80–300 字微测试
frontend/src/
  components/        Splash / AssistThread / PlanDrawer / ThoughtLog / RiskChecklist / Modals
  pages/Workspace.tsx
```

## 边界

- 微测试不校验对错，只做低负荷反思；导出交由授课老师评估。
- 复制锁定只限制应用内一键复制，截图、手动选中无法物理阻止。
- AI 输出严格禁止 Markdown 符号，只用【】标题、换行和空行。
- 本工具不替代教师评价，也不应用来规避学校的生成式 AI 使用规范。
