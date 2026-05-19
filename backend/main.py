# 导入FastAPI框架核心类，用于创建Web应用
from fastapi import FastAPI
# 导入CORS中间件，处理跨域资源共享问题
from fastapi.middleware.cors import CORSMiddleware

# ==================== FastAPI应用实例化 ====================
# 创建FastAPI应用对象，配置API文档信息
# 参数说明：
# - title: API文档显示的标题
# - description: API文档的详细描述
# - version: API版本号，便于版本管理
app = FastAPI(
    title="遥感目标智能检测平台",
    description="基于YOLO11的遥感图像目标检测系统API，支持飞机、油罐、立交桥、操场等目标检测",
    version="1.0.0"
)

# ==================== CORS跨域中间件配置 ====================
# 配置跨域访问规则，允许前端应用访问后端API
# 参数说明：
# - allow_origins: 允许访问的源地址列表，["*"]表示允许所有来源（生产环境需限制）
# - allow_credentials: 是否允许携带身份凭证（如Cookie、Token）
# - allow_methods: 允许的HTTP方法（GET、POST、PUT、DELETE等）
# - allow_headers: 允许的请求头字段
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 开发环境允许所有来源，生产环境应指定具体域名
    allow_credentials=True,       # 启用凭证支持
    allow_methods=["*"],          # 允许所有HTTP方法
    allow_headers=["*"],          # 允许所有请求头
)

# ==================== API接口定义 ====================

# 健康检查接口 - GET请求
# @app.get装饰器定义GET请求接口
# tags参数用于在Swagger文档中分组显示
@app.get("/health", tags=["健康检查"])
async def health_check():
    """
    健康检查接口
    用于检测服务运行状态，支持负载均衡器健康检查
    
    返回值说明：
    - status: 服务状态（healthy表示正常）
    - service: 服务名称标识
    - version: 当前服务版本号
    """
    return {
        "status": "healthy",           # 服务健康状态
        "service": "rsod-web-platform", # 服务名称
        "version": "1.0.0"             # 服务版本
    }

# 根路径接口 - GET请求
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.detection import router as detection_router
from app.utils.file_utils import ensure_directories

ensure_directories()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="遥感目标检测平台后端API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

app.include_router(detection_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )