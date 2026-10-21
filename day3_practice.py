score=float(input("请输入分数："))
if score>=90:
    print("优秀")
elif score>=80 and score<90:
    print("良好")
elif score>=70 and score<80:
    print("中等")
elif score>=60 and score<70:
    print("及格")
else:
    print("不及格")
num=int(input("请输入一个整数："))
if num%2==0:
    print("偶数")
else:
    print("奇数")
year=int(input("请输入年份："))
if year%4==0 and year%100!=0 or year%400==0:
    print("是闰年")
else:
    print("不是闰年") 