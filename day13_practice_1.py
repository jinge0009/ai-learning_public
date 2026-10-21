#任务一：计算器API
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Literal

app = FastAPI(title="计算器 API")

class CalcRequest(BaseModel):
    a: float
    b: float
    op: Literal["add", "sub", "mul", "div","pow","mod"] = "add"

class CalcResponse(BaseModel):
    a: float
    b: float
    op: str
    result: float

@app.post("/calc", response_model=CalcResponse)
def calculate(req: CalcRequest):
    if req.op == "add":
        result = req.a + req.b
    elif req.op == "sub":
        result = req.a - req.b
    elif req.op == "mul":
        result = req.a * req.b
    elif req.op == "div":
        if req.b == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="除数不能为0"
            )
        result = req.a / req.b
    elif req.op == "pow":
        result = req.a ** req.b
    elif req.op == "mod": 
        if req.b == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="除数不能为0"
            )
        result = req.a % req.b
    return {"a": req.a, "b": req.b, "op": req.op, "result": round(result, 2)}