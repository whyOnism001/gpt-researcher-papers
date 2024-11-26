from typing import TypedDict, List, Annotated
import operator

# 定义一个类型为TypedDict的DraftState，用于指定草稿状态的结构
class DraftState(TypedDict):
    # 任务相关的信息，以字典形式存储
    task: dict
    # 主题，以字符串形式表示
    topic: str
    # 草稿内容，以字典形式存储
    draft: dict
    # 评审意见，以字符串形式表示
    review: str
    # 修订笔记，以字符串形式表示
    revision_notes: str