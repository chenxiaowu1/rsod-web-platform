"""
AI 智能问答 API — DeepSeek LLM（支持流式输出 + 知识引用）
"""

import json, re
import httpx
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.config import settings
from app.models.schemas import QARequest, QAResponse

logger = logging.getLogger("rsod.qa")

router = APIRouter(prefix="/qa", tags=["qa"])

SYSTEM_PROMPT = """你是 RSOD 遥感目标智能检测平台的 AI 助手。以下是平台完整功能说明，请据此回答用户问题：

## 平台功能
1. **智能检测** — YOLO11-OBB 模型（Nano/Medium/XLarge 三档），DOTA v1.0 15 类遥感目标：飞机、船舶、储罐、棒球场、网球场、篮球场、田径场、港口、桥梁、大型车辆、小型车辆、直升机、环岛、足球场、游泳池。支持单图/批量上传，SAHI 切片推理，置信度/IoU 阈值调节，标注导出（COCO/YOLO/GeoJSON）。
2. **变化检测** — BAN 模型（B0/L0/L1 三档，ViT + mit 编码器），LEVIR-CD 数据集，二值变化检测（变化/未变化），仅标注建筑物变化。支持双时相影像对比，滑窗推理 512×512（50%重叠），变化比例统计。
3. **视频流检测** — YOLO11 模型（Nano/Medium/XLarge 三档），COCO 80 类目标，支持上传视频逐帧推理（mp4/avi/mov），标注视频下载，逐帧目标统计。另有摄像头实时检测模式，调用浏览器摄像头进行实时帧检测。
4. **目标类别库** — DOTA 15 类 + COCO 80 类（人员/交通/动物/其他 4 组）+ 变化检测说明。
5. **历史记录** — 三 Tab（检测/变化/视频），支持预览、下载、删除，按用户隔离。
6. **检测统计** — 每日趋势、模型分布、置信度分布、各类别统计。
7. **个人中心** — 全平台任务概览、模型使用分布、最近活动、编辑资料、修改密码。

## 技术栈
- 前端: Vue 3 + Element Plus + Vite
- 后端: FastAPI + SQLAlchemy + JWT
- 引擎: YOLO11-OBB / BAN / YOLO11（独立 FastAPI 微服务）
- 数据库: PostgreSQL，对象存储: MinIO
- 容器化: Docker Compose

## 回答要求
- 优先使用中文回答
- 回答专业、准确、简洁
- 若问题超出平台范围，礼貌说明并尝试给出通用建议
- 涉及平台功能时，明确告知用户对应模块路径"""

