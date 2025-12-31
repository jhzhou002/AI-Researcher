# Celery异步任务系统 - 快速启动指南

## 前置要求

1. **Redis** - 消息broker和结果存储
2. **MySQL** - 数据库（已配置）
3. **Python依赖** - celery[redis], redis

## 安装依赖

```bash
pip install "celery[redis]" redis
```

## 启动服务

### 1. 启动Redis

**使用Docker（推荐）**：
```bash
docker run -d -p 6379:6379 --name redis-ai-researcher redis:latest
```

**使用WSL（Windows）**：
```bash
# 在WSL中
sudo service redis-server start
```

**验证Redis运行**：
```bash
redis-cli ping
# 应返回: PONG
```

### 2. 启动Celery Worker

**Windows（使用solo pool）**：
```bash
celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo
```

**Linux/Mac**：
```bash
celery -A backend.tasks.celery_app worker --loglevel=info -c 4
```

### 3. 启动FastAPI

```bash
python run.py
```

## 测试流程

### 1. 运行测试脚本

```bash
python test_celery.py
```

应看到：
```
✅ Celery应用创建成功
✅ 任务模块导入成功
✅ Redis连接成功
✅ 数据库连接成功
```

### 2. 使用API测试

访问：http://localhost:8000/docs

**完整测试流程**：

```python
import requests

# 1. 注册用户
response = requests.post("http://localhost:8000/api/auth/register", json={
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
})

# 2. 登录
response = requests.post("http://localhost:8000/api/auth/login", data={
    "username": "testuser",
    "password": "testpass123"
})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. 创建项目
response = requests.post("http://localhost:8000/api/projects", json={
    "title": "Test Research",
    "keywords": "machine learning transformers",
    "year_start": 2023,
    "year_end": 2024,
    "journal_level": "any",
    "paper_type": "research",
    "field": "ml"
}, headers=headers)
project_id = response.json()["id"]

# 4. 启动文献检索（Celery任务）
response = requests.post(
    f"http://localhost:8000/api/workflows/projects/{project_id}/discover",
    params={"max_results": 20},
    headers=headers
)
task_data = response.json()
task_id = task_data["task_id"]

print(f"任务已提交: {task_id}")

# 5. 轮询任务状态
import time

while True:
    response = requests.get(
        f"http://localhost:8000/api/tasks/{task_id}",
        headers=headers
    )
    task = response.json()
    
    print(f"状态: {task['status']}, 进度: {task['progress']}%")
    
    if task["status"] in ["completed", "failed"]:
        print(f"最终结果: {task['result']}")
        break
    
    time.sleep(2)
```

## 监控

### Celery Flower（可选）

安装：
```bash
pip install flower
```

启动：
```bash
celery -A backend.tasks.celery_app flower
```

访问：http://localhost:5555

## 故障排查

### Redis连接失败
```
❌ Redis连接失败: Error 61 connecting to localhost:6379
```
**解决**：确保Redis正在运行
```bash
docker ps | grep redis
```

### Worker未启动
```
⚠️  未检测到活跃的worker
```
**解决**：在另一个终端启动worker
```bash
celery -A backend.tasks.celery_app worker --loglevel=info --pool=solo
```

### ImportError
```
ModuleNotFoundError: No module named 'celery'
```
**解决**：安装依赖
```bash
pip install "celery[redis]" redis
```

### 任务一直pending
**检查**：
1. Worker是否运行？
2. Redis是否可访问？
3. 检查worker日志查看错误

## 配置

环境变量（.env文件）：
```bash
REDIS_URL=redis://localhost:6379/0
```

## 已实现的任务

1. **literature.discovery** - 多源文献检索
   - ArXiv + Semantic Scholar
   - 自动去重和评分
   - 进度追踪（0-100%）

## 下一步

- [ ] 实现文献分析任务
- [ ] 实现研究想法生成任务
- [ ] 实现论文草稿生成任务
- [ ] 添加WebSocket实时通知
