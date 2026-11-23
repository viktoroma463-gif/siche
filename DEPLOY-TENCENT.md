# 腾讯云云托管部署说明

适用：不想买服务器、希望有一个公网 HTTPS 网址，且使用国内账号（实名 + 支付宝/微信，不需要国际信用卡）。

本目录已准备好：

- `Dockerfile.tencent`：腾讯云专用，基础镜像、npm、pip 都走国内镜像，构建更快；
- `Dockerfile`：通用 Dockerfile（Render/Railway 用）；
- 上传包：`Desktop\思拆-腾讯云部署包.zip`（根目录就是 Dockerfile.tencent、backend、frontend，可直接上传）。

> 当前没有访问密码。拿到网址的人都能使用你的 DeepSeek 额度。建议在 DeepSeek 控制台设置消费上限，不要把网址公开贴出。

---

## 一、准备

1. 腾讯云账号，并完成实名认证。
2. 开通「云托管 / CloudBase 云托管」服务（控制台搜索“云托管”或“CloudBase”）。
3. 你的 DeepSeek API Key。

---

## 二、用代码包部署（推荐，最简单）

1. 进入腾讯云 → 云托管 → **新建服务**。
2. 部署方式选择 **本地代码 / 代码包上传**。
3. 上传 `Desktop\思拆-腾讯云部署包.zip`。
4. 构建配置：
   - Dockerfile 路径：`Dockerfile.tencent`
   - 构建上下文：根目录（默认）
   - 服务端口：`8000`
5. 环境变量：
   | 变量 | 值 |
   |---|---|
   | `SICHE_DEEPSEEK_API_KEY` | 你的 DeepSeek Key |
   | `SICHE_DEEPSEEK_MODEL` | `deepseek-flash` |
   | `SICHE_DB_PATH` | 有持久存储时填 `/data/siche.db`；没有就填 `/app/siche.db` |
   | `PORT` | `8000`（如果控制台要求指定端口） |
6. 点击 **部署 / 发布**，等待构建完成（首次约 5–15 分钟）。
7. 在服务详情里找到默认公网域名（通常是 `https://xxx.service.tcloudbase.com` 之类），浏览器打开。
8. 健康检查地址：`https://你的域名/api/health`，应返回 `{"ok":true,...}`。

---

## 三、用 Git 仓库部署（如果你想把代码放 Gitee/GitHub）

1. 把项目推到一个 Git 仓库：
   ```bash
   cd siche
   git init
   git add .
   git commit -m "deploy siche"
   git remote add origin <你的仓库地址>
   git push -u origin main
   ```
2. 云托管 → 新建服务 → **Git 仓库** → 关联仓库 → 分支 `main`。
3. Dockerfile 路径填 `Dockerfile.tencent`，服务端口 `8000`。
4. 环境变量同上，部署。

> 如果控制台没有 Gitee 选项，就用上面的代码包上传，或先用 GitHub。

---

## 四、持久化（重要）

云托管默认是无状态容器：没有挂载持久存储时，SQLite 数据库会在实例重建/重新部署后重置。

- 如果控制台的“存储/文件存储”支持挂载 CFS 或持久卷：
  - 挂载路径填 `/data`
  - 环境变量 `SICHE_DB_PATH=/data/siche.db`
- 如果没有持久存储或不想额外购买：
  - 保持 `SICHE_DB_PATH=/app/siche.db`
  - 每次重新部署后会话会清空；重要记录请先在网页里「导出会话档案」下载 HTML + JSON。

> 云托管/CFS 的具体计费与是否支持挂载，以腾讯云控制台和文档为准。

---

## 五、部署后自测

1. 打开 `https://你的域名/api/health`：
   - `configured: true` 表示密钥已读到；
   - `model: deepseek-flash` 表示模型正确。
2. 打开首页，应该先看到 3 秒闪屏，然后进入协作区。
3. 发一条「什么是认知负荷？」：
   - 能返回分析，说明 DeepSeek 调用成功；
   - 顶部如果显示“未配置密钥”，检查环境变量并重新部署。

---

## 六、常见问题

**构建失败**
- 确认 Dockerfile 路径是 `Dockerfile.tencent`（不是 `Dockerfile`）。
- 看构建日志；常见原因是 npm/pip 网络。`Dockerfile.tencent` 已使用国内镜像。
- 如果 `npm ci` 报 lockfile 不一致：本地执行 `npm install` 后重新打包/提交。

**打开 502 / 503**
- 503：`SICHE_DEEPSEEK_API_KEY` 没配置或为空。
- 502：DeepSeek 超时/额度问题，看服务日志。

**端口不对**
- 服务端口填 `8000`；环境变量 `PORT=8000`。
- Dockerfile 默认监听 8000，`${PORT}` 有值时跟随平台端口。

**数据没了**
- 没有挂载持久存储；重新部署会重置 SQLite。先导出，或挂 CFS 到 `/data`。

**想加访问密码**
- 当前没有密码。需要的话可以加 HTTP Basic Auth：设置 `SICHE_ACCESS_PASSWORD`，打开链接先弹用户名/密码框。这个需要改代码，可以后续加。

---

## 七、费用提示

- 云托管按量计费，新用户通常有免费额度/低消，具体以腾讯云控制台为准。
- CFS/持久存储可能单独计费。
- 长期低流量演示成本通常不高，但请以控制台账单为准。
- 不想产生费用时，可以随时停用服务；本地安装包/绿色版仍可继续使用。
