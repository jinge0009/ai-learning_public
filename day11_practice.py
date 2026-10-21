from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel,Field

app = FastAPI()

students = []

class Student(BaseModel):
    name:str = Field(...,min_length=1,max_length=20)
    score:float = Field(...,ge=0,le=100)
    age:int = Field(...,ge=0,le=150)

@app.post("/students",status_code=status.HTTP_201_CREATED)
def create_student(student:Student):
    for s in students:
        if s["name"] == student.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"学生 {student.name} 已存在"
            )
    new_student = student.model_dump()
    new_student["id"] = max((s["id"] for s in students),default=0)+1
    students.append(new_student)
    return {"message": "创建成功","total":len(students)}

@app.get("/students")
def list_student():
    return {"students":students,"total":len(students)}

@app.get("/students/{student_id}")
def get_student(student_id:int):
    if student_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生 ID 不能为负数"
        )
    for student in students:
        if student.get("id") == student_id:
            return student
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"学生 {student_id} 不存在"
        )
@app.delete("/students/{student_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id:int):
    for i,student in enumerate(students):
        if student["id"] == student_id:
            students.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"学生 {student_id} 不存在"
    )

