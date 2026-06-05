"""
模块名称：应用入口（main）
功能描述：InterviewEcho FastAPI 应用的启动入口。通过 uvicorn 直接运行此文件即可启动服务。
启动命令：uvicorn main:app --host 0.0.0.0 --port 8000
"""

from app import create_app

app = create_app()
