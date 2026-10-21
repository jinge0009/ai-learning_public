def add_student(students):
    name=input("请输入姓名：")
    score=float(input("请输入成绩："))
    students.append({"name":name,"score":score})

def show_all(students):
    if students:
        for student in students:
            print(f"姓名：{student['name']} 成绩：{student['score']}")
    else:
        print("暂无记录")

def find_student(students):
    name=input("请输入要查询的姓名：")
    for student in students:
        if student['name']==name:
            print(f"姓名：{student['name']} 成绩：{student['score']}")
            break
    else:
        print("未找到该学生") 

def delete_student(students):
    name=input("请输入要删除的姓名：")
    for student in students:
        if student['name']==name:
            students.remove(student)
            print(f"已删除【{name}】的记录")
            break
    else:
        print("未找到该学生")

def show_stats(students):
    count=len(students)
    if count==0:
        print("暂无记录，无法统计")
    else:
        scores=0
        max_score=0
        max_student=[]
        for student in students:
            scores+=student['score']
        average_score=scores/count
        for student in students:
            if student['score']>max_score:
                max_score=student['score']
                max_student=[student['name']]
            elif student['score']==max_score:
                max_student.append(student['name'])
        print(f"平均分：{average_score:.1f}\n最高分：{max_score}\n获得最高分的同学：{','.join(max_student)}")

def main():
    students=[]
    while True:
        print("\n1.添加 2.查看全部 3.查询 4.删除 5.统计 q.退出")
        choice = input("请选择：")

        if choice == "q":
            print("再见")
            break
        elif choice == "1":
            add_student(students)
        elif choice == "2":
            show_all(students)
        elif choice == "3":
            find_student(students)
        elif choice == "4":
            delete_student(students)
        elif choice == "5":
            show_stats(students)
        else:
            print("无效选择")


main()