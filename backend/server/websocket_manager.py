import asyncio
import datetime
from typing import Dict, List

from fastapi import WebSocket

from backend.report_type import BasicReport, DetailedReport
from backend.chat import ChatAgentWithMemory

from gpt_researcher.utils.enum import ReportType, Tone
from multi_agents.main import run_research_task
from gpt_researcher.actions import stream_output  # 导入 stream_output


class WebSocketManager:
    """管理WebSocket连接"""

    def __init__(self):
        """初始化WebSocketManager类"""
        self.active_connections: List[WebSocket] = []
        self.sender_tasks: Dict[WebSocket, asyncio.Task] = {}
        self.message_queues: Dict[WebSocket, asyncio.Queue] = {}
        self.chat_agent = None

    async def start_sender(self, websocket: WebSocket):
        """启动发送者任务"""
        queue = self.message_queues.get(websocket)
        if not queue:
            return

        while True:
            message = await queue.get()
            if websocket in self.active_connections:
                try:
                    if message == "ping":
                        await websocket.send_text("pong")
                    else:
                        await websocket.send_text(message)
                except:
                    break
            else:
                break

    async def connect(self, websocket: WebSocket):
        """连接WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queues[websocket] = asyncio.Queue()
        self.sender_tasks[websocket] = asyncio.create_task(
            self.start_sender(websocket))

    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.sender_tasks[websocket].cancel()
            await self.message_queues[websocket].put(None)
            del self.sender_tasks[websocket]
            del self.message_queues[websocket]

    async def start_streaming(self, task, report_type, report_source, source_urls, tone, websocket, headers=None):
        """开始流式传输输出"""
        tone = Tone[tone]
        # 在此处添加自定义的JSON配置文件路径
        config_path = "default"
        report = await run_agent(task, report_type, report_source, source_urls, tone, websocket, headers=headers, config_path=config_path)
        # 每次编写新报告时创建新的聊天代理
        self.chat_agent = ChatAgentWithMemory(report, config_path, headers)
        return report

    async def chat(self, message, websocket):
        """基于消息差异与代理聊天"""
        if self.chat_agent:
            await self.chat_agent.chat(message, websocket)
        else:
            await websocket.send_json({"type": "chat", "content": "知识库为空，请先运行研究以获取知识"})

async def run_agent(task, report_type, report_source, source_urls, tone: Tone, websocket, headers=None, config_path=""):
    """运行代理"""
    start_time = datetime.datetime.now()
    # 通过不同的报告类型类来运行代理，而不是直接运行代理
    if report_type == "multi_agents":
        report = await run_research_task(query=task, websocket=websocket, stream_output=stream_output, tone=tone, headers=headers)
        report = report.get("report", "")
    elif report_type == ReportType.DetailedReport.value:
        researcher = DetailedReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            tone=tone,
            config_path=config_path,
            websocket=websocket,
            headers=headers
        )
        report = await researcher.run()
    else:
        researcher = BasicReport(
            query=task,
            report_type=report_type,
            report_source=report_source,
            source_urls=source_urls,
            tone=tone,
            config_path=config_path,
            websocket=websocket,
            headers=headers
        )
        report = await researcher.run()

    # 测量时间
    end_time = datetime.datetime.now()
    await websocket.send_json(
        {"type": "logs", "output": f"\n总运行时间：{end_time - start_time}\n"}
    )

    return report