def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "除数不能为0"
    return a / b
def calculator():
    history=[]
    while True:
        print("\n1.加法 2.减法 3.乘法 4.除法 q.退出 h.查询历史")
        choice = input("请选择：")

        if choice == "q":
            print("再见")
            break

        if choice == "h":
            if history:
                for record in history:
                    print(record)
            else:
                print("暂无历史记录")
            continue

        if choice not in ["1", "2", "3", "4"]:
            print("无效选择")
            continue

        a = float(input("第一个数："))
        b = float(input("第二个数："))

        if choice == "1":
            print(f"结果：{add(a, b)}")
            history.append(f"{a}+{b}={add(a, b)}")
        elif choice == "2":
            print(f"结果：{subtract(a, b)}")
            history.append(f"{a}-{b}={subtract(a, b)}")
        elif choice == "3":
            print(f"结果：{multiply(a, b)}")
            history.append(f"{a}*{b}={multiply(a, b)}")
        elif choice == "4":
            print(f"结果：{divide(a, b)}")
            history.append(f"{a}/{b}={divide(a, b)}")
calculator()