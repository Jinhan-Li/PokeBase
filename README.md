# 宝可梦知识图谱问答系统

这是一个面向宝可梦知识图谱的中文问答系统。用户在前端输入自然语言问题，后端调用 DashScope OpenAI 兼容接口生成只读 Cypher，查询 Neo4j 图数据库后再生成中文回答，并在界面中展示答案、Cypher 和原始查询结果。

## 技术栈

| 模块 | 技术 |
|------|------|
| 前端 | Vue 3、Vite、Axios |
| 后端 | Python 3.12、FastAPI、Pydantic、Uvicorn |
| 图数据库 | Neo4j / Neo4j Aura |
| LLM 接入 | DashScope OpenAI 兼容接口，默认模型由 `LLM_MODEL` 控制 |
| 数据源 | PokeAPI |
| 数据管线 | Python 脚本分阶段抓取、建点、建边、构建属性克制和进化关系 |

## 当前功能

- 聊天问答：`POST /api/chat` 完成“问题 -> Cypher -> Neo4j 查询 -> 中文回答”流程。
- Cypher 自愈重试：生成或执行失败时最多重试 5 次，并把错误信息反馈给下一次生成。
- 只读 Cypher 校验：聊天接口会拒绝包含 `CREATE`、`MERGE`、`DELETE`、`SET`、`DROP`、`CALL` 等写入或管理语句的 LLM 输出。
- Schema 对齐：`backend/services/schema_provider.py` 优先读取 `docs/schema.md` 作为 LLM 提示词中的权威图谱 Schema。
- 前端透明展示：聊天界面展示自然语言回答、生成的 Cypher 和 Neo4j 原始结果。
- 数据管线：支持从 PokeAPI 缓存数据，并导入 Pokemon、Type、Ability、Move、属性克制、招式学习和进化关系。
- Neo4j 迁移脚本：根目录提供导出 JSONL 和复制数据库的辅助脚本。

## 环境变量

根目录当前没有 `.env.example`，请手动创建 `.env`。后端和根目录导出/复制脚本会从该文件读取配置。

```env
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io
NEO4J_USER=your_user
NEO4J_PASSWORD=your_password
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_MODEL=deepseek-v4-flash
```

可选变量：

| 变量 | 用途 |
|------|------|
| `LLM_MODEL` | 后端调用的模型名，未设置时默认 `deepseek-v4-flash` |
| `VITE_API_BASE_URL` | 前端请求后端的地址，未设置时默认 `http://localhost:8000` |
| `SOURCE_NEO4J_URI` / `SOURCE_NEO4J_USER` / `SOURCE_NEO4J_PASSWORD` | `exportNeo4j.py` 和 `getNeo4j.py` 的源库配置 |
| `TARGET_NEO4J_URI` / `TARGET_NEO4J_USER` / `TARGET_NEO4J_PASSWORD` | `getNeo4j.py` 的目标库配置 |
| `NEO4J_EXPORT_DIR` | `exportNeo4j.py` 的导出目录，默认 `neo4j_export` |

注意：`data_pipeline/` 当前脚本读取 `data_pipeline/config.py` 中的 Neo4j 配置。如果数据管线要写入其他数据库，需要同步调整该文件中的连接配置。

## 快速启动

### 1. 创建 Python 环境

```bash
conda create -n PokeBase python=3.12 pip -y
conda activate PokeBase
cd backend
pip install -r requirements.txt
```

数据管线脚本还会使用 `requests`。如果当前环境没有安装：

```bash
pip install requests
```

### 2. 检查后端环境

```bash
cd backend
python check_env.py
```

该脚本会检查 `.env`、`NEO4J_PASSWORD`、`DASHSCOPE_API_KEY`、Neo4j 连接，以及 `openai`、`fastapi`、`neo4j` 依赖。

### 3. 构建或更新知识图谱

```bash
cd data_pipeline
python run_pipeline.py
```

`run_pipeline.py` 当前会顺序执行 5 个阶段：

| 阶段 | 脚本 | 作用 |
|------|------|------|
| 0 | `phase0_cache_data.py` | 缓存 PokeAPI 原始数据 |
| 1 | `phase1_nodes.py` | 创建或更新 Pokemon、Type、Ability、Move 节点 |
| 2 | `phase2_basic_relationships.py` | 创建 HAS_TYPE、HAS_ABILITY、CAN_LEARN、Move-HAS_TYPE 关系 |
| 2.5 | `phase2_5_type.py` | 创建 Type 到 Type 的 DAMAGE_TO 属性克制关系 |
| 3 | `phase3_evolution.py` | 创建 EVOLVES_TO 和 EVOLVES_FROM 进化关系 |

当前默认数据规模来自脚本常量：1025 个 Pokemon、18 个 Type、919 个 Move、307 个 Ability、550 条 evolution-chain、20 个 evolution-trigger。`run_pipeline.py` 不解析命令行数量参数。

### 4. 启动后端

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

健康检查：

```bash
curl http://localhost:8000/api/health
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

Vite 配置的默认地址是 `http://localhost:5173`，并会尝试自动打开浏览器。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/chat` | 主问答接口 |
| `POST` | `/api/query` | 直接执行 Cypher，调试用 |
| `GET` | `/api/schema` | 返回当前图谱 Schema 文本和节点/关系列表 |
| `POST` | `/api/import` | 占位接口，当前提示手动运行数据管线 |

