"""
AI 智能问答 API — DeepSeek LLM（支持流式输出）
"""

import json
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.config import settings
from app.models.schemas import QARequest, QAResponse

router = APIRouter(prefix="/qa", tags=["qa"])

SYSTEM_PROMPT = """你是遥感目标检测平台的 AI 助手。当前平台使用 YOLO11x-OBB 模型，在 DOTA v1.0 数据集上预训练，支持 15 类遥感目标检测：

飞机(plane)、船舶(ship)、储罐(storage-tank)、棒球场(baseball-diamond)、网球场(tennis-court)、篮球场(basketball-court)、田径场(ground-track-field)、港口(harbor)、桥梁(bridge)、大型车辆(large-vehicle)、小型车辆(small-vehicle)、直升机(helicopter)、环岛(roundabout)、足球场(soccer-ball-field)、游泳池(swimming-pool)。

请用中文回答用户关于遥感目标检测、YOLO 模型、DOTA 数据集、目标检测指标（mAP、Precision、Recall等）、OBB 旋转框等问题。回答要专业、准确、简洁。"""


def _build_messages(req: QARequest) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if req.history:
        for h in req.history:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": req.question})
    return messages


@router.post("/ask", response_model=QAResponse)
async def ask_question(req: QARequest):
    """非流式问答（备用）"""
    if not settings.LLM_API_KEY:
        return QAResponse(
            success=False,
            message="LLM API Key 未配置",
            data={"answer": "请在 .env 中配置 LLM_API_KEY", "references": []},
        )

    messages = _build_messages(req)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.LLM_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            body = resp.json()
            answer = body["choices"][0]["message"]["content"]
    except Exception:
        return QAResponse(
            success=False,
            message="LLM 请求失败",
            data={"answer": "AI 服务暂时不可用，请稍后重试。", "references": []},
        )

    return QAResponse(
        success=True,
        message="获取成功",
        data={"answer": answer, "references": []},
    )


@router.post("/ask/stream")
async def ask_question_stream(req: QARequest):
    """流式问答（SSE）"""
    if not settings.LLM_API_KEY:
        async def error_stream():
            yield f"data: {json.dumps({'error': 'LLM API Key 未配置'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    messages = _build_messages(req)

    async def stream():
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.LLM_BASE_URL}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 1024,
                        "stream": True,
                    },
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
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
