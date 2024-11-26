import json
import os
import re
import time
import shutil
from typing import Dict, List, Any
from fastapi.responses import JSONResponse

from gpt_researcher.actions import stream_output
from gpt_researcher.document.document import DocumentLoader
# 添加这个导入
from backend.utils import write_md_to_pdf, write_md_to_word, write_text_to_md
from multi_agents.main import run_research_task


# 清洗文件名，使其符合文件系统的要求
def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\s-]", "", filename).strip()

# 处理启动命令，生成报告并发送文件路径
async def handle_start_command(websocket, data: str, manager):
    json_data = json.loads(data[6:])
    task, report_type, source_urls, tone, headers, report_source = extract_command_data(
        json_data)

    if not task or not report_type:
        print("错误：缺少任务或报告类型")
        return

    sanitized_filename = sanitize_filename(f"task_{int(time.time())}_{task}")

    report = await manager.start_streaming(
        task, report_type, report_source, source_urls, tone, websocket, headers
    )
    report = str(report)
    file_paths = await generate_report_files(report, sanitized_filename)
    await send_file_paths(websocket, file_paths)

# 处理人类反馈
async def handle_human_feedback(data: str):
    feedback_data = json.loads(data[14:])  # 移除 "human_feedback" 前缀
    print(f"收到人类反馈：{feedback_data}")
    # TODO: 添加逻辑将反馈转发给适当的代理或更新研究状态

# 处理聊天消息
async def handle_chat(websocket, data: str, manager):
    json_data = json.loads(data[4:])
    print(f"收到聊天消息：{json_data.get('message')}")
    await manager.chat(json_data.get("message"), websocket)

# 生成报告文件
async def generate_report_files(report: str, filename: str) -> Dict[str, str]:
    pdf_path = await write_md_to_pdf(report, filename)
    docx_path = await write_md_to_word(report, filename)
    md_path = await write_text_to_md(report, filename)
    return {"pdf": pdf_path, "docx": docx_path, "md": md_path}

# 发送文件路径
async def send_file_paths(websocket, file_paths: Dict[str, str]):
    await websocket.send_json({"type": "path", "output": file_paths})

# 获取配置字典
def get_config_dict(
    langchain_api_key: str, openai_api_key: str, tavily_api_key: str,
    google_api_key: str, google_cx_key: str, bing_api_key: str,
    searchapi_api_key: str, serpapi_api_key: str, serper_api_key: str, searx_url: str
) -> Dict[str, str]:
    return {
        "LANGCHAIN_API_KEY": langchain_api_key or os.getenv("LANGCHAIN_API_KEY", ""),
        "OPENAI_API_KEY": openai_api_key or os.getenv("OPENAI_API_KEY", ""),
        "TAVILY_API_KEY": tavily_api_key or os.getenv("TAVILY_API_KEY", ""),
        "GOOGLE_API_KEY": google_api_key or os.getenv("GOOGLE_API_KEY", ""),
        "GOOGLE_CX_KEY": google_cx_key or os.getenv("GOOGLE_CX_KEY", ""),
        "BING_API_KEY": bing_api_key or os.getenv("BING_API_KEY", ""),
        "SEARCHAPI_API_KEY": searchapi_api_key or os.getenv("SEARCHAPI_API_KEY", ""),
        "SERPAPI_API_KEY": serpapi_api_key or os.getenv("SERPAPI_API_KEY", ""),
        "SERPER_API_KEY": serper_api_key or os.getenv("SERPER_API_KEY", ""),
        "SEARX_URL": searx_url or os.getenv("SEARX_URL", ""),
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "true"),
        "DOC_PATH": os.getenv("DOC_PATH", "./my-docs"),
        "RETRIEVER": os.getenv("RETRIEVER", ""),
        "EMBEDDING_MODEL": os.getenv("OPENAI_EMBEDDING_MODEL", "")
    }

# 更新环境变量
def update_environment_variables(config: Dict[str, str]):
    for key, value in config.items():
        os.environ[key] = value

# 处理文件上传
async def handle_file_upload(file, DOC_PATH: str) -> Dict[str, str]:
    file_path = os.path.join(DOC_PATH, os.path.basename(file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    print(f"文件上传到 {file_path}")

    document_loader = DocumentLoader(DOC_PATH)
    await document_loader.load()

    return {"filename": file.filename, "path": file_path}

# 处理文件删除
async def handle_file_deletion(filename: str, DOC_PATH: str) -> JSONResponse:
    file_path = os.path.join(DOC_PATH, os.path.basename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"文件已删除：{file_path}")
        return JSONResponse(content={"message": "文件删除成功"})
    else:
        print(f"文件未找到：{file_path}")
        return JSONResponse(status_code=404, content={"message": "文件未找到"})

# 执行多代理任务
async def execute_multi_agents(manager) -> Any:
    websocket = manager.active_connections[0] if manager.active_connections else None
    if websocket:
        report = await run_research_task("Is AI in a hype cycle?", websocket, stream_output)
        return {"report": report}
    else:
        return JSONResponse(status_code=400, content={"message": "没有活动的WebSocket连接"})

# 处理WebSocket通信
async def handle_websocket_communication(websocket, manager):
    while True:
        data = await websocket.receive_text()
        if data.startswith("start"):
            await handle_start_command(websocket, data, manager)
        elif data.startswith("human_feedback"):
            await handle_human_feedback(data)
        elif data.startswith("chat"):
            await handle_chat(websocket, data, manager)
        else:
            print("错误：未知命令或未提供足够的参数。")

# 提取命令数据
def extract_command_data(json_data: Dict) -> tuple:
    return (
        json_data.get("task"),
        json_data.get("report_type"),
        json_data.get("source_urls"),
        json_data.get("tone"),
        json_data.get("headers", {}),
        json_data.get("report_source")
    )