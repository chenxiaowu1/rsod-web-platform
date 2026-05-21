# rsod-web-platform v1.0

遥感目标智能检测平台，基于深度学习 YOLO11-OBB 模型，支持对遥感图像中的典型地物目标进行自动检测与识别。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite |
| 后端 | FastAPI + Ultralytics YOLO |
| 模型 | YOLO11-OBB (Nano / Medium / XLarge) |
| 数据库 | PostgreSQL 15 + Redis 7 |
| 对象存储 | MinIO |
| AI 问答 | DeepSeek LLM |
| 容器化 | Docker Compose |

## 功能概述

- **智能检测**：支持单图检测、批量检测、文件夹上传，可热切换检测模型
- **历史记录**：检测结果持久化存储，支持搜索、筛选与详情查看
- **AI 问答**：基于 DeepSeek 的遥感检测领域知识问答，支持流式对话
- **目标库**：DOTA v1.0 15 类遥感目标类别字典
- **用户系统**：注册 / 登录 / 个人中心 / 检测统计

## 检测类别

支持 DOTA v1.0 数据集定义的 15 类遥感目标：飞机、船舶、储油罐、棒球场、网球场、篮球场、田径场、港口、桥梁、大型车辆、小型车辆、直升机、环形交叉路口、足球场、游泳池。

## 快速开始

```bash
# 1. 启动基础设施
docker-compose up -d

# 2. 启动后端
cd backend
pip install -r requirements.txt
python main.py

# 3. 启动前端
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，后端 API 运行在 `http://localhost:8000`。

## 项目结构

```
rsod-web-platform/
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── api/             # API 接口层
│       ├── components/      # 通用组件
│       ├── layouts/         # 布局组件
│       ├── router/          # 路由配置
│       ├── stores/          # 状态管理 (Pinia)
│       ├── utils/           # 工具函数
│       └── views/           # 页面视图
├── backend/                 # FastAPI 后端
│   └── app/
│       ├── api/             # 接口路由
│       ├── models/          # 模型权重 & Pydantic 定义
│       ├── services/        # 业务逻辑
│       └── utils/           # 工具函数
├── storage/                 # 持久化数据目录
└── docker-compose.yml       # 容器编排
```
