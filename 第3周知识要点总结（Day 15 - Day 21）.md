# 第3周知识要点总结（Day 15 - Day 21）

## 一、大模型 API 基础

### 1.1 调用大模型

| 概念 | 说明 |
|------|------|
| SDK | `openai` 官方 SDK，兼容绝大多数平台 |
| `base_url` | 指向不同平台，切换模型只改这个 |
| `api_key` | 存 `.env`，用 `python-dotenv` 读取 |
| `model` | 模型名称，如 `deepseek/deepseek-flash` |

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

response = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=[...]
)
```

### 1.2 messages 结构

| 角色 | 作用 |
|------|------|
| `system` | 设定模型身份、行为、约束 |
| `user` | 用户输入 |
| `assistant` | 模型之前的回复 |

```python
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你的？"}
]
```

### 1.3 核心特性

| 特性 | 说明 |
|------|------|
| 无状态 | 模型不记忆，每次调用独立 |
| Token | 计费单位，输入和输出都算 |
| 上下文 | 多轮对话靠传完整 `messages` |

## 二、Prompt 工程

### 2.1 System Prompt

设定模型身份、任务、约束、输出格式。

```python
system = """你是一个代码审查助手。
任务：检查用户提交的Python代码。
输出：
1. 潜在bug
2. 性能问题
3. 代码风格
每次回答不超过100字。"""
```

### 2.2 Few-Shot

给几个示例，让模型照着学，稳定输出格式。

```python
system = """把用户输入的情感分类。
示例：
输入：这家餐厅的菜太好吃了
输出：正面
输入：服务态度很差
输出：负面
只输出分类结果。"""
```

### 2.3 思维链（Chain of Thought）

让模型一步步推理，提升准确率。

```python
system = "你是一个数学助手。先展示推理过程，最后给出答案。"
```

### 2.4 结构化输出

| 技巧 | 用途 |
|------|------|
| `response_format={"type": "json_object"}` | 强制合法 JSON |
| system 里写 JSON 模板 | 告诉模型字段和类型 |
| 容错解析 | 去掉 markdown 包裹 |

```python
response = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=[...],
    response_format={"type": "json_object"}
)
```

**注意**：system 里必须提到 "JSON"，否则 API 报错。

## 三、流式输出

### 3.1 基础用法

```python
stream = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=[...],
    stream=True
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

### 3.2 关键点

| 要点 | 说明 |
|------|------|
| `stream=True` | 开启流式 |
| `chunk.choices[0].delta.content` | 取出增量文本 |
| `if content:` | 过滤 None |
| `end=""` + `flush=True` | 实时连续显示 |
| `full_reply += content` | 拼出完整文本 |
| `stream_options={"include_usage": True}` | 拿 Token 统计 |

### 3.3 delta vs message

| | 流式 | 非流式 |
|---|------|--------|
| 取内容 | `delta.content` | `message.content` |
| 返回方式 | 逐块返回 | 一次性返回 |

## 四、JSON 结构化输出

### 4.1 强制 JSON

```python
response_format={"type": "json_object"}
```

### 4.2 Pydantic 校验

```python
from pydantic import BaseModel
from typing import Optional

class Person(BaseModel):
    name: str
    age: Optional[int] = None
    city: Optional[str] = None
    skills: list[str] = []

# 校验
data = json.loads(response.choices[0].message.content)
person = Person(**data)
```

### 4.3 重试机制

```python
for attempt in range(max_retries):
    try:
        # 调用 + 解析 + 校验
        return Person(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        if attempt < max_retries - 1:
            time.sleep(1)
```

### 4.4 关键要点

| 要点 | 说明 |
|------|------|
| `Optional[X] = None` | 可选字段，缺字段不崩 |
| `model_dump()` | Pydantic 转字典 |
| system 模板与 Pydantic 字段名一致 | 避免解析失败 |
| `try/except + 重试` | 处理模型偶发错误 |

## 五、Function Calling

### 5.1 定义工具

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]
```

### 5.2 两轮请求流程

```text
用户提问
    ↓
