# RSOD Web Platform v3.0

遥感目标智能检测平台，支持目标检测、变化检测、视频流检测三大功能，微服务架构，引擎隔离。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite |
| 主服务 | FastAPI + SQLAlchemy + JWT |
| 目标检测 | YOLO11-OBB (DOTA) + SAHI 切片推理 |
| 变化检测 | BAN (ViT + mit-B0/B1) + Open-CD |
| 视频流检测 | YOLO11 + 逐帧推理 |
| 数据库 | PostgreSQL |
| 对象存储 | MinIO |
| AI 问答 | DeepSeek LLM |
| 容器化 | Docker Compose |

## 架构

```
浏览器 :5173 → 主服务 :8000 (shixi_main)
                  ├── httpx → :8001 检测引擎 (shixi_det)
                  ├── httpx → :8002 变化检测引擎 (shixi_cd)
                  └── httpx → :8003 视频流引擎 (shixi_video)
```

四个 conda 环境互不污染，引擎各自管理 torch 版本。

## 功能

### 智能检测
- 单图 / 批量上传，YOLO11-OBB 三档模型 (Nano / Medium / XLarge)
- 置信度 / IoU 阈值调节，SAHI 切片推理开关
- DOTA v1.0 15 类遥感目标：飞机、船舶、储罐、棒球场、网球场、篮球场、田径场、港口、桥梁、大型车辆、小型车辆、直升机、环岛、足球场、游泳池
- 标注导出：COCO / YOLO / GeoJSON

### 变化检测
- 双时相影像对比，BAN 三档模型 (Nano / Medium / XLarge)
- 自动滑窗推理 (512×512, 50% 重叠)
- 变化比例统计，结果图下载

### 视频流检测
- 上传视频逐帧推理 (mp4 / avi / mov)
- YOLO11 三档模型 (Nano / Medium / XLarge)
- 标注视频下载，逐帧目标统计

### 其他
- JWT 认证 (access + refresh token)
- 历史记录管理、检测统计分析
- 目标类别库 (15 类遥感目标)
- AI 问答 (DeepSeek 流式对话)

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

首次访问无需登录，点击上传/检测/AI 问答时会自动弹出登录框。右上角头像未登录时显示"点击登录"。

## 页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 智能检测 | /detection | YOLO11-OBB 目标检测 |
| 变化检测 | /change-detection | BAN 双时相变化检测 |
| 视频流检测 | /video | YOLO11 视频逐帧推理 |
| 历史记录 | /history | 三 Tab：检测/变化/视频记录 |
| 检测统计 | /statistics | 三 Tab：检测/变化/视频统计 |
| 目标库 | /targets | 三 Tab：DOTA/变化说明/COCO |
| AI 问答 | /qa | DeepSeek 流式对话 |
| 个人中心 | /profile | 账户信息与检测统计 |

登录/注册改为模态框，不再作为独立页面。

## 模型清单

| 引擎 | 快速 | 均衡 | 精准 | 数据集 |
|------|------|------|------|------|
| 目标检测 | yolo11n-obb.pt | yolo11m-obb.pt | yolo11x-obb.pt | DOTA v1.0 |
| 变化检测 | ban_vit-b32...pth | ban_vit-l14...pth | ban_vit-l14...pth | LEVIR-CD |
| 视频流 | yolo11n.pt | yolo11m.pt | yolo11x.pt | COCO |

## 项目结构

```
rsod-web-platform/
├── frontend/                     # Vue 3 前端
│   └── src/
│       ├── api/detection.js      # API 接口 (检测/变化/视频)
│       ├── components/           # Sidebar, Header, LoginModal
│       ├── router/               # 路由
│       ├── utils/                # auth, request
│       └── views/                # 8 个页面
├── backend/                      # FastAPI 主服务
│   └── app/
│       ├── api/                  # detection, change_detection, video, auth, qa, user
│       ├── models/               # ORM + Pydantic + 权重
│       │   ├── detection/        # YOLO11-OBB 权重
│       │   ├── change_detection/ # BAN 权重
│       │   └── video/            # YOLO11 权重
│       └── services/             # history_service, auth_service, minio_service
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
| shixi_det | 3.10 | 最新 | 目标检测引擎 | 8001 |
| shixi_cd | 3.8 | 2.0.1 | 变化检测引擎 | 8002 |
| shixi_video | 3.10 | 最新 | 视频流检测引擎 | 8003 |
