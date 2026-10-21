from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="学生管理系统 API", version="1.0")

# ========== 数据模型 ==========
class Student(BaseModel):
    name: str = Field(..., min_length=1, max_length=20)
    score: float = Field(..., ge=0, le=100)
    age: int = Field(..., ge=0, le=150)

class StudentOut(Student):
    id: int

# ========== 内存数据 ==========
students = []

# ========== 工具函数 ==========
def find_student(student_id: int):
    for s in students:
        if s["id"] == student_id:
            return s
    return None

def next_id():
    return max((s["id"] for s in students), default=0) + 1

# ========== CREATE ==========
@app.post("/students", status_code=status.HTTP_201_CREATED, response_model=StudentOut)
def create_student(student: Student):
    for s in students:
        if s["name"] == student.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"学生 {student.name} 已存在"
            )
    new_student = student.model_dump()
    new_student["id"] = next_id()
    students.append(new_student)
    return new_student

# ========== READ ALL ==========
@app.get("/students", response_model=list[StudentOut])
def list_students(min_score:Optional[float] = None):
    if min_score is not None:
        return [s for s in students if s["score"] >= min_score]
    return students

# ========== STATS ==========
@app.get("/students/stats")
def get_stats():
    if not students:
        return {"count": 0, "average_score": None, "max_score": None, "min_score": None}
    scores = [s["score"] for s in students]
    return {
        "count": len(students),
        "average_score": sum(scores) / len(scores),
        "max_score": max(scores),
        "min_score": min(scores)
    }

# ========== READ ONE ==========
@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int):
    if student_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生 ID 不能为负数"
        )
    student = find_student(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"学生 {student_id} 不存在"
        )
    return student

# ========== UPDATE ==========
@app.put("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, student: Student):
    existing = find_student(student_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"学生 {student_id} 不存在"
        )
    for s in students:
        if s["name"] == student.name and s["id"] != student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"学生 {student.name} 已存在"
            )
    existing["name"] = student.name
    existing["score"] = student.score
    existing["age"] = student.age
    return existing

# ========== DELETE ==========
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int):
    for i, s in enumerate(students):
        if s["id"] == student_id:
            students.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"学生 {student_id} 不存在"
    )
