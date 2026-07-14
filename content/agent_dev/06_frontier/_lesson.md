# 前沿主题（2026 Q2 版本）

## 这一节的特殊性

这节内容**会过时**——和前 5 节的 Git/调试/Spec 不一样。这里讲的是"现在 AI 圈正在火"的东西。

> ⚠️ **这一节内容版本：2026 Q2**。每季度看一眼是不是还在主流。

## 1. MCP（Model Context Protocol）

**Anthropic 2024 年底推的标准**——让 LLM 接外部工具的统一协议。

打个比方：以前每个工具都要 LLM 学一套调用方式，**MCP 是"USB-C 标准"**——所有工具长一样的接口。

```
LLM ←→ MCP server ←→ 你的工具（数据库 / 文件 / API）
```

写 MCP server 几十行 Python 就够。Claude Code 就是 MCP 的早期使用者。

## 2. Tool Use / Function Calling

LLM 不光会聊天，还能**主动调函数**。最常见做法：

```python
tools = [{
    "name": "get_weather",
    "description": "Get weather of a city",
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    tools=tools,
    messages=[{"role": "user", "content": "北京天气如何？"}]
)
# LLM 返回 tool_use block：要调用 get_weather(city="北京")
```

**关键**：函数描述用 **JSON Schema** 格式——这是行业标准。

## 3. 多 Agent 协作

一个 LLM 解决不了的复杂任务——**让多个 LLM 分工**。

三种常见模式：

| 模式 | 说明 |
|---|---|
| **Orchestrator + Workers** | 一个主 agent 拆任务派给多个子 agent（你这个学习系统就是这种）|
| **Pipeline / Sequential** | A 输出 → B 加工 → C 验证（流水线） |
| **Debate / Critic** | 一个写、一个挑刺、一个仲裁 |

Claude Code、AutoGen、CrewAI 都是这种思路的具体实现。

## 4. RAG（检索增强生成）

LLM 不知道你公司的内部数据怎么办？**先检索 + 再生成**：

```
用户问 → 把问题向量化 → 在向量库找最相似的文档 →
   把文档塞进 prompt → LLM 基于文档回答
```

三步：**embed → retrieve → generate**。

为啥重要：**降低 LLM 幻觉**——它有"参考资料"了。

PA 场景：把公司 HR 政策 / 历史员工调研做成知识库，AI 回答员工问题时去检索。

## 5. Prompt 进阶：Chain-of-Thought

让 LLM **先思考再回答**——只需要在 prompt 里加一句"让我们一步步思考"或者放几个"思考过程的例子"。

```
普通 prompt：23 × 47 是多少？
→ LLM 可能直接猜一个数（错）

CoT prompt：23 × 47 是多少？让我们一步步算。
→ LLM 输出：23 × 47 = 23 × 50 - 23 × 3 = 1150 - 69 = 1081 ✓
```

延伸：
- **Few-shot prompting**：给几个例子让 LLM 学格式
- **Self-consistency**：让 LLM 答 5 次，取多数
- **Tree of Thoughts**：让 LLM 探索多条思考路径

## 跟踪 AI 进展的 5 个信息源

| 来源 | 看什么 |
|---|---|
| **Anthropic Blog** | Claude / API 大版本更新 |
| **OpenAI Blog** | GPT 大版本 / 新能力 |
| **Hacker News** "AI" 标签 | 业界正在讨论的新工具 |
| **Simon Willison's blog** | 实战派博主，过滤虚假繁荣很准 |
| **Hugging Face Daily Papers** | 学术前沿 |

**别看**：营销号、"震惊体"、夸张测评。

## 自检清单（季度更新）

每个季度问自己：
1. 我用的 LLM 大版本变了吗？
2. 我常用的库（langchain / Anthropic SDK）API 变了吗？
3. 我没听过的新概念冒出来了吗？（如 2024 年的 MCP、2025 年的某个）
4. 这一节内容里有没有过时的？

## 现在做练习

5 道题：MCP 全称、function calling 描述格式、多 agent 模式名、RAG 三步、CoT 缩写。
