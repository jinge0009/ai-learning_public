import os,json,time
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel,Field,ValidationError
from typing import Optional

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)


class Resume(BaseModel):
    name: str
    gender: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None      # 学历
    school: Optional[str] = None
    major: Optional[str] = None
    experience_years: Optional[int] = None
    skills: list[str] = []
    expected_salary: Optional[str] = None

def extract_resume(text: str, max_retries: int = 3) -> Resume:
    system = """从简历文本中提取信息，输出JSON：
{
  "name": "姓名",
  "gender": "男",
  "age": 28,
  "education": "硕士",
  "school": "北京大学",
  "major": "计算机",
  "experience_years": 5,
  "skills": ["Python", "Django"],
  "expected_salary": "30-40k"
}
规则：
- 不存在字段填 null
- age、experience_years 填整数
- skills 填数组
- 只输出 JSON"""

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-flash",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return Resume(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"第 {attempt + 1} 次失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    raise Exception(f"重试 {max_retries} 次后仍失败")

resumes = [
    "张伟，男，28岁，北京大学计算机硕士，5年Python开发经验，熟悉Django和FastAPI，期望薪资30-40k。",
    "李娜，女，25岁，清华大学软件工程本科，3年Java开发经验，精通Spring Boot，期望薪资20-25k。",
    "王强，男，32岁，上海交大博士，8年AI算法经验，擅长PyTorch和TensorFlow，期望薪资50k+。"
]

results = []
for text in resumes:
    try:
        r = extract_resume(text)
        results.append(r)
        print(f"✓ {r.name} | {r.school} | {r.skills}")
    except Exception as e:
        print(f"✗ 失败: {e}")

print(f"\n成功 {len(results)} / {len(resumes)} 条")
for p in results:
    print(p.model_dump())

print("\n=== 任务3：字段缺失 ===")
r = extract_resume("我叫小明")
print(r)
print(r.model_dump())