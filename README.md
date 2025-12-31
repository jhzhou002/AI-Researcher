# AI-Researcher 智能科研助手

> 从研究问题到论文草稿的一站式AI科研助手系统

---

## 📋 目录

- [项目简介](#项目简介)
- [环境要求](#环境要求)
- [配置说明](#配置说明)
- [启动指南](#启动指南)
- [使用教程](#使用教程)
- [API文档](#api文档)
- [常见问题](#常见问题)

---

## 项目简介

AI-Researcher是一个生产级的科研智能助手系统，支持完整的研究工作流：

```
文献检索 → 文献分析 → 脉络梳理 → 想法生成 → 方法设计 → 论文草稿
```

### 核心功能

- 🔍 **多源文献检索** - ArXiv + Semantic Scholar
- 📖 **智能文献分析** - LLM驱动的结构化分析
- 🗺️ **研究脉络梳理** - 自动识别研究趋势和空白
- 💡 **创新想法生成** - 基于研究gap的创意生成
- ⚙️ **方法设计** - 自动设计算法框架
- 📝 **论文草稿** - 分章节生成学术论文
- ⚡ **异步处理** - 所有长时任务后台执行，实时进度追踪

---

## 环境要求

### 必需软件

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端运行环境 |
| Redis | 6.0+ | 消息队列 |
| MySQL | 8.0+ | 数据库 |

### 可选软件

| 软件 | 说明 |
|------|------|
| Docker | 容器化部署 |
| Nginx | 生产环境反向代理 |

---

## 配置说明

### 1. 创建环境变量文件

在项目根目录创建 `.env` 文件（可复制 `.env.example`）：

```bash
cp .env.example .env
```

### 2. 必需配置项

#### 数据库配置

```env
# MySQL数据库连接
DATABASE_URL=mysql+pymysql://用户名:密码@主机:端口/数据库名

# 示例（本地）
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_researcher

# 示例（远程）
DATABASE_URL=mysql+pymysql://admin:pass123@49.235.74.98:3306/ai_researcher
```

#### Redis配置

```env
# Redis连接URL
REDIS_URL=redis://localhost:6379/0

# 如果Redis需要密码
REDIS_URL=redis://:password@localhost:6379/0
```

#### JWT安全配置

```env
# JWT密钥 - 必须修改为随机字符串！
SECRET_KEY=your-super-secret-key-change-this-in-production

# Token过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### LLM配置（至少配置一个）

```env
# DeepSeek（推荐，性价比高）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini

# Claude
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Gemini
GEMINI_API_KEY=xxxxxxxxxxxxx
GEMINI_MODEL=gemini-1.5-flash

# Qwen（通义千问）
QWEN_API_KEY=sk-xxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-turbo

# Kimi
KIMI_API_KEY=xxxxxxxxxxxxx
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=moonshot-v1-8k

# 默认LLM（优先使用）
DEFAULT_LLM=deepseek
```

### 3. 完整配置示例

```env
# ============ 数据库 ============
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/ai_researcher

# ============ Redis ============
REDIS_URL=redis://localhost:6379/0

# ============ JWT ============
SECRET_KEY=my-super-secret-key-2024
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============ LLM ============
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
DEFAULT_LLM=deepseek

# ============ 可选配置 ============
LOG_LEVEL=INFO
DEBUG=false
```

---

## 启动指南

### 方式一：开发环境（推荐）

#### 1. 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
cd ..
```

#### 2. 初始化数据库

```bash
python init_db.py
```

成功输出：
```
数据库 ai_researcher 已存在
创建数据库表...
数据库表创建成功！
```

#### 3. 启动Redis（新终端）

```bash
# Windows（使用WSL或Docker）
docker run -d -p 6379:6379 redis

# Linux/Mac
redis-server
```

#### 4. 启动Celery Worker（新终端）

```bash
celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo
```

成功输出：
```
 -------------- celery@xxx v5.3.x
--- ***** -----
[tasks]
  . analysis.landscape
  . analysis.papers
  . generation.ideas
  . generation.method
  . generation.paper_draft
  . literature.discovery
```

#### 5. 启动FastAPI（新终端）

```bash
python run.py
```

成功输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

#### 6. 启动前端（新终端）

```bash
cd frontend
npm run dev
```

成功输出：
```
VITE v7.x.x ready
➜  Local:   http://localhost:5173/
```

### 方式二：快速测试（仅后端）

如果只需要测试API：

```bash
# 终端1：Redis
docker run -d -p 6379:6379 redis

# 终端2：Celery
celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo

# 终端3：FastAPI
python run.py
```

然后访问：http://localhost:8000/docs

---

## 使用教程

### 1. 注册账号

**方式一：通过API**

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@example.com",
    "username": "researcher",
    "password": "your_password"
  }'
```

**方式二：通过前端**

访问 http://localhost:5173/register

### 2. 登录获取Token

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=researcher&password=your_password"
```

返回：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 3. 创建研究项目

```bash
curl -X POST "http://localhost:8000/api/projects" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "大语言模型Agent规划能力研究",
    "keywords": "LLM agent planning reasoning",
    "year_start": 2023,
    "year_end": 2024,
    "field": "nlp"
  }'
```

### 4. 运行研究流程

#### 步骤1：文献检索

```bash
curl -X POST "http://localhost:8000/api/workflows/projects/1/discover?max_results=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

返回任务ID，用于查询进度。

#### 步骤2：查询任务进度

```bash
curl "http://localhost:8000/api/tasks/TASK_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

返回：
```json
{
  "task_id": "abc-123",
  "status": "running",
  "progress": 45,
  "result": {"current_message": "Searching ArXiv..."}
}
```

#### 步骤3：文献分析（等待检索完成后）

```bash
curl -X POST "http://localhost:8000/api/workflows/projects/1/analyze?max_papers=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤4：研究脉络分析

```bash
curl -X POST "http://localhost:8000/api/workflows/projects/1/landscape" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤5：研究想法生成

```bash
curl -X POST "http://localhost:8000/api/workflows/projects/1/ideas?num_ideas=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤6：方法设计

```bash
curl -X POST "http://localhost:8000/api/workflows/projects/1/method?idea_id=IDEA_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤7：论文草稿生成

```bash
curl -X POST "http://localhost:8000/api/workflows/projects/1/draft?idea_id=IDEA_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 使用前端界面

前端提供更友好的操作界面：

1. 访问 http://localhost:5173
2. 登录/注册
3. 创建项目
4. 点击按钮触发各步骤
5. 实时查看进度

---

## API文档

### 在线文档

启动后端后访问：http://localhost:8000/docs

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/projects` | GET/POST | 项目列表/创建 |
| `/api/projects/{id}` | GET/PUT/DELETE | 项目详情 |
| `/api/workflows/projects/{id}/discover` | POST | 文献检索 |
| `/api/workflows/projects/{id}/analyze` | POST | 文献分析 |
| `/api/workflows/projects/{id}/landscape` | POST | 脉络分析 |
| `/api/workflows/projects/{id}/ideas` | POST | 想法生成 |
| `/api/workflows/projects/{id}/method` | POST | 方法设计 |
| `/api/workflows/projects/{id}/draft` | POST | 论文草稿 |
| `/api/tasks/{id}` | GET | 任务状态 |
| `/api/monitor/health` | GET | 健康检查 |
| `/api/monitor/metrics` | GET | 性能指标 |

---

## 常见问题

### Q: 数据库连接失败？

检查MySQL服务是否启动，DATABASE_URL是否正确。

```bash
# 测试连接
mysql -h localhost -u root -p
```

### Q: Celery无法连接Redis？

确保Redis正在运行：

```bash
redis-cli ping
# 应返回：PONG
```

### Q: LLM调用失败？

1. 检查API Key是否正确
2. 检查网络是否能访问LLM服务
3. 查看日志获取详细错误

### Q: 任务一直pending？

确保Celery worker正在运行：

```bash
celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo
```

### Q: 前端无法访问后端？

1. 检查后端是否启动（http://localhost:8000）
2. 检查CORS配置
3. 检查前端.env中的VITE_API_URL

---

## 技术支持

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/monitor/health
- **系统指标**: http://localhost:8000/api/monitor/metrics

---

## 版本信息

- **版本**: 1.0.0-beta
- **更新日期**: 2025-12-31
- **Python**: 3.10+
- **Node.js**: 18+
