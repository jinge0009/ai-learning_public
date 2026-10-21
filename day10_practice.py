#任务一
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Student(BaseModel):
    name: str
    score: float
    age: int

students = []

@app.post("/students")
def create_student(student:Student):
    students.append(student.model_dump())
    return {"message": "创建成功","total":len(students)}

#任务二
@app.get("/students")
def list_students():
    return{"students":students,"total":len(students)}

