import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def ask(question: str, system: str) -> str:
    response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

def extract_info(text:str) -> dict:
    system = """从用户文本中提取信息,输出JSON:
{
"name":"姓名",
"age":"年龄",
"school":"毕业院校",
"major":"专业",
"experience_years":"经验年限",
"skills":"技能",
"email":"电子邮箱",
"expected_salary":"期望工资"
}
规则:
- 不存在的字段填null
- 只输出JSON,不要其他文字
- age和experience_years用数字
- skills用数组"""

    reply = ask(text,system)

    reply = reply.strip()
    if reply.startswith("```"):
        reply = reply.split("\n",1)[1].rsplit("```",1)[0]

    return json.loads(reply.strip())

result = extract_info("""我叫张三，25岁，毕业于清华大学计算机系。
有3年Python开发经验，熟悉FastAPI和Docker。
邮箱是zhangsan@example.com，期望薪资20k-30k。""")

print(result)
print(type(result))
print(result["name"], result["skills"])