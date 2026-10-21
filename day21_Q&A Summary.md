# **大模型基础**
## messages 里的三种角色分别是什么？
system:系统/全局指令；user:用户输入；assistant：助手回复
## 为什么模型不记得上一句话？
未上传历史，每次对话都是独立调用模型
## Token 是什么？输入和输出都算吗？
词元，模型处理文本的最小单位；输入和输出都算
# **Prompt 工程**
## System Prompt 的作用是什么？
设定模型身份、约束行为、控制输出格式
## Few-Shot 是什么？
给几个输入输出示例，让模型照着学，稳定输出格式
## 思维链（CoT）怎么触发？
在 system 里写"一步步思考"、"先展示推理过程"
# **结构化输出**
## response_format={"type": "json_object"} 的作用？
强制输出json格式
## 为什么用 Pydantic 校验模型输出？
校验字段类型和范围，不合法就报错
## 模型偶尔返回错误 JSON，怎么处理？
重试 + 间隔 + 最多 N 次
# **流式输出**
## stream=True 后怎么取内容？
for chunk in stream 循环，取 delta.content
## chunk.choices[0].delta.content 和 message.content 有什么区别？
delta 是增量，message 是完整内容
# **Function Calling**
## tools 里 description 为什么重要？
模型靠它判断什么时候用工具
## tool_call_id 是干什么的？
让工具执行的结果能够准确对应回请求执行的哪个工具调用
## 工具调用为什么需要两轮请求？
第一轮调用是为了让模型决定用什么工具，第二轮调用是根据工具所产生结果生成最终回答
# **多轮对话**
## 怎么让模型记住上下文？
每一次调用都把完整历史上传模型
## 历史太长怎么处理？
历史截断或历史摘要