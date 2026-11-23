# 思拆部署说明（永久网址）

这个应用是 **FastAPI + React + SQLite + DeepSeek** 的全栈应用，不能只传静态文件。要得到永久网址，需要一台一直运行的服务器。

> 国内腾讯云方案见 [`DEPLOY-TENCENT.md`](DEPLOY-TENCENT.md)，上传包为 `Desktop\思拆-腾讯云部署包.zip`，无需国际信用卡。

本目录已经准备好：

- `Dockerfile`：多阶段构建前端 + 后端，单容器运行；
- `render.yaml`：Render Blueprint 配置；
- `railway.json`：Railway 配置；
- `.dockerignore`：排除本地环境与密钥；
- 后端支持 `SICHE_WEB_DIR`（静态前端目录）与 `SICHE_DB_PATH`（SQLite 路径）环境变量。

> 注意：当前**没有访问密码**。拿到网址的人都能使用你的 DeepSeek 额度。建议在 DeepSeek 控制台设置消费上限，且不要把网址公开贴出。需要加密码可以后续加 HTTP Basic Auth。

---

## 方案 A：Render（推荐，最简单）

### 前提

- 一个 GitHub 账号；
- 一个 Render 账号（用 GitHub 登录即可）；
- 需要持久化 SQLite 时，使用 Render 的 **Starter** 付费实例（约 $7/月）并挂 1GB 磁盘；免费实例没有磁盘，SQLite 会在重启/重新部署后重置。

### 步骤

1. 把本项目推到一个 GitHub 仓库：
   ```bash
   cd siche
   git init
   git add .
   git commit -m "deploy siche"
   # 在 GitHub 新建空仓库后：
   git remote add origin https://github.com/<你的用户名>/siche.git
   git push -u origin main
   ```
   `.env`、`siche.db`、`node_modules`、`.venv` 已被 `.gitignore` 排除，不会上传。

2. 打开 Render → **New** → **Blueprint** → 连接刚才的仓库。
3. Render 会读取 `render.yaml`，创建 Web Service。
4. 在环境变量页填写：
   - `SICHE_DEEPSEEK_API_KEY`：你的 DeepSeek 密钥（`sync: false`，不会从仓库读取）
   - `SICHE_DEEPSEEK_MODEL`：`deepseek-flash`（已在配置里）
5. 点击 **Apply / Deploy**，等待构建完成。
6. 打开 Render 给出的 `https://siche-xxxx.onrender.com` 网址。

### 想先用免费实例

把 `render.yaml` 改成：

```yaml
plan: free
# 删除 disk 段
# 删除 SICHE_DB_PATH（默认写到容器内 /app/siche.db）
```

免费实例会在无访问时休眠，首次打开可能需要几十秒；重新部署后 SQLite 数据会丢失。重要会话请先导出 HTML/JSON。

---

## 方案 B：Railway

### 前提

- GitHub 账号；
- Railway 账号（需要绑定支付方式/试用额度）。

### 步骤

1. 同上，把项目推到 GitHub。
2. Railway → **New Project** → **Deploy from GitHub repo** → 选择仓库。
3. Railway 会读取 `railway.json` 与 `Dockerfile` 构建。
4. 在服务设置里添加 **Volume**：
   - Mount path：`/data`
   - 大小：1GB 左右即可
5. 在 **Variables** 添加：
   - `SICHE_DEEPSEEK_API_KEY=你的密钥`
   - `SICHE_DEEPSEEK_MODEL=deepseek-flash`
   - `SICHE_DB_PATH=/data/siche.db`
6. 在 **Settings → Networking** 点击 **Generate Domain**，得到永久网址。

---

## 方案 C：任意 Docker 服务器 / 云主机

```bash
docker build -t siche .
docker run -d --name siche \
  -p 8000:8000 \
  -e SICHE_DEEPSEEK_API_KEY=sk-你的密钥 \
  -e SICHE_DEEPSEEK_MODEL=deepseek-flash \
  -e SICHE_DB_PATH=/data/siche.db \
  -v /opt/siche-data:/data \
  --restart unless-stopped \
  siche
```

然后在前面加 Nginx / Caddy 做 HTTPS 反向代理到 `127.0.0.1:8000`。

---

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `SICHE_DEEPSEEK_API_KEY` | 是 | DeepSeek 密钥，只在服务器环境变量里配置，不要写进仓库 |
| `SICHE_DEEPSEEK_MODEL` | 否 | 默认 `deepseek-flash` |
| `SICHE_DB_PATH` | 否 | SQLite 路径；有持久卷时用 `/data/siche.db` |
| `SICHE_WEB_DIR` | 否 | Dockerfile 已设为 `/app/web`，本地开发不用管 |
| `PORT` | 否 | 平台自动注入；Dockerfile 默认 8000 |

---

## 本地 Docker 自测

```bash
docker build -t siche .
docker run --rm -p 8012:8000 \
  -e SICHE_DEEPSEEK_API_KEY=sk-你的密钥 \
  -e SICHE_DB_PATH=/app/siche.db \
  siche
```

打开 http://127.0.0.1:8012/ ，健康检查 http://127.0.0.1:8012/api/health。

---

## 数据与备份

- 有持久卷：SQLite 在 `/data/siche.db`，重启/重新部署不丢。
- 没有持久卷：SQLite 在容器内，重新部署会重置。
- 重要会话请在网页里点「导出会话档案」，下载 HTML + JSON 保存到本地。
- `.env` 不在镜像里；密钥只通过平台环境变量注入。

---

## 常见问题

**构建失败**
- 看平台构建日志。前端需要 Node 22（Dockerfile 已用 `node:22-alpine`）；后端 Python 3.12。
- `npm ci` 失败通常是 `frontend/package-lock.json` 与 `package.json` 不同步；本地 `npm install` 后重新提交。

**打开显示 502 / 503**
- 503：`SICHE_DEEPSEEK_API_KEY` 没配上。
- 502：DeepSeek 超时或额度问题，看平台日志。

**免费实例第一次打开很慢**
- Render 免费服务会休眠，首次访问需要唤醒。

**数据没了**
- 没用持久卷，重新部署后 SQLite 被重置。改用带磁盘的实例，或先导出。

**想加访问密码**
- 当前没有密码。需要的话可以加 HTTP Basic Auth：设置 `SICHE_ACCESS_PASSWORD`，所有请求先弹用户名/密码框。这个需要改代码，可后续加。

---

## 本地安装包 / 绿色版

不想部署到公网时，继续使用：

- `Desktop\思拆-安装包.exe`（安装到本机）
- `Desktop\思拆-双击即用.zip`（免安装，本机双击）
- `Desktop\思拆-绿色版.zip`（可分享，对方填自己的 key）
