from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()

class Student(BaseModel):
    name: str
    score: float

students = []

@app.post("/students", status_code=201)
def create_student(student: Student):
    students.append(student.model_dump())
    return {"message": "创建成功", "total": len(students)}

@app.get("/students")
def list_students():
    return {"students": students, "total": len(students)}

# ========== 测试 ==========
client = TestClient(app)

def test_create_student():
    response = client.post("/students", json={"name": "小明", "score": 85})
    assert response.status_code == 201
    assert response.json()["total"] == 1

def test_list_students():
    response = client.get("/students")
    assert response.status_code == 200
    assert "students" in response.json()