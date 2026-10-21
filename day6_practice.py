#任务一
nums=[]
for i in range(1,11):
    nums.append(i)
print(nums)
print(len(nums))
for n in nums:
    if n%2==0:
        print(n)
#任务二
text=input("请输入一句话：")
words=text.split()
count={}
for word in words:
    if word in count:
        count[word]+=1
    else:
        count[word]=1
print(count)