# ── 知识库（可按关键词匹配引用）──
KNOWLEDGE_BASE = [
    {
        "title": "DOTA v1.0 15 类遥感目标",
        "keywords": ["类别", "目标", "检测类别", "DOTA", "15类", "plane", "ship", "飞机", "船舶"],
        "source": "平台目标类别库 → 遥感检测 · DOTA",
        "content": "飞机(plane)、船舶(ship)、储罐(storage-tank)、棒球场(baseball-diamond)、网球场(tennis-court)、篮球场(basketball-court)、田径场(ground-track-field)、港口(harbor)、桥梁(bridge)、大型车辆(large-vehicle)、小型车辆(small-vehicle)、直升机(helicopter)、环岛(roundabout)、足球场(soccer-ball-field)、游泳池(swimming-pool)",
    },
    {
        "title": "YOLO11-OBB 模型说明",
        "keywords": ["模型", "YOLO", "OBB", "检测", "yolo11", "旋转框", "obb"],
        "source": "智能检测 → 模型配置",
        "content": "三档模型：YOLO11n-OBB (2.7M参数，快速)、YOLO11m-OBB (20.9M参数，均衡)、YOLO11x-OBB (58.8M参数，精准)。支持 OBB 旋转边界框检测，SAHI 切片推理大图。",
    },
    {
        "title": "BAN 变化检测模型说明",
        "keywords": ["变化检测", "BAN", "LEVIR", "双时相", "变化", "change"],
        "source": "变化检测 → 模型配置",
        "content": "三档模型：BAN-B0 (ViT-B/32+mit-b0，快速)、BAN-L0 (ViT-L/14+mit-b0，均衡)、BAN-L1 (ViT-L/14+mit-b1，精准)。LEVIR-CD 数据集训练，二值变化掩膜（变化/未变化），仅标注建筑物变化。",
    },
    {
        "title": "视频流检测模型说明",
        "keywords": ["视频", "video", "摄像头", "camera", "YOLO11", "帧"],
        "source": "视频流检测 → 模型配置",
        "content": "三档模型：YOLO11n (2.6M参数，快速)、YOLO11m (20.9M参数，均衡)、YOLO11x (56.9M参数，精准)。COCO 80 类目标，支持视频文件上传和摄像头实时检测两种模式。",
    },
    {
        "title": "SAHI 切片推理",
        "keywords": ["SAHI", "切片", "大图", "slice", "sahi"],
        "source": "智能检测 → SAHI 切片开关",
        "content": "SAHI 将大图切成 640×640 小块逐块检测后合并，推荐边长 > 2000px 时开启，可提升小目标检出率。小图（≤2000px）建议关闭。",
    },
    {
        "title": "COCO 80 类目标",
        "keywords": ["COCO", "视频类别", "person", "car", "行人"],
        "source": "平台目标类别库 → 视频流 · COCO",
        "content": "视频流检测支持 COCO 80 类目标，分 4 组：人员（person/bicycle/car/motorcycle）、交通（airplane/bus/train/truck/boat/traffic light/fire hydrant/stop sign）、动物（bird/cat/dog/horse/sheep/cow/elephant/bear/zebra/giraffe）、其他（backpack/umbrella/chair/tv/laptop/book等）。",
    },
    {
        "title": "标注导出格式",
        "keywords": ["导出", "COCO", "YOLO", "GeoJSON", "标注", "export"],
        "source": "智能检测 → 检测结果 → 导出",
        "content": "支持三种标注导出格式：COCO JSON（标准目标检测格式）、YOLO TXT（归一化坐标）、GeoJSON（地理空间格式）。检测完成后在结果面板或历史记录详情中导出。",
    },
]


def _match_references(question: str) -> list[dict]:
    """根据问题关键词匹配知识库引用。"""
    q_lower = question.lower()
    matched = []
    for item in KNOWLEDGE_BASE:
        if any(kw.lower() in q_lower for kw in item["keywords"]):
            matched.append({"title": item["title"], "source": item["source"]})
    return matched[:3]  # 最多 3 条


def _build_messages(req: QARequest) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if req.history:
        for h in req.history:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": req.question})
    return messages


@router.post("/ask", response_model=QAResponse)
async def ask_question(req: QARequest):
    if not settings.LLM_API_KEY:
        return QAResponse(success=False, message="LLM API Key 未配置",
                          data={"answer": "请在 .env 中配置 LLM_API_KEY", "references": []})

    messages = _build_messages(req)
    references = _match_references(req.question)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.LLM_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
                json={"model": settings.LLM_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 1024},
            )
            resp.raise_for_status()
            body = resp.json()
            answer = body["choices"][0]["message"]["content"]
    except Exception:
        logger.error("LLM 非流式请求失败", exc_info=True)
        return QAResponse(success=False, message="LLM 请求失败",
                          data={"answer": "AI 服务暂时不可用，请稍后重试。", "references": []})

    logger.info("非流式问答完成，回答长度: %d 字", len(answer))
    return QAResponse(success=True, message="获取成功", data={"answer": answer, "references": references})


@router.post("/ask/stream")
async def ask_question_stream(req: QARequest):
    if not settings.LLM_API_KEY:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'LLM API Key 未配置'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    messages = _build_messages(req)
    references = _match_references(req.question)

    async def stream():
        # 先发送引用信息
        yield f"data: {json.dumps({'references': references})}\n\n"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST", f"{settings.LLM_BASE_URL}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
                    json={"model": settings.LLM_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 1024, "stream": True},
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                yield f"data: {json.dumps({'done': True})}\n\n"
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0]["delta"]
                                content = delta.get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except (json.JSONDecodeError, KeyError, IndexError):
                                pass
        except Exception as e:
            logger.error("LLM 流式请求失败: %s", e)
            yield f"data: {json.dumps({'error': 'AI 服务暂时不可用'})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
