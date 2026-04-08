# 宝可梦知识图谱问答系统

基于 Neo4j 图数据库 + 通义千问 LLM 的宝可梦知识问答系统。

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite |
| 后端 | Python FastAPI |
| 图数据库 | Neo4j Aura (云端) |
| LLM | 通义千问 API |
| 数据源 | PokeAPI |

## 快速启动

### 0. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 NEO4J_PASSWORD 和 DASHSCOPE_API_KEY
```

### 1. 检查环境

```bash
cd backend
python check_env.py
```

### 2. 数据导入

```bash
cd data_pipeline
python run_pipeline.py 10  # 先导入 10 只测试
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问

打开浏览器访问 http://localhost:5173

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/chat` | 主问答接口 |
| POST | `/api/query` | 直接 Cypher 查询 |
| GET | `/api/schema` | 获取图谱 Schema |

## 测试用例

详见 [tests/test_cases.md](tests/test_cases.md)

## 项目结构

```
pokemon-kg/
├── backend/              # FastAPI 后端
│   ├── main.py           # 入口
│   ├── config.py         # 配置
│   ├── check_env.py      # 环境检查
│   ├── routers/          # API 路由
│   ├── services/         # 业务逻辑
│   ├── models/           # 数据模型
│   └── data/             # Cypher 导入脚本
├── data_pipeline/        # 数据管线
│   ├── fetch_pokeapi.py  # 数据抓取
│   ├── transform.py      # 数据转换
│   ├── load_to_neo4j.py  # Neo4j 导入
│   └── run_pipeline.py   # 一键执行
├── frontend/             # Vue 3 前端
│   ├── src/
│   │   ├── App.vue       # 主页面
│   │   ├── api/          # API 封装
│   │   └── main.js
│   └── package.json
├── tests/                # 测试用例
├── .env.example          # 环境变量模板
└── requirements.txt      # Python 依赖
```

## 开发团队

知识工程课程期末大作业

## License

MIT
