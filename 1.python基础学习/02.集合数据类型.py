'''Python 集合（数组）
Python 编程语言中有四种集合数据类型：
列表（List）是一种有序和可更改的集合。允许重复的成员。
元组（Tuple）是一种有序且不可更改的集合。允许重复的成员。
集合（Set）是一个无序和无索引的集合。没有重复的成员。集合（Set）是可变的，但它的元素必须是不可变类型（即可哈希的类型，如整数、字符串、元组等）
词典（Dictionary）是一个无序，可变和有索引的集合。没有重复的成员。
'''

'''*
在 Python 中，列表、元组、字典、集合 这些内置容器，它们变量里的“值”本质上都是引用（指针）。
也就是说，它们并不直接存放数据本身（比如整数 1、字符串 "hello" 或另一个列表），而是存放指向实际数据对象的内存地址。
数组的每个索引位置：存放的就是“数据本身”，没有间接层。

1.哈希表（哈希表是通过哈希函数快速定位的数据结构）
哈希表通过哈希函数把key直接映射到存储位置，实现 O(1) 查找，
Python 的 dict 和 set 底层都是哈希表（set相当于只存key不存value的dict）。
但"唯一性集合"不等于"哈希表"——有些语言的有序集合（如 Java TreeSet、C++ set）用的是红黑树，牺牲一点速度换取有序性。
Python选择用哈希表实现唯一性，追求最快查找速度，需要有序时再用 sorted() 手动排序。
'''

'''*总结
1.需要顺序、允许重复、要修改（存储混合类型或动态增删 ）                  用 列表。
2.需要顺序、但内容绝不能变（比如做字典的键）                           用 元组。
3.需要根据一个“名字”快速找到“值”                                    用 字典。
4.需要去重或快速判断元素是否存在（不关心顺序）                         用 集合。
5.需要存储大量同类型数值且节省内存                                   用 array.array或 numpy.array 
6.需要高性能数值计算（如机器学习）                                   用 numpy.array。
'''


'''列表方法(Python 有一组可以在列表上使用的内建方法)
方法	    描述
append()	在列表的末尾添加一个元素
clear()	删除列表中的所有元素
copy()	返回列表的副本
count()	返回具有指定值的元素数量。
extend()	将列表元素（或任何可迭代的元素）添加到当前列表的末尾
index()	返回具有指定值的第一个元素的索引
insert()	在指定位置添加元素
pop()	删除指定位置的元素(删除指定的索引)
remove()	删除具有指定值的项目
reverse()	颠倒列表的顺序
sort()	对列表进行排序
'''


'''元组（Tuple）
元组是有序且不可更改的集合。在 Python 中，元组是用圆括号编写的。
1.更改元组值
创建元组后，您将无法更改其值。元组是不可变的，或者也称为恒定的。
但是有一种解决方法。您可以将元组转换为列表，更改列表，然后将列表转换回元组。
2.创建有一个项目的元组
如需创建仅包含一个项目的元组，您必须在该项目后添加一个逗号，否则 Python 无法将变量识别为元组。
3.删除项目(您无法删除元组中的项目)
元组是不可更改的，因此您无法从中删除项目，但您可以完全删除元组。del 关键字可以完全删除元组。
4.元组方法(Python 提供两个可以在元组上使用的内建方法)
方法	    描述
count()	返回元组中指定值出现的次数。
index()	在元组中搜索指定的值并返回它被找到的位置。
'''
#1.更改元组值
x = ("apple", "banana", "cherry")
y = list(x)
y[1] = "kiwi"
x = tuple(y)
print(x)

#2.创建有一个项目的元组
thistuple = ("apple",)
print(type(thistuple))
#不是元组
thistuple = ("apple")
print(type(thistuple))

#3.删除项目
thistuple = ("apple", "banana", "cherry")
del thistuple
print(thistuple) # 这会引发错误，因为元组已不存在。


"""集合（Set）(集合是无序和无索引的集合。在 Python 中，集合用花括号编写)
1.访问项目
您无法通过引用索引来访问 set 中的项目，因为 set 是无序的，项目没有索引。
但是您可以使用 for 循环遍历 set 项目，或者使用 in 关键字查询集合中是否存在指定值。
2.更改项目
集合一旦创建，您就无法更改项目，但是您可以添加新项目。
3.添加项目
要将一个项添加到集合，请使用 add() 方法。要向集合中添加多个项目，请使用 update() 方法。
4.删除项目
要删除集合中的项目，请使用 remove() 或 discard() 方法
5.合并两个集合(在 Python 中，有几种方法可以连接两个或多个集合)
您可以使用 union() 方法返回包含两个集合中所有项目的新集合，也可以使用 update() 方法将一个集合中的所有项目插入另一个集合中：
注意：union() 和 update() 都将排除任何重复项。
6.Set 方法(Python 拥有一套能够在集合（set）上使用的内建方法)。
方法	    描述
add()	向集合添加元素。
clear()	删除集合中的所有元素。
copy()	返回集合的副本。
difference()	返回包含两个或更多集合之间差异的集合。
difference_update()	删除此集合中也包含在另一个指定集合中的项目。
discard()	删除指定项目。
intersection()	返回为两个其他集合的交集的集合。
intersection_update()	删除此集合中不存在于其他指定集合中的项目。
isdisjoint()	返回两个集合是否有交集。
issubset()	返回另一个集合是否包含此集合。
issuperset()	返回此集合是否包含另一个集合。
pop()	从集合中删除一个元素。
remove()	删除指定元素。
symmetric_difference()	返回具有两组集合的对称差集的集合。
symmetric_difference_update()	插入此集合和另一个集合的对称差集。
union()	返回包含集合并集的集合。
update()	用此集合和其他集合的并集来更新集合。
"""
thisset = {"apple", "banana", "cherry"}
#3.添加项目
##使用 add() 方法向 set 添加项目
thisset.add("orange")
print(thisset)
##使用 update() 方法将多个项添加到集合中：
thisset.update(["orange", "mango", "grapes"])
print(thisset)
#4.删除项目
##使用 remove() 方法来删除 “banana”
##注意：如果要删除的项目不存在，则 remove() 将引发错误。
thisset.remove("banana")
print(thisset)
##使用 discard() 方法来删除 “banana”（把remove换成discard）
##注意：如果要删除的项目不存在，则 discard() 不会引发错误。
#5.合并两个集合
set1 = {"a", "b" , "c"}
set2 = {1, 2, 3}
##union() 方法返回一个新集合，其中包含两个集合中的所有项目：
set3 = set1.union(set2)
print(set3)
##update() 方法将 set2 中的项目插入 set1 中：
set1.update(set2)
print(set1)


