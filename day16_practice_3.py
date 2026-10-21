import os
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

print(ask("""甲乙两人从相距100公里的两地同时出发相向而行，甲的速度是6公里/小时，乙的速度是4公里/小时，几小时后两人相遇？""", 
          system="""你是一个数学助手。解决问题时，先展示推理过程及步骤，再最后给答案。不要用LaTeX格式"""))