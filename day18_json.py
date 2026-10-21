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

class Person(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)
    city: Optional[str] = None
    skills: list[str] = []

def extract_with_retry(text: str, max_retries: int = 3) -> Person:
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-flash",
                messages=[
                    {"role": "system", "content": """从用户文本中提取信息，输出JSON：
{
  "name": "姓名",
  "age": 0,
  "city": "城市",
  "skills": ["技能1", "技能2"]
}
不存在的字段填 null，age 用整数。"""},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)
            return Person(**data)

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"第 {attempt + 1} 次失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)    # 等一下再重试

    raise Exception(f"重试 {max_retries} 次后仍失败")

texts = [
    "我叫张三，25岁，住在上海，会Java和Spring。",
    "我是李四，30岁，来自广州，精通Python和Docker。",
    "王五，28岁，深圳，擅长Go和Kubernetes。"
]

results = []
for text in texts:
    try:
        person = extract_with_retry(text)
        results.append(person)
        print(f"✓ {person.name}")
    except Exception as e:
        print(f"✗ 失败: {text[:20]}... 原因: {e}")

print(f"\n成功 {len(results)} / {len(texts)} 条")
for p in results:
    print(p.model_dump())