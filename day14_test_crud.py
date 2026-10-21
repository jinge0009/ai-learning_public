from fastapi.testclient import TestClient
from day12_crud import app, students

client = TestClient(app)

def setup_function():
    """每个测试函数运行前清空数据"""
    students.clear()

def test_create_student():
    response = client.post("/students", json={
        "name": "小明", "score": 85, "age": 18
    })
    assert response.status_code == 201
    assert response.json()["name"] == "小明"
    assert response.json()["id"] == 1

def test_create_duplicate_name():
    client.post("/students", json={"name": "小明", "score": 85, "age": 18})
    response = client.post("/students", json={"name": "小明", "score": 90, "age": 19})
    assert response.status_code == 400
    assert "已存在" in response.json()["detail"]

def test_create_invalid_score():
    response = client.post("/students", json={
        "name": "小红", "score": 150, "age": 18
    })
    assert response.status_code == 422

def test_list_students():
    client.post("/students", json={"name": "小明", "score": 85, "age": 18})
    client.post("/students", json={"name": "小红", "score": 92, "age": 19})

    response = client.get("/students")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_student():
    client.post("/students", json={"name": "小明", "score": 85, "age": 18})
    response = client.get("/students/1")
    assert response.status_code == 200
    assert response.json()["name"] == "小明"

def test_get_not_found():
    response = client.get("/students/999")
    assert response.status_code == 404

def test_update_student():
    client.post("/students", json={"name": "小明", "score": 85, "age": 18})
    response = client.put("/students/1", json={
        "name": "小明", "score": 90, "age": 19
    })
    assert response.status_code == 200
    assert response.json()["score"] == 90

def test_delete_student():
    client.post("/students", json={"name": "小明", "score": 85, "age": 18})
    response = client.delete("/students/1")
    assert response.status_code == 204

def test_delete_not_found():
    response = client.delete("/students/999")
    assert response.status_code == 404

def test_stats():
    client.post("/students", json={"name": "小明", "score": 80, "age": 18})
    client.post("/students", json={"name": "小红", "score": 90, "age": 19})
    response = client.get("/students/stats")
    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert response.json()["average_score"] == 85.0