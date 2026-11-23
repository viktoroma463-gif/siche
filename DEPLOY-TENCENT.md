# 腾讯云云托管部署说明

适用：不想买服务器、希望有一个公网 HTTPS 网址，且使用国内账号（实名 + 支付宝/微信，不需要国际信用卡）。

本目录已准备好：

- `Dockerfile.tencent`：固定监听 8000，使用官方源；
- `Dockerfile.tencent80`：固定监听 80，使用官方源；
- `Dockerfile`：通用 Dockerfile（Render/Railway 用）；
- 上传包：`Desktop\思拆-腾讯云部署包.zip`（根目录含 Dockerfile.tencent、Dockerfile.tencent80、backend、frontend，可直接上传）。

> 当前没有访问密码。拿到网址的人都能使用你的 DeepSeek 额度。建议在 DeepSeek 控制台设置消费上限，不要把网址公开贴出。

---

## 零、找不到入口时先看这里

云托管在「**云开发 CloudBase**」里，不在「云服务器 CVM / 轻量应用服务器」列表里。

- 云开发控制台：<https://console.cloud.tencent.com/tcb>
- 云托管产品页：<https://cloud.tencent.com/product/cloudbaserun>
- 新版云开发控制台：<https://tcb.cloud.tencent.com/dev>

路径：登录腾讯云 → 控制台 → 顶部搜索「云开发」或「云托管」→ 云开发 CloudBase → 创建/选择环境 → 左侧「云托管」→ 新建服务。

如果左侧没有「云托管」：在控制台顶部搜索「云托管」，或在云开发环境的「扩展能力/更多」里找「云托管 CloudBase Run」。

## 一、准备

1. 腾讯云账号，并完成实名认证。
2. 开通「云开发 CloudBase」并创建一个环境（按量计费；地域选上海/广州即可）。
3. 进入该环境的「云托管」页面。
4. 你的 DeepSeek API Key。

---

## 二、用代码包部署（推荐，最简单）

1. 进入腾讯云 → 云托管 → **新建服务**。
2. 部署方式选择 **本地代码 / 代码包上传**。
3. 上传 `Desktop\思拆-腾讯云部署包.zip`。
4. 构建配置：
   - 上传方式：本地代码/代码包
   - 上传 `Desktop\思拆-腾讯云部署包.zip`（zip 根目录就是 Dockerfile.tencent，**不要再多套一层文件夹**）
   - Dockerfile 名称：`Dockerfile.tencent`
   - Dockerfile 目录/目标目录：留空（根目录）
   - 监听端口/服务端口：`8000`

   > **如果你必须用 80 端口**：Dockerfile 名称改为 `Dockerfile.tencent80`，服务端口填 `80`，不需要设置 `PORT`。这个文件固定监听 80，不会出现服务端口和容器端口错位。
5. 环境变量：
   | 变量 | 值 |
   |---|---|
   | `SICHE_DEEPSEEK_API_KEY` | 你的 DeepSeek Key |
   | `SICHE_DEEPSEEK_MODEL` | `deepseek-flash` |
   | `SICHE_DB_PATH` | 有持久存储时填 `/data/siche.db`；没有就填 `/app/siche.db` |

   > 腾讯云专用镜像固定监听 **8000**，不需要设置 `PORT`；控制台的「监听端口/服务端口」填 `8000`。
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
- 确认 Dockerfile 名称与你要用的端口匹配：固定 80 用 `Dockerfile.tencent80`，固定 8000 用 `Dockerfile.tencent`。
- 看构建日志；`Dockerfile.tencent` / `Dockerfile.tencent80` 使用官方源（腾讯云构建环境已验证可访问）。如果某个源失败，按日志换源。
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
