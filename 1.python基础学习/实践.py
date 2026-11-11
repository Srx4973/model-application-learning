#1.9*9乘法表
for i in range(1, 10):
    for j in range(1, 10):
        cheng = i * j
        # 使用格式化字符串确保对齐，每个数字占2位，不足两位前面补空格
        print(f"{i}*{j}={cheng:2d}", end=' ')  # :2d表示整数占2位，右对齐
        # end 的作用：决定 print() 输出结束后，在屏幕上追加什么字符（默认为换行符 \n）
    print()  # 每完成一行后换行

#2.构造字典
thisdict = dict(brand="Porsche", model="911", year=1963)
# 请注意，关键字不是字符串字面量
# 请注意，使用了等号而不是冒号来赋值
print(thisdict)

#3.continue和break
i = 0
while i < 5:
    i += 1
    if i == 3:
        continue
    print(i)

i = 1
while i < 7:
  print(i)
  if i == 3:
    break
  i += 1

#4.字典验证
a= {'a':'a','a':'b'}
b= {'a':'a','b':'a'}
print(type(a.values()) ,'\n' ,type(b.keys()))
c= 'ab'

#5.猜数字1-100
import random
b = random.randrange(1,101)
i = 1
while i < 6:
    try:
        a= int(input(f"第 {i} 次猜测："))
    except ValueError:
        print("❌ 无效输入，请输入一个整数。")
        i -= 1  # 无效输入不消耗次数
        continue
    i += 1
    if a == b:
        print('yes,good')
        break
    elif a < b:
        if i < 6:
            print('no,small')
    else:
        if i < 6:
            print('no,big')
else:
    print('no,you are loser')

#6.子，父类
class fu:
    def __init__(self,name,age):
        self.name = name
        self.age = age
        self.jieshao()

    def jieshao(self):
        print(f'大家好我是{self.name},今年{self.age}岁')

x = fu('baoluo',19)
print(x)

class zi(fu):
    def __init__(self,name,age,chushen):
        super().__init__(name,age)
        self.chushen = chushen
        self.chushendi()

    def chushendi(self):
        print(f'并且我出生于{self.chushen}')

y =  zi('rouse',20,'luoma')
print(y)


#7.迭代器
class numbers:
    def __iter__(self):
        self.a = 1
        return self
    def __next__(self):
        if self.a <= 20:
            x = self.a
            self.a += 1
            return x
        else:
            raise StopIteration
dx = numbers()
ddq = iter(dx)

for i in ddq:
    print(i)

#8.类多态
class Vehicle:
  def __init__(self, brand, model):
    self.brand = brand
    self.model = model

  def move(self):
    print("Move!")

class Car(Vehicle):
  pass

class Boat(Vehicle):
  def move(self):
    print("Sail!")

class Plane(Vehicle):
  def move(self):
    print("Fly!")

car1 = Car("Ford", "Mustang") # 创建 Car 对象
boat1 = Boat("Ibiza", "Touring 20") # 创建 Boat 对象
plane1 = Plane("Boeing", "747") # 创建 Plane 对象

for x in (car1, boat1, plane1):
  print(x.brand)
  print(x.model)
  x.move()

#9.文件处理
x = open('demo.text','w')
x.write('Hello!'
        'Welcome to demofile.txt,'
        'This file is for testing purposes.'
        'Good Luck!')
x.close()
x = open('demo.text')
print(x.read())


with open('demo.text') as f:
    for i in f:
        print(i)