第一轮：模型决定调用哪个工具
    ↓
执行工具函数
    ↓
第二轮：把工具结果发给模型，生成最终回答
```

### 5.3 关键代码

```python
# 第一轮
response = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
message = response.choices[0].message
messages.append(message)

# 执行工具
for tool_call in message.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    result = execute_tool(name, args)
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": result
    })

# 第二轮
final = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=messages,
    tools=tools
)
```

### 5.4 关键要点

| 要点 | 说明 |
|------|------|
| `description` | 模型靠它判断何时调用 |
| `tool_call.function.name` | 要调用的函数名 |
| `tool_call.function.arguments` | JSON 字符串参数 |
| `role: "tool"` | 工具执行结果消息 |
| `tool_call_id` | 关联请求和结果 |
| `while True` 循环 | 支持多工具连续调用 |

## 六、多轮对话管理

### 6.1 维护历史

```python
messages = [{"role": "system", "content": "..."}]

while True:
    user_input = input("你: ")
    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=messages
    )
    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
```

### 6.2 历史截断

```python
def trim_messages(messages, max_turns=10):
    if len(messages) <= 1:
        return messages
    system = messages[0]
    rest = messages[1:]
    user_indices = [
        i for i, m in enumerate(rest)
        if isinstance(m, dict) and m.get("role") == "user"
    ]
    if len(user_indices) <= max_turns:
        return [system] + rest
    start = user_indices[-max_turns]
    return [system] + rest[start:]
```

**原则**：以 `user` 消息为界截断，保留完整的对话轮结构。

### 6.3 关键要点

| 要点 | 说明 |
|------|------|
| 多轮实现 | 每次传完整 `messages` |
| 追加历史 | user 和 assistant 都加 |
| 历史截断 | 保留 system + 最近 N 轮 |
| 历史摘要 | 旧对话压缩成一段话 |
| 截断时机 | 只在对话边界做，不在中间做 |

## 七、第3周核心技能汇总

| 技能 | 用途 |
|------|------|
| 大模型调用 | OpenAI SDK + messages |
| Prompt 工程 | system/few-shot/CoT/JSON |
| 流式输出 | `stream=True` + delta |
| 结构化输出 | `response_format` + Pydantic |
| Function Calling | tools + tool_call_id + 两轮请求 |
| 多轮对话 | 维护 messages + 截断 |

## 八、常用代码片段

### 8.1 基础调用函数

```python
def ask(question: str, system: str = "你是一个助手") -> str:
    response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content
```

### 8.2 流式调用函数

```python
def ask_stream(question: str, system: str = "你是一个助手") -> str:
    stream = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ],
        stream=True
    )
    full = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            c = chunk.choices[0].delta.content
            print(c, end="", flush=True)
            full += c
    print()
    return full
```

### 8.3 JSON 提取函数

```python
def extract_json(text: str, system: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-flash",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            if attempt < max_retries - 1:
                time.sleep(1)
    raise Exception("重试失败")
```

## 九、环境依赖

### requirements.txt

```text
openai
python-dotenv
fastapi
uvicorn
pydantic
pytest
httpx
```

### 安装

```bash
pip install -r requirements.txt
```

### .env

```text
TOKENHUB_API_KEY=你的key
```

### .gitignore

```text
.env
__pycache__/
*.pyc
.pytest_cache/
uploads/
```

## 十、面试高频问题

| 问题 | 答题要点 |
|------|---------|
| 怎么让模型记住上下文？ | 维护 messages，每次传完整历史；过长时截断或摘要 |
| Function Calling 原理？ | 模型返回工具名和参数，程序执行，结果回传生成回答 |
| 怎么保证 JSON 输出稳定？ | `response_format` + Pydantic 校验 + 重试 |
| 流式输出有什么用？ | 降低首字延迟，提升用户体验 |
| Prompt 工程核心？ | 明确身份、任务、约束、输出格式 |
| 历史太长怎么办？ | 截断（保留最近N轮）或摘要（压缩旧对话） |