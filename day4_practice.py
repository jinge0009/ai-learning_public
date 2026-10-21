for i in range(1,10):
    for j in range(1,10):
        x=i*j
        print(f"{i}*{j}={x}")
import random
answer=random.randint(1,100)
count=0
while True:
    count=count+1
    s=int(input("猜数字："))
    if s==answer:
        print(f"猜对了,你猜了{count}次")
        break
    if s<answer:
        print("小了")
    else:
        print("大了")
s=0
count=0
while True:
    score=input("输入分数")
    if score=="q":
        break
    s=s+int(score)
    count=count+1
print(f"输入了{count}个分数，平均分是{s/(count)}")