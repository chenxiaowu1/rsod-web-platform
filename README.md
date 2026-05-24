# RSOD Web Platform v3.0

遥感目标智能检测平台，支持智能检测、变化检测、视频流检测三大功能，微服务架构，引擎隔离。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Pinia + Vite |
| 主服务 | FastAPI + SQLAlchemy + JWT (bcrypt + access/refresh token) |
| 智能检测 | YOLO11-OBB (DOTA) + SAHI 切片推理 |
| 变化检测 | BAN (ViT + mit-B0/B1) + Open-CD + LEVIR-CD |
| 视频流检测 | YOLO11 (COCO 80 类) + 摄像头实时帧检测 |
| 数据库 | PostgreSQL |
| 缓存 / 限流 | Redis |
| 对象存储 | MinIO |
| AI 问答 | DeepSeek LLM (流式对话 + 知识引用) |
| 容器化 | Docker Compose |

## 架构

```
浏览器 :5173 → 主服务 :8000 (shixi_main)
                  ├── httpx → :8001 检测引擎 (shixi_det)
                  ├── httpx → :8002 变化检测引擎 (shixi_cd)
                  ├── httpx → :8003 视频流引擎 (shixi_video)
```

四个 conda 环境互不污染，引擎各自管理依赖版本。

## 功能

### 智能检测
- 单图 / 批量上传，YOLO11-OBB 三档模型 (Nano / Medium / XLarge)
- 置信度 / IoU 阈值调节，SAHI 切片推理开关
- TIF 遥感影像自动转 PNG 预览
- DOTA v1.0 15 类遥感目标：飞机、船舶、储罐、棒球场、网球场、篮球场、田径场、港口、桥梁、大型车辆、小型车辆、直升机、环岛、足球场、游泳池
- 标注导出：COCO / YOLO / GeoJSON
- 批量结果 ZIP 下载

### 变化检测
- 双时相影像对比，BAN 三档模型 (B0 / L0 / L1)
- LEVIR-CD 数据集，二值分类：变化 / 未变化（仅建筑物变化）
- 自动滑窗推理 (512×512, 50% 重叠)
- 变化比例统计，结果图下载，批量 ZIP 下载

### 视频流检测
- **视频模式**：上传视频逐帧推理 (mp4 / avi / mov)，标注视频下载，逐帧目标统计，结果视频回放
- **摄像头模式**：浏览器摄像头实时帧检测，画框叠加，停止并保存为视频，进入历史记录
- YOLO11 三档模型 (Nano / Medium / XLarge)，COCO 80 类目标

### 其他
- JWT 认证 (access + refresh token)，登录/注册/修改密码
- Redis 限流保护 (检测 / 登录 / 注册 / 刷新)
- 历史记录管理（三 Tab：检测/变化/视频，预览/下载/删除）
- 检测统计分析（每日趋势 / 模型分布 / 置信度分布 / 各类别统计）
- 目标类别库（DOTA 15 类 + 变化检测说明 + COCO 80 类，中英文切换）
- AI 问答（DeepSeek 流式对话 + 知识库引用 + Markdown 渲染）
- 个人中心（全平台任务概览 / 模型使用分布 / 最近活动 / 编辑资料 / 修改密码）

## 快速开始

```bash
# 0. 启动基础设施
docker-compose up -d

# 1. 检测引擎 (shixi_det)
conda activate shixi_det
cd engines/detection_engine && python main.py

# 2. 变化检测引擎 (shixi_cd)
conda activate shixi_cd
cd engines/cd_engine && python main.py

# 3. 视频流引擎 (shixi_video)
conda activate shixi_video
cd engines/video_engine && python main.py

# 4. 主服务 (shixi_main)
conda activate shixi_main
cd backend && python main.py

# 5. 前端
cd frontend && npm run dev
```

前端 `http://localhost:5173`，默认账号 `admin` / `admin123`。

## 页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 智能检测 | /detection | YOLO11-OBB 目标检测，单图 / 批量 |
| 变化检测 | /change-detection | BAN 双时相变化检测，单对 / 批量 |
| 视频流检测 | /video | YOLO11 视频检测 / 摄像头实时检测 |
| AI 问答 | /qa | DeepSeek 流式对话，知识库引用 |
| 历史记录 | /history | 三 Tab：检测 / 变化 / 视频记录，预览 / 下载 / 删除 |
| 检测统计 | /statistics | 三 Tab：检测 / 变化 / 视频统计 |
| 目标库 | /targets | 三 Tab：DOTA 15 类 / 变化检测说明 / COCO 80 类 |
| 个人中心 | /profile | 全平台概览，模型使用分布，最近活动，编辑资料，修改密码 |

## 模型清单

| 引擎 | 快速 | 均衡 | 精准 | 数据集 |
|------|------|------|------|------|
| 智能检测 | yolo11n-obb.pt | yolo11m-obb.pt | yolo11x-obb.pt | DOTA v1.0 |
| 变化检测 | BAN-B0 | BAN-L0 | BAN-L1 | LEVIR-CD |
| 视频流 | yolo11n.pt | yolo11m.pt | yolo11x.pt | COCO |

## 项目结构

```
rsod-web-platform/
├── frontend/                     # Vue 3 前端
│   └── src/
│       ├── api/detection.js      # API 接口 (检测/变化/视频/用户)
│       ├── components/           # Sidebar, Header, LoginModal
│       ├── composables/          # useChatHistory, useChatExport, useExport
│       ├── layouts/              # MainLayout
│       ├── locales/              # zh-CN.js, en.js (i18n)
│       ├── router/               # 路由
│       ├── stores/               # Pinia (auth, detection, changeDetection, video, ui)
│       ├── utils/                # auth, request, paths
│       └── views/                # 8 个页面
├── backend/                      # FastAPI 主服务
│   └── app/
│       ├── api/                  # detection, change_detection, video, auth, qa, user
│       ├── models/               # db_models (ORM) + schemas (Pydantic) + 权重文件
│       │   ├── detection/        # YOLO11-OBB 权重
│       │   ├── change_detection/ # BAN 权重
│       │   └── video/            # YOLO11 权重
│       └── services/             # history_service, auth_service, minio_service, redis_service
├── engines/                      # 推理引擎 (独立 FastAPI)
│   ├── detection_engine/         # YOLO 检测 :8001
│   ├── cd_engine/                # BAN 变化检测 :8002
│   ├── video_engine/             # YOLO 视频流 :8003
│   └── open-cd/                  # Open-CD 工具包
├── docker-compose.yml
└── README.md
```

## 环境清单

| 环境 | Python | torch | 作用 | port |
|------|--------|-------|------|:---:|
| shixi_main | 3.10 | - | 主服务 (认证/DB/MinIO/路由) | 8000 |
| shixi_det | 3.10 | 最新 | 智能检测引擎 | 8001 |
| shixi_cd | 3.8 | 2.0.1 | 变化检测引擎 | 8002 |
| shixi_video | 3.10 | 最新 | 视频流检测引擎 | 8003 |
