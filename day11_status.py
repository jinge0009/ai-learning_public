from fastapi import FastAPI, status
from pydantic import BaseModel

app = FastAPI()

class Student(BaseModel):
    name: str
    score: float

students = []

@app.post("/students", status_code=status.HTTP_201_CREATED)
def create_student(student: Student):
    students.append(student.model_dump())
    return {"message": "创建成功", "total": len(students)}

@app.delete("/students/{index}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(index: int):
    students.pop(index)