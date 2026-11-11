'''
数值类型：	int, float, complex
序列类型：	list, tuple, range
映射类型：	dict
集合类型：	set, frozenset
布尔类型：	bool
二进制类型：	bytes, bytearray, memoryview
'''

'''type,types,dpyte
名称	     类别	              作用范围	                               举例
type	内置函数	            Python 所有对象	                      type(5) is int
types	标准库模块	        提供特定类型常量（函数、方法、生成器等）	  import types; isinstance(f, types.FunctionType)
dtype	属性（NumPy/Pandas）	描述数组中元素的存储格式	              arr.dtype = int64
'''

#type()函数获取任何对象的数据类型：
a='sdsd'
print(type(a))
#设定特定的数据类型，就用数据类型():
b = float(10)
print(b,type(b))
#Python 中有三种数字类型：int；float；complex(复数)无法将复数转换为其他数字类型。
c = 2j
try:
    int(c)
except TypeError as e:
    print(f"❌ 转换为整数失败: {e}")
print(type(c))
#Python 没有 random() 函数来创建随机数，但 Python 有一个名为 random 的内置模块，可用于生成随机数：
import random
print(random.randrange(450))

'''字符串是数组
像许多其他流行的编程语言一样，Python 中的字符串是表示 unicode 字符的字节数组。
但是，Python 没有字符数据类型，单个字符就是长度为 1 的字符串。
方括号可用于访问字符串的元素。
'''

b = " Hello, World! "
print(b[2:5])
print(b[-5:-2])
print(len(b))
#strip() 方法删除开头和结尾的空白字符：
print(b.strip())

'''在Python中，方法（Method）和内置函数（Built-in Function）的区别源于语言设计哲学和面向对象编程思想。
| 特性       | 方法（如 a.strip()）   | 内置函数（如 len(a)）   |
|-----------|-----------------------|----------------------|
| 所属关系   | 属于特定对象（如字符串）   | 属于全局命名空间        |
| 调用方式   | 对象.方法()             | 函数(对象)            |
| 功能范围   | 仅作用于特定对象类型      | 可作用于多种对象类型     |
| 扩展性     | 可通过继承/组合扩展       | 通常不直接扩展          |
1.面向对象原则
字符串的strip()、upper()等方法直接封装在字符串对象中
符合"数据与操作该数据的方法绑定"的OOP思想
2.通用工具函数
len()、type()、print()等作为全局工具函数
可作用于多种类型（字符串、列表、字典等）
'''

#lower() 返回小写的字符串：
print(b.lower())
#upper() 方法返回大写的字符串：
print(b.upper())
#replace() 用另一段字符串来替换字符串：
print(b.replace("World", "Kitty"))
#split() 方法在找到分隔符的实例时将字符串拆分为子字符串：
print(b.split(",")) # returns ['Hello', ' World!']

'''
1.检查字符串
如需检查字符串中是否存在特定短语或字符，我们可以使用 in 或 not in 关键字。
2.字符串级联（串联）
如需串联或组合两个字符串，您可以使用 + 运算符。
3.字符串格式
正如在 Python 变量一章中所学到的，我们不能直接用 + 组合字符串和数字：
但是我们可以使用 format() 方法组合字符串和数字！
format() 方法接受传递的参数，格式化它们，并将它们放在占位符 {} 所在的字符串中：
'''

age = 63
txt = "My name is Bill, and I am {}"
print(txt.format(age))
#可以使用索引号 {0} 来确保参数被放在正确的占位符中：
quantity = 3
itemno = 567
price = 49.95
myorder = "I want to pay {2} dollars for {0} pieces of item {1}."
print(myorder.format(quantity, itemno, price))

'''字符串方法(Python 有一组可以在字符串上使用的内建方法)
注意：所有字符串方法都返回新值。它们不会更改原始字符串。
方法	   描述
capitalize()	把首字符转换为大写。
casefold()	把字符串转换为小写。
center()	返回居中的字符串。
count()	返回指定值在字符串中出现的次数。
encode()	返回字符串的编码版本。
endswith()	如果字符串以指定值结尾，则返回 true。
expandtabs()	设置字符串的 tab 尺寸。
find()	在字符串中搜索指定的值并返回它被找到的位置。
format()	格式化字符串中的指定值。
format_map()	格式化字符串中的指定值。
index()	在字符串中搜索指定的值并返回它被找到的位置。
isalnum()	如果字符串中的所有字符都是字母数字，则返回 True。
isalpha()	如果字符串中的所有字符都在字母表中，则返回 True。
isdecimal()	如果字符串中的所有字符都是小数，则返回 True。
isdigit()	如果字符串中的所有字符都是数字，则返回 True。
isidentifier()	如果字符串是标识符，则返回 True。
islower()	如果字符串中的所有字符都是小写，则返回 True。
isnumeric()	如果字符串中的所有字符都是数，则返回 True。
isprintable()	如果字符串中的所有字符都是可打印的，则返回 True。
isspace()	如果字符串中的所有字符都是空白字符，则返回 True。
istitle()	如果字符串遵循标题规则，则返回 True。
isupper()	如果字符串中的所有字符都是大写，则返回 True。
join()	把可迭代对象的元素连接到字符串的末尾。
ljust()	返回字符串的左对齐版本。
lower()	把字符串转换为小写。
lstrip()	返回字符串的左修剪版本。
maketrans()	返回在转换中使用的转换表。
partition()	返回元组，其中的字符串被分为三部分。
replace()	返回字符串，其中指定的值被替换为指定的值。
rfind()	在字符串中搜索指定的值，并返回它被找到的最后位置。
rindex()	在字符串中搜索指定的值，并返回它被找到的最后位置。
rjust()	返回字符串的右对齐版本。
rpartition()	返回元组，其中字符串分为三部分。
rsplit()	在指定的分隔符处拆分字符串，并返回列表。
rstrip()	返回字符串的右边修剪版本。
split()	在指定的分隔符处拆分字符串，并返回列表。
splitlines()	在换行符处拆分字符串并返回列表。
startswith()	如果以指定值开头的字符串，则返回 true。
strip()	返回字符串的剪裁版本。
swapcase()	切换大小写，小写成为大写，反之亦然。
title()	把每个单词的首字符转换为大写。
translate()	返回被转换的字符串。
upper()	把字符串转换为大写。
zfill()	在字符串的开头填充指定数量的 0 值。
'''


'''
1.布尔值
在编程中，通常需要知道表达式是True还是False。可以计算Python中的任何表达式，并获得两个答案之一，即True或False。
比较两个值时，将对表达式求值，Python返回布尔值答案：
2.评估值和变量
bool()函数可让您评估任何值，并为您返回True或False。大多数值都为 True
3.如果有某种内容，则几乎所有值都将评估为 True。
除空字符串外，任何字符串均为 True。
除 0 外，任何数字均为 True。
除空列表外，任何列表、元组、集合和字典均为 True。
4.某些值为 False
实际上，除空值（例如 ()、[]、{}、""、数字 0 和值 None）外，没有多少值会被评估为 False。当然，值 False 的计算结果为 False。
5.函数可返回布尔
Python 还有很多返回布尔值的内置函数，例如 isinstance() 函数，该函数可用于确定对象是否具有某种数据类型：
'''