'''字典（Dictionary）(字典是一个无序、可变和有索引的集合。在 Python 中，字典用花括号编写，拥有键和值)
1.访问项目
您可以通过在方括号内引用其键名来访问字典的项目
2.更改值
您可以通过引用其键名来更改特定项的值
3.遍历字典
您可以使用 for 循环遍历字典。
循环遍历字典时，返回值是字典的键，但也有返回值的方法
4.添加项目
通过使用新的索引键并为其赋值，可以将项目添加到字典中
5.删除项目
有几种方法可以从字典中删除项目
6.复制字典
您不能通过键入 dict2 = dict1 来复制字典，因为：dict2 只是对 dict1 的引用，而 dict1 中的更改也将自动在 dict2 中进行。
有一些方法可以进行复制，一种方法是使用内建的字典方法 copy()
7.嵌套字典
词典也可以包含许多词典，这被称为嵌套词典。
8.dict() 构造函数
也可以使用 dict() 构造函数创建新的字典
字典方法
9.Python 提供一组可以在字典上使用的内建方法。
方法	    描述
clear()	删除字典中的所有元素
copy()	返回字典的副本
fromkeys()	返回拥有指定键和值的字典
get()	返回指定键的值
items()	返回包含每个键值对的元组的列表
keys()	返回包含字典键的列表
pop()	删除拥有指定键的元素
popitem()	删除最后插入的键值对
setdefault()	返回指定键的值。如果该键不存在，则插入具有指定值的键。
update()	使用指定的键值对字典进行更新
values()	返回字典中所有值的列表
'''

thisdict =	{
  "brand": "Porsche",
  "model": "911",
  "year": 1963
}
print(thisdict)

#1.访问项目,还有一个名为 get() 的方法会给你相同的结果：
x = thisdict["model"]
x = thisdict.get("model")

#2.更改值
thisdict["year"] = 2019

#3.遍历字典
##a.逐个打印字典中的所有键名
for x in thisdict:
  print(x)

##b.逐个打印字典中的所有值：
for x in thisdict:
  print(thisdict[x])

##c.您还可以使用 values() 函数返回字典的值：
for x in thisdict.values():
  print(x)

##d.通过使用items()函数遍历键和值：
for x, y in thisdict.items():
  print(x, y)

#4.添加项目
thisdict["color"] = "red"
print(thisdict)

#5.删除项目
##a. pop() 方法删除具有指定键名的项
thisdict.pop("model")
print(thisdict)

##b. popitem() 方法删除最后插入的项目（在 3.7 之前的版本中，删除随机项目）：
thisdict.popitem()
print(thisdict)

##c. del 关键字删除具有指定键名的项目,也可以完全删除字典：
del thisdict["model"]
print(thisdict)
del thisdict
print(thisdict) #this 会导致错误，因为 "thisdict" 不再存在。

#6.复制字典
##使用 copy() 方法来复制字典
mydict = thisdict.copy()
print(mydict)
##制作副本的另一种方法是使用内建方法 dict()
mydict = dict(thisdict)
print(mydict)

#7.嵌套字典
myfamily = {
  "child1" : {
    "name" : "Phoebe Adele",
    "year" : 2002
  },
  "child2" : {
    "name" : "Jennifer Katharine",
    "year" : 1996
  },
  "child3" : {
    "name" : "Rory John",
    "year" : 1999
  }
}
##创建三个字典，然后创建一个包含其他三个字典的字典：
child1 = {
  "name" : "Phoebe Adele",
  "year" : 2002
}
child2 = {
  "name" : "Jennifer Katharine",
  "year" : 1996
}
child3 = {
  "name" : "Rory John",
  "year" : 1999
}

myfamily = {
  "child1" : child1,
  "child2" : child2,
  "child3" : child3
}
#8.dict() 构造函数
thisdict = dict(brand="Porsche", model="911", year=1963)
# 请注意，关键字不是字符串字面量
# 请注意，使用了等号而不是冒号来赋值
print(thisdict)
