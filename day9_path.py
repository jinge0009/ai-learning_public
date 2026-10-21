from fastapi import FastAPI

app = FastAPI()

@app.get("/students/{student_id}/courses")
def get_courses(student_id: int, semester: str = "2025春"):
    return {
        "student_id": student_id,
        "semester": semester,
        "courses": ["Python", "FastAPI", "AI基础"]
    }