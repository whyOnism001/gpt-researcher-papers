from fastapi import WebSocket
from typing import Any

from gpt_researcher import GPTResearcher

# 定义一个基础报告类
class BasicReport:
    def __init__(
        self,
        query: str,
        report_type: str,
        report_source: str,
        source_urls,
        tone: Any,
        config_path: str,
        websocket: WebSocket,
        headers=None
    ):
        # 初始化查询、报告类型、报告来源、来源网址、语气、配置路径、WebSocket连接和头部信息
        self.query = query
        self.report_type = report_type
        self.report_source = report_source
        self.source_urls = source_urls
        self.tone = tone
        self.config_path = config_path
        self.websocket = websocket
        self.headers = headers or {}

    async def run(self):
        # 初始化研究者
        researcher = GPTResearcher(
            query=self.query,
            report_type=self.report_type,
            report_source=self.report_source,
            source_urls=self.source_urls,
            tone=self.tone,
            config_path=self.config_path,
            websocket=self.websocket,
            headers=self.headers
        )

        # 进行研究并生成报告
        await researcher.conduct_research()
        report = await researcher.write_report()
        return report