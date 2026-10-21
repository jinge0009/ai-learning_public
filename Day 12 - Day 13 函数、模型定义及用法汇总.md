# Day 12 - Day 13 函数、模型定义及用法汇总

## 一、FastAPI 核心

| 名称 | 导入 | 定义 / 用法 | 说明 |
|------|------|------------|------|
| `FastAPI` | `from fastapi import FastAPI` | `app = FastAPI(title="...", version="...")` | 创建应用实例 |
| `@app.post` | — | `@app.post("/students", status_code=201, response_model=StudentOut)` | 创建资源 |
| `@app.get` | — | `@app.get("/students", response_model=list[StudentOut])` | 查询资源 |
| `@app.put` | — | `@app.put("/students/{id}", response_model=StudentOut)` | 更新资源 |
| `@app.delete` | — | `@app.delete("/students/{id}", status_code=204)` | 删除资源 |
| `HTTPException` | `from fastapi import HTTPException` | `raise HTTPException(status_code=404, detail="...")` | 抛出 HTTP 错误 |
| `status` | `from fastapi import status` | `status.HTTP_201_CREATED`、`status.HTTP_404_NOT_FOUND` | 状态码常量 |
| `UploadFile` | `from fastapi import UploadFile` | `file: UploadFile = File(...)` | 接收上传文件 |
| `File` | `from fastapi import File` | `File(...)` | 声明文件参数 |

## 二、Pydantic 模型

| 名称 | 导入 | 定义 / 用法 | 说明 |
|------|------|------------|------|
| `BaseModel` | `from pydantic import BaseModel` | `class Student(BaseModel): ...` | 模型基类 |
| `Field` | `from pydantic import Field` | `name: str = Field(..., min_length=1, max_length=20)` | 字段校验 |
| `model_dump()` | — | `student.model_dump()` | 模型转字典 |
| 模型继承 | — | `class StudentOut(Student): id: int` | 继承父类字段 |
| `response_model` | — | `@app.get(..., response_model=StudentOut)` | 控制返回结构 |

## 三、类型提示

| 名称 | 导入 | 定义 / 用法 | 说明 |
|------|------|------------|------|
| `Optional` | `from typing import Optional` | `min_score: Optional[float] = None` | 可选类型 |
| `Literal` | `from typing import Literal` | `op: Literal["add","sub","mul","div","pow","mod"] = "add"` | 限定字段值 |
| `list[...]` | — | `response_model=list[StudentOut]` | 列表类型 |

## 四、文件与路径

| 名称 | 导入 | 定义 / 用法 | 说明 |
|------|------|------------|------|
| `Path` | `from pathlib import Path` | `UPLOAD_DIR = Path("uploads")` | 路径对象 |
| `mkdir` | — | `UPLOAD_DIR.mkdir(exist_ok=True)` | 创建目录，已存在不报错 |
| `open` | — | `with open(file_path, "wb") as buffer:` | 二进制写模式打开 |
| `write` | — | `buffer.write(content)` | 写入字节 |
| `decode` | — | `content.decode("utf-8")` | 字节转字符串 |
| `stem` | — | `Path(file.filename).stem` | 文件名（不含后缀） |
| `suffix` | — | `Path(file.filename).suffix` | 文件后缀（含点） |

## 五、datetime

| 名称 | 导入 | 定义 / 用法 | 说明 |
|------|------|------------|------|
| `datetime` | `from datetime import datetime` | `datetime.now()` | 当前时间 |
| `strftime` | — | `datetime.now().strftime("%Y%m%d%H%M%S")` | 格式化时间戳 |

## 六、Python 内置函数 / 方法

| 名称 | 用法 | 说明 |
|------|------|------|
| `round` | `round(result, 2)` | 四舍五入保留两位 |
| `max` | `max((s["id"] for s in students), default=0)` | 最大值，空列表返回默认值 |
| `len` | `len(content)`、`len(text.splitlines())` | 长度 |
| `sum` | `sum(scores)` | 求和 |
| `split` | `text.split()` | 按任意空白切分 |
| `splitlines` | `text.splitlines()` | 按行切分，正确处理末尾换行 |
| `append` | `students.append(new_student)` | 列表末尾添加 |
| `pop` | `students.pop(i)` | 按索引删除 |
| `enumerate` | `for i, s in enumerate(students):` | 同时拿索引和值 |

## 七、自定义函数（Day 12 学生系统）

| 函数名 | 定义 | 用途 |
|--------|------|------|
| `find_student` | `def find_student(student_id: int):` | 按 id 查找学生，返回字典或 `None` |
| `next_id` | `def next_id(): return max((s["id"] for s in students), default=0) + 1` | 生成下一个 id |
| `create_student` | `@app.post("/students", status_code=201, response_model=StudentOut)` | 创建学生，重名返回 400 |
| `list_students` | `@app.get("/students", response_model=list[StudentOut])` | 列表 + `min_score` 筛选 |
| `get_stats` | `@app.get("/students/stats")` | 统计数量、平均分、最高分、最低分 |
| `get_student` | `@app.get("/students/{student_id}", response_model=StudentOut)` | 查询单个，404 处理 |
| `update_student` | `@app.put("/students/{student_id}", response_model=StudentOut)` | 更新，检查重名（排除自己） |
| `delete_student` | `@app.delete("/students/{student_id}", status_code=204)` | 删除，404 处理 |

## 八、自定义函数（Day 13 计算器 / 文件上传）

| 函数名 | 定义 | 用途 |
|--------|------|------|
| `calculate` | `@app.post("/calc", response_model=CalcResponse)` | 计算器，支持 add/sub/mul/div/pow/mod |
| `upload_file` | `@app.post("/upload") async def upload_file(file: UploadFile = File(...))` | 上传文件，类型/大小检查，时间戳重命名，保存 |
| `text_stats` | `@app.post("/text_stats") async def text_stats(file: UploadFile = File(...))` | 统计 txt 字符数、行数、词数 |

## 九、关键常量与变量

| 名称 | 定义 | 用途 |
|------|------|------|
| `students` | `students = []` | 内存中存储学生列表 |
| `UPLOAD_DIR` | `UPLOAD_DIR = Path("uploads")` | 上传文件保存目录 |
| `ALLOWED_TYPES` | `ALLOWED_TYPES = ["application/pdf", "text/plain"]` | 允许上传的 MIME 类型 |
| `MAX_SIZE` | `MAX_SIZE = 2 * 1024 * 1024` | 文件大小上限 2MB |
| `timestamp` | `datetime.now().strftime("%Y%m%d%H%M%S")` | 时间戳，用于重命名 |
| `new_name` | `f"{stem}_{timestamp}{suffix}"` | 重命名后的文件名 |