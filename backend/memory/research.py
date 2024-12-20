from typing import TypedDict, List, Annotated
import operator

# 定义一个类型为TypedDict的ResearchState，用于指定研究状态的结构
class ResearchState(TypedDict):
    # 任务相关的信息，以字典形式存储
    task: dict
    # 初始研究内容，以字符串形式表示
    initial_research: str
    # 报告的各个部分，以字符串列表形式表示
    sections: List[str]
    # 研究数据，以字典列表形式存储
    research_data: List[dict]
    # 报告布局
    # 报告的标题，以字符串形式表示
    title: str
    # 报告的头部信息，以字典形式存储
    headers: dict
    # 报告的日期，以字符串形式表示
    date: str
    # 报告的目录，以字符串形式表示
    table_of_contents: str
    # 报告的引言部分，以字符串形式表示
    introduction: str
    # 报告的结论部分，以字符串形式表示
    conclusion: str
    # 报告的来源列表，以字符串列表形式表示
    sources: List[str]
    # 完整的报告内容，以字符串形式表示
    report: str