### `POST /api/chat`

请求：

```json
{
  "question": "皮卡丘是什么属性？"
}
```

响应：

```json
{
  "answer": "皮卡丘是电属性宝可梦。",
  "cypher": "MATCH ... RETURN ...",
  "data": []
}
```

### `POST /api/query`

请求：

```json
{
  "cypher": "MATCH (p:Pokemon {name: \"pikachu\"}) RETURN p.name",
  "parameters": {}
}
```

该接口直接执行传入的 Cypher，主要用于开发调试，不应暴露给不可信用户。

## 图谱 Schema 概览

完整 Schema 维护在 `docs/schema.md`。当前核心节点和关系如下：

| 类型 | 内容 |
|------|------|
| 节点 | `Pokemon`、`Type`、`Ability`、`Move` |
| Pokemon 属性 | `id`、`name`、`height`、`weight`、`base_experience`、`hp`、`attack`、`defense`、`special_attack`、`special_defense`、`speed` |
| Move 属性 | `id`、`name`、`power`、`accuracy`、`pp`、`priority`、`damage_class` |
| 关系 | `HAS_TYPE`、`HAS_ABILITY`、`CAN_LEARN`、`DAMAGE_TO`、`EVOLVES_TO`、`EVOLVES_FROM` |
| 关系属性 | `HAS_TYPE.slot`、`HAS_ABILITY.is_hidden`、`HAS_ABILITY.slot`、`CAN_LEARN.versions/methods/levels`、`DAMAGE_TO.multiplier`、进化关系的 `min_level/item/details` |

所有名称字段当前按 PokeAPI 英文小写名称存储，例如 `pikachu`、`charizard`、`fire`、`thunderbolt`。

## Neo4j 数据导出与复制

导出当前 `.env` 配置的 Neo4j 数据库到本地 JSONL：

```bash
python exportNeo4j.py
```

默认输出目录为 `neo4j_export/`，包含：

- `nodes.jsonl`
- `relationships.jsonl`
- `metadata.json`

当前 `neo4j_export/metadata.json` 记录的导出规模为 2269 个节点、84451 条关系。

复制源库到目标库：

```bash
python getNeo4j.py --clear-target
```

默认源库读取 `SOURCE_NEO4J_*`，未设置时回退到 `NEO4J_*`；默认目标库是 `bolt://localhost:7687`、用户 `neo4j`、密码 `password`。

## 前端说明

前端入口为 `frontend/src/App.vue`，实际聊天页面在 `frontend/src/views/ChatView.vue`。

主要组件：

| 文件 | 作用 |
|------|------|
| `frontend/src/api/index.js` | Axios 实例和 `/api/chat` 请求封装 |
| `frontend/src/views/ChatView.vue` | 消息列表、loading、错误状态和发送逻辑 |
| `frontend/src/components/ChatInput.vue` | 问题输入框和发送按钮 |
| `frontend/src/components/ChatBubble.vue` | 用户/助手消息、Cypher 和原始数据展示 |

常用命令：

```bash
cd frontend
npm run dev
npm run build
npm run preview
```

## 测试与验证

当前工作区没有 `tests/` 目录。可通过以下方式做手动验证：

```bash
curl http://localhost:8000/api/health
```

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"皮卡丘是什么属性？\"}"
```

推荐测试问题：

- 皮卡丘是什么属性？
- 小火龙有什么特性？
- 火属性克制哪些属性？
- 喷火龙的体重是多少？
- 妙蛙种子如何进化？

## 项目结构

```text
Pokemon/
├── backend/
│   ├── main.py                  # FastAPI 入口和路由注册
│   ├── config.py                # 后端环境变量配置
│   ├── check_env.py             # 后端环境检查
│   ├── routers/                 # /api 路由
│   ├── models/                  # Pydantic 请求/响应模型
│   ├── services/                # LLM、Cypher、Neo4j、Schema 服务
│   └── data/cypher/             # 手写 Cypher 导入脚本
├── data_pipeline/
│   ├── config.py                # 数据管线 Neo4j 配置
│   ├── phase0_cache_data.py     # PokeAPI 原始数据缓存
│   ├── phase1_nodes.py          # 节点构建
│   ├── phase2_basic_relationships.py
│   ├── phase2_5_type.py
│   ├── phase3_evolution.py
│   └── run_pipeline.py
├── docs/
│   └── schema.md                # 当前图谱 Schema
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── neo4j_export/                # Neo4j JSONL 导出结果
├── exportNeo4j.py               # 导出 Neo4j 到 JSONL
├── getNeo4j.py                  # 复制 Neo4j 源库到目标库
└── README.md
```

## 注意事项

- `.env` 不要提交到版本控制。
- `POST /api/query` 是调试接口，不做聊天接口中的只读生成校验。
- 数据管线会写入 Neo4j，请确认目标数据库配置无误后再执行。
- `cache/`、`frontend/node_modules/`、`frontend/dist/`、`.env` 等文件已在 `.gitignore` 中忽略。

## 开发背景

知识工程课程期末大作业。

## License

MIT
