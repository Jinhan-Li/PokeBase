# 宝可梦知识图谱问答系统前端说明文档

## 1. 项目简介

本前端项目是“宝可梦知识图谱问答系统”的用户交互界面，使用 Vue 3 + Vite + Axios 开发。

用户可以在页面中输入宝可梦相关问题，例如：

- 皮卡丘是什么属性？
- 小火龙有什么特性？
- 火属性克制哪些属性？

前端会将用户问题发送到后端 `/api/chat` 接口，并展示后端返回的自然语言答案、Cypher 查询语句和原始查询结果。

---

## 2. 技术栈

| 技术 | 版本建议 | 作用 |
|---|---|---|
| Node.js | 18.x 或 20.x | 前端运行环境 |
| npm | 9.x 或以上 | 包管理工具 |
| Vue | ^3.5.13 | 前端框架 |
| Vite | ^6.0.7 | 前端构建工具 |
| Axios | ^1.7.9 | HTTP 请求库 |

---

## 3. 项目目录结构

    frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.development
    ├── .gitignore
    └── src/
        ├── main.js
        ├── App.vue
        ├── style.css
        ├── api/
        │   └── index.js
        ├── views/
        │   └── ChatView.vue
        └── components/
            ├── ChatBubble.vue
            └── ChatInput.vue

---

## 4. 安装与运行

### 4.1 进入前端目录

    cd frontend

### 4.2 安装依赖

    npm install

### 4.3 启动开发服务器

    npm run dev

启动成功后访问：

    http://localhost:5173

---

## 5. 后端接口配置

前端默认连接后端地址：

    http://localhost:8000

该地址配置在 `.env.development` 文件中：

    VITE_API_BASE_URL=http://localhost:8000

如果后端部署在其他地址，需要修改：

    VITE_API_BASE_URL=http://你的服务器地址:端口

修改后需重启前端：

    npm run dev

---

## 6. 后端接口要求

接口：

    POST /api/chat

请求体：

    {
      "question": "皮卡丘是什么属性？"
    }

返回体：

    {
      "answer": "皮卡丘是电属性宝可梦。",
      "cypher": "MATCH (p:Pokemon {name:'pikachu'})-[:HAS_TYPE]->(t:Type) RETURN t.name",
      "data": [
        { "name": "electric" }
      ]
    }

字段说明：

- answer：自然语言回答  
- cypher：查询语句（可选）  
- data：数据库原始结果  

---

## 7. 主要文件说明

### 7.1 api/index.js
- 封装 Axios 请求
- 统一错误处理
- 对接 `/api/chat`

### 7.2 ChatView.vue
- 主聊天页面
- 管理消息列表
- 调用后端接口
- 控制 loading 和错误状态

### 7.3 ChatBubble.vue
- 渲染消息气泡
- 区分用户 / AI
- 展示回答 / Cypher / 数据

### 7.4 ChatInput.vue
- 输入框组件
- Enter 发送
- 防重复提交

---

## 8. 常用命令

启动开发环境：

    npm run dev

打包项目：

    npm run build

预览打包结果：

    npm run preview

---

## 9. 常见问题与解决方案

### 问题 1：npm install 失败
解决：
- 确认 Node.js ≥ 18
- 切换镜像：

    npm config set registry https://registry.npmmirror.com

---

### 问题 2：发送请求失败
检查：
- 后端是否启动
- 接口地址是否正确
- `.env.development` 是否配置正确

---

### 问题 3：跨域 CORS 报错

后端需加入：

    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

---

### 问题 4：修改 .env 不生效

需要重启：

    npm run dev

---

### 问题 5：端口冲突

修改 vite.config.js：

    port: 5174

---

## 10. 前后端联调注意事项

- 前端默认端口：5173  
- 后端默认端口：8000  
- 必须存在接口 `/api/chat`  
- 请求字段必须为 `question`  
- 返回建议包含 `answer/cypher/data`  
- 不同端口需配置 CORS  
- 修改环境变量需重启前端  

---

## 11. 推荐测试问题

    皮卡丘是什么属性？
    小火龙有什么特性？
    火属性克制哪些属性？
    喷火龙的体重是多少？
    妙蛙种子如何进化？

---

## 12. 前端成员工作说明

负责内容：

1. Vue 3 + Vite 项目搭建  
2. 聊天界面开发  
3. Axios API 对接  
4. 消息展示（用户 / AI）  
5. loading / 错误处理 / 自动滚动  
6. 展示 answer / cypher / data  
7. 前后端联调  

---

## 13. 运行流程总结

    cd frontend
    npm install
    npm run dev

浏览器访问：

    http://localhost:5173

输入问题并得到回答，即表示运行成功。