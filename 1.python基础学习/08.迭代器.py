'''Python 迭代器
迭代器是一种对象，该对象包含值的可计数数字。
迭代器是可迭代的对象，这意味着您可以遍历所有值。
从技术上讲，在 Python 中，迭代器是实现迭代器协议的对象，它包含方法 __iter__() 和 __next__()。
1.迭代器 VS 可迭代对象（Iterable）
列表、元组、字典和集合都是可迭代的对象。它们是可迭代的容器，您可以从中获取迭代器（Iterator）。
所有这些对象都有用于获取迭代器的 iter() 方法

2.遍历迭代器
我们也可以使用 for 循环遍历可迭代对象
for 循环实际上创建了一个迭代器对象，并为每个循环执行 next() 方法。

3.创建迭代器
要把对象/类创建为迭代器，必须为对象实现 __iter__() 和 __next__() 方法。
正如您在 Python 类/对象 一章中学到的，所有类都有名为 __init__() 的函数，它允许您在创建对象时进行一些初始化。
__iter__() 方法的作用相似，您可以执行操作（初始化等），但必须始终返回迭代器对象本身。
__next__() 方法也允许您执行操作，并且必须返回序列中的下一个项目。

4.StopIteration
如果你有足够的 next() 语句，或者在 for 循环中使用，则上面的例子将永远进行下去。
为了防止迭代永远进行，我们可以使用 StopIteration 语句。
在 __next__() 方法中，如果迭代完成指定的次数，我们可以添加一个终止条件来引发错误：
'''

#1.从元组返回一个迭代器，并打印每个值：
mytuple = ("apple", "banana", "cherry")
myit = iter(mytuple)

print(next(myit))
print(next(myit))
print(next(myit))
#甚至连字符串都是可迭代的对象，并且可以返回迭代器
mystr = "banana"
myit = iter(mystr)

print(next(myit))
print(next(myit))
print(next(myit))
print(next(myit))
print(next(myit))
print(next(myit))

#2.遍历迭代器,我们也可以使用 for 循环遍历可迭代对象
mytuple = ("apple", "banana", "cherry")

for x in mytuple:
  print(x)

#3.创建迭代器
#创建一个返回数字的迭代器，从 1 开始，每个序列将增加 1（返回 1、2、3、4、5 等）：
class MyNumbers:
  def __iter__(self):
    self.a = 1
    return self

  def __next__(self):
    x = self.a
    self.a += 1
    return x

myclass = MyNumbers()
myiter = iter(myclass)

print(next(myiter))
print(next(myiter))
print(next(myiter))
print(next(myiter))
print(next(myiter))

#4.停止迭代
class numbers:
  def __iter__(self):
    self.a = 1
    return self

  def __next__(self):
    if self.a <= 20:
      x = self.a
      self.a += 1
    else:
      raise StopIteration
    return x

dx = numbers()
ddq = iter(dx)

for x in ddq:
  print(x)

'''总结
迭代器就是构造一个类，必须包括iter函数和next函数。
且iter函数必须返回对象本身。next函数必须返回下一个项目。
使用raise StopIteration结束迭代。
'''


'''
1️⃣ 代码简化与最佳实践
复合赋值运算符（+=、-=）与普通赋值（= a + b）在等价条件下完全等价，推荐使用前者，更简洁易读。
编写条件判断时，推荐使用卫语句（Guard Clause）——先处理异常/边界情况并提前返回，让主逻辑保持在最外层、最扁平的位置，比嵌套if更清晰优雅。

2️⃣ 遍历中修改数据结构的坑 
Python禁止在遍历字典/集合时直接删除元素（RuntimeError），
因为它们底层基于哈希表，迭代器与数据强耦合，修改会导致哈希表重组、迭代器指针失效而崩溃。
列表虽然允许边遍历边删（不报错），但底层基于索引，删除后元素前移会导致迭代器跳过元素，同样有逻辑bug。
正确做法是：先收集要删除的键，循环外再删；或用字典推导式 {k:v for k,v in car.items() if v>0} 一步到位。

3️⃣ 哈希表与数据结构底层 
哈希表通过哈希函数把key直接映射到存储位置，实现 O(1) 查找，
Python 的 dict 和 set 底层都是哈希表（set相当于只存key不存value的dict）。
但"唯一性集合"不等于"哈希表"——有些语言的有序集合（如 Java TreeSet、C++ set）用的是红黑树，牺牲一点速度换取有序性。
Python选择用哈希表实现唯一性，追求最快查找速度，需要有序时再用 sorted() 手动排序。
'''