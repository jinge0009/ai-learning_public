from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message":"欢迎"}

@app.get("/about")
def read_about():
    return {"name":"Jin Ge","goal":"AI应用工程师"}

@app.get("/time")
def read_time():
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"time":now}