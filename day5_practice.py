def is_even(num):
    return num%2==0
def max_of_three(a,b,c):
    if a>=b and a>=c:
        return a
    elif b>=c:
        return b
    else:
        return c
def get_grade(score):
    if score>=90:
        return"优秀"
    elif score>=80:
        return"良好"
    elif score>=70:
        return"中等"
    elif score>=60:
        return"及格"
    else:
        return"不及格" 