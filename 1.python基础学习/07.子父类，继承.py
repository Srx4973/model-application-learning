'''Python 继承
继承允许我们定义继承另一个类的所有方法和属性的类。
父类是继承的类，也称为基类。
子类是从另一个类继承的类，也称为派生类。
1.创建父类
任何类都可以是父类，因此语法与创建任何其他类相同

2.创建子类
要创建从其他类继承功能的类，请在创建子类时将父类作为参数发送

3.添加 __init__() 函数
到目前为止，我们已经创建了一个子类，它继承了父类的属性和方法。
我们想要把 __init__() 函数添加到子类（而不是 pass 关键字）。
当添加 __init__() 函数时，子类将不再继承父的 __init__() 函数。
注意：每次使用类创建新对象时，都会自动调用 __init__() 函数。

4.super() 函数
super() 函数，它会使子类从其父继承所有方法和属性。

5.添加属性和方法
a.在这例子中，2019 年应该是一个变量，并在创建 student 对象时传递到 Student 类。
为此，在 __init__() 函数中添加另一个参数
b.把名为 welcome 的方法添加到 子类Student中
'''

#2.创建子类:创建一个名为 Student 的类，它将从 Person 类继承属性和方法
class Student(Person):
  pass
#如果不想向该类添加任何其他属性或方法，使用 pass 关键字。
#现在，Student 类拥有与 Person 类相同的属性和方法。

#3.子类添加 __init__() 函数
# a.为 Student 类添加 __init__() 函数：
class Student(Person):
  def __init__(self, fname, lname):
          # 添加属性等
          pass #举例，暂时不用添加先pass
#注意：子的__init__()函数会覆盖对父的__init__()函数的继承。

#b.如需保持父的 __init__() 函数的继承，添加对父的 __init__() 函数的调用
class Student(Person):
  def __init__(self, fname, lname):
    Person.__init__(self, fname, lname)

#4.super() 函数，它会使子类从其父继承所有方法和属性
class Student(Person):
  def __init__(self, fname, lname):
    super().__init__(fname, lname)
#通过使用 super() 函数，不必使用父元素的名称，它将自动从其父元素继承方法和属性。

#5.添加属性和方法
#a.添加属性
class Student(Person):
  def __init__(self, fname, lname, year):
    super().__init__(fname, lname)
    self.graduationyear = year

x = Student("Elon", "Musk", 2019)

#b.添加方法
class Student(Person):
  def __init__(self, fname, lname, year):
    super().__init__(fname, lname)
    self.graduationyear = year

  def welcome(self):
    print("Welcome", self.firstname, self.lastname, "to the class of", self.graduationyear)
#如果在子类中添加一个与父类中的函数同名的方法，则将覆盖父方法的继承。

'''总结
子父类继承就是，创建子类时将父类作为参数发送。super()函数可以直接继承父类的所有方法和属性。
当方法和属性与父类冲突时。覆盖父类的方法属性。
'''