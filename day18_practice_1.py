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

class Product(BaseModel):
    name: str                                     # 商品名
    original_price: float                         # 原价
    current_price: float                          # 现价
    discount: Optional[float] = None              # 折扣金额
    screen_size: float                            # 屏幕尺寸
    chip: str                                     # 芯片
    supports_5g: bool                             # 是否支持5G
    battery_hours: int                            # 续航小时
    returnable: bool                              # 是否可退货

def extract_with_retry(text: str, max_retries: int = 3) -> Product:
    system = """从用户文本中提取商品信息，输出JSON：
{
  "name": "商品名",
  "original_price": 0.0,
  "current_price": 0.0,
  "discount": 0.0,
  "screen_size": 0.0,
  "chip": "芯片型号",
  "supports_5g": true,
  "battery_hours": 0,
  "returnable": true
}
规则：
- 不存在字段填 null
- 价格、尺寸字段只填数字，去掉"元"、"英寸"等单位
- supports_5g、returnable 填 true 或 false
- battery_hours 填整数
- 只输出 JSON，不要其他文字"""
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-flash",
                messages=[
                    {"role": "system", "content":system},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            data = json.loads(raw)
            return Product(**data)

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"第 {attempt + 1} 次失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)    # 等一下再重试

    raise Exception(f"重试 {max_retries} 次后仍失败")

text = """
iPhone 15 Pro Max 256GB 原色钛金属，
原价9999元，现在活动价8999元，直降1000元。
屏幕6.7英寸，A17 Pro芯片，支持5G，电池续航29小时。
库存充足，支持7天无理由退货。
"""
product = extract_with_retry(text)
print(product)
print(f"商品: {product.name}")
print(f"原价: {product.original_price} 现价: {product.current_price}")
print(f"折扣: {product.discount} 屏幕: {product.screen_size}英寸")