# AI 学习记录

## 简介
Python + AI 应用开发自学记录，目标：6个月达到初级 AI 应用工程师求职水平。

## 学习进度

### 第1周：Python 基础
- Day 1: 环境搭建
- Day 2: 数据类型与输入输出
- Day 3: 条件判断 if
- Day 4: 循环 for/while
- Day 5: 函数 def
- Day 6: 列表和字典
- Day 7: 综合练习

### 第2周：FastAPI 后端开发
- Day 8: FastAPI 入门
- Day 9: 路径参数与查询参数
- Day 10: POST 请求与 Pydantic
- Day 11: 状态码与错误处理
- Day 12: 完整 CRUD API
- Day 13: 计算器 API 与文件上传
- Day 14: 测试基础与项目整理

## 项目

| 文件 | 内容 |
|------|------|
| day12_crud.py | 学生管理系统 REST API（CRUD + 统计 + 筛选） |
| day13_practice.py | 计算器 API + 文件上传 + 文本统计 |
| day14_test_crud.py | 学生系统自动化测试（10 个测试） |

## 运行

```bash
uvicorn day12_crud:app --reload   # 启动学生系统 API
pytest day14_test_crud.py -v      # 运行测试