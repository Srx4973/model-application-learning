'''Python 类/对象
Python 是一种面向对象的编程语言。
Python 中的几乎所有东西都是对象，拥有属性和方法。
类（Class）类似对象构造函数，或者是用于创建对象的“蓝图”。
1.创建类
如需创建类，请使用 class 关键字
使用名为 x 的属性，创建一个名为 MyClass 的类
class MyClass:
  x = 5

2.创建对象
现在我们可以使用名为 myClass 的类来创建对象：
创建一个名为 p1 的对象，并打印 x 的值
p1 = MyClass()
print(p1.x)

3.__init__() 函数
上面的例子是最简单形式的类和对象，在实际应用程序中并不真正有用。
要理解类的含义，我们必须先了解内置的 __init__() 函数。
**所有类都有一个名为 __init__() 的函数，它始终在启动类时执行。
使用 __init__() 函数将值赋给对象属性，或者在创建对象时需要执行的其他操作

4.对象方法
对象也可以包含方法。对象中的方法是属于该对象的函数。
让我们在 Person 类中创建方法：

5.self 参数（self 的作用就是：让方法知道自己操作的是哪个对象）
self 参数是对类的当前实例的引用，用于访问属于该类的变量。
它不必被命名为 self，您可以随意调用它，但它必须是类中任意函数的首个参数：
'''

#3.创建名为 Person 的类，使用 __init__() 函数为 name 和 age 赋值：
class Person:
  def __init__(self, name, age):
    self.name = name # self.name → 这个对象的 name 属性
    self.age = age# self.age → 这个对象的 age 属性

p1 = Person("Bill", 63)

print(p1.name)
print(p1.age)
#每次使用类创建新对象时，都会自动调用 __init__() 函数。

#4.对象方法：插入一个打印问候语的函数，并在 p1 对象上执行它：
class Person:
  def __init__(self, name, age):
    self.name = name # self.name → 这个对象的 name 属性
    self.age = age # self.age → 这个对象的 age 属性

  def myfunc(self):
    print("Hello my name is " + self.name) # 通过 self 访问这个对象的属性

p1 = Person("Bill", 63)
p1.myfunc()
#self 参数是对类的当前实例的引用，用于访问属于该类的变量。

#5.self 参数名字可变，__init__函数自动执行对象方法实现
class Person:
    def __init__(mysillyobject, name, age):
        mysillyobject.name = name
        mysillyobject.age = age
        mysillyobject.myfunc()  # 创建对象时自动执行！

    def myfunc(abc):
        print("Hello my name is " + abc.name)

p1 = Person("Bill", 63)
# 自动打印：Hello my name is Bill

#6.修改删除对象的属性，或者删除对象。
#把 p1 的年龄改为 40
p1.age = 40
#删除 p1 对象的 name属性
del p1.name
#删除对象 p1
del p1

'''总结
总的来说就是将类赋给p1，创造名为p1的对象。再用自启动也就是__init__() 函数，
来构造这个对象的属性。也可如例5：用self.method自动执行对象的方法。'''