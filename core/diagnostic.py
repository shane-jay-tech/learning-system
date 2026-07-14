"""首次诊断测试 — 5-8 道轻量题评估用户基础，推荐学习入口。

不依赖 AI（离线可用）。结果写入 meta 表。
"""
from typing import Dict, List, Optional
from core.progress import ProgressDAO

DIAGNOSTIC_QUESTIONS = [
    {
        "id": "d1_python_read",
        "question": "下面这段 Python 代码输出什么？\n```python\nx = 3\ny = x + 2\nprint(y)\n```",
        "options": ["3", "5", "x + 2", "报错"],
        "answer": 1,
        "skill": "python_basics",
    },
    {
        "id": "d2_loop",
        "question": "这段代码打印几次 'hi'？\n```python\nfor i in range(3):\n    print('hi')\n```",
        "options": ["1 次", "2 次", "3 次", "4 次"],
        "answer": 2,
        "skill": "python_basics",
    },
    {
        "id": "d3_sql",
        "question": "SQL 中 `SELECT name FROM users WHERE age > 18` 的作用是？",
        "options": [
            "删除 18 岁以上的用户",
            "查询 18 岁以上用户的名字",
            "插入一条新记录",
            "修改年龄字段",
        ],
        "answer": 1,
        "skill": "sql_basics",
    },
    {
        "id": "d4_dataframe",
        "question": "pandas 的 DataFrame 最像什么？",
        "options": ["一个数字", "一段文字", "一张 Excel 表格", "一张图片"],
        "answer": 2,
        "skill": "data_analysis",
    },
    {
        "id": "d5_function",
        "question": "Python 函数 `def add(a, b): return a + b` 调用 `add(2, 3)` 返回？",
        "options": ["23", "5", "ab", "报错"],
        "answer": 1,
        "skill": "python_basics",
    },
    {
        "id": "d6_git",
        "question": "`git commit` 的作用是？",
        "options": [
            "下载代码到本地",
            "保存当前修改到版本历史",
            "把代码推送到远程",
            "删除最近的修改",
        ],
        "answer": 1,
        "skill": "agent_basics",
    },
]

RECOMMENDATIONS = {
    "zero_base": {
        "path": "agent_mastery",
        "milestone": "a0",
        "message": "建议从「编程预备」开始，打好 Python 基础再进入其他内容。",
    },
    "has_python": {
        "path": "agent_mastery",
        "milestone": "a1",
        "message": "你有 Python 基础！建议直接进入「Agent 指挥主线」学 Git + 读代码。",
    },
    "data_oriented": {
        "path": "people_analytics",
        "milestone": "m1",
        "message": "你对数据分析有概念！建议走「People Analytics」路径。",
    },
    "all_good": {
        "path": "agent_mastery",
        "milestone": "a2",
        "message": "基础扎实！建议直接从「读懂代码」开始 Agent 路径。",
    },
}


def evaluate_diagnostic(answers: Dict[str, int]) -> Dict:
    """评估诊断结果，返回推荐。answers: {question_id: selected_option_index}"""
    skills = {"python_basics": 0, "sql_basics": 0, "data_analysis": 0, "agent_basics": 0}
    total_correct = 0

    for q in DIAGNOSTIC_QUESTIONS:
        user_answer = answers.get(q["id"])
        if user_answer == q["answer"]:
            total_correct += 1
            skills[q["skill"]] += 1

    if total_correct <= 1:
        rec_key = "zero_base"
    elif skills["python_basics"] >= 2 and total_correct >= 4:
        rec_key = "all_good"
    elif skills["data_analysis"] >= 1 and skills["sql_basics"] >= 1:
        rec_key = "data_oriented"
    elif skills["python_basics"] >= 2:
        rec_key = "has_python"
    else:
        rec_key = "zero_base"

    return {
        "total_correct": total_correct,
        "total_questions": len(DIAGNOSTIC_QUESTIONS),
        "skills": skills,
        "recommendation_key": rec_key,
        "recommendation": RECOMMENDATIONS[rec_key],
    }


def save_diagnostic_result(dao: ProgressDAO, result: Dict) -> None:
    """保存诊断结果到 meta 表。"""
    import json
    dao.set_meta("diagnostic_result", json.dumps(result, ensure_ascii=False))
    dao.set_meta("diagnostic_recommendation", result["recommendation_key"])


def get_diagnostic_result(dao: ProgressDAO) -> Optional[Dict]:
    """读取已保存的诊断结果。"""
    import json
    raw = dao.get_meta("diagnostic_result")
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None
