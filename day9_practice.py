#任务一
students = [
    {"id": 1, "name": "小明", "score": 85},
    {"id": 2, "name": "小红", "score": 92},
    {"id": 3, "name": "小刚", "score": 78}
]

from fastapi import FastAPI

app = FastAPI()

@app.get("/students/{student_id}")
def get_student(student_id:int):
    for student in students:
        if student["id"] == student_id:
            return student
    else:
        return {"error":"学生不存在"}

#任务二
@app.get("/search")
def get_search(keyword:str,limit:int = 5,sort:str = "asc"):
    return {
        "keyword":keyword,
        "limit":limit,
        "sort":sort
        }

#任务三
def add(a,b):
    return a+b
def sub(a,b):
    return a-b
def mul(a,b):
    return a*b
def div(a,b):
    return a/b
@app.get("/calc/{a}/{b}")
def get_calc(a:float,b:float,op:str="add"):
    if op == "add":
        return {"result":add(a,b)}
    elif op == "sub":
        return {"result":sub(a,b)}
    elif op == "mul":
        return {"result":mul(a,b)}
    elif op == "div":
        return {"result":div(a,b)}
    else:
        return {"输入有误"}

