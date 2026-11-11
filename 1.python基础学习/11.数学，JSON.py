'''
一.Python 数学
Python 拥有一组内置的数学函数，包括一个广泛的数学模块，允许你对数字执行数学任务。
1.内置数学函数
.min() 和 max() 函数可用于查找可迭代对象中的最低或最高值.
b.abs() 函数返回指定数字的绝对（正）值
c.pow(x, y) 函数返回 x 的 y 次幂（xy）的值

2.数学模块
Python 还有一个内置模块叫做 math，它扩展了数学函数的列表。要使用它，你必须导入 math 模块

二.Python JSON
JSON 是用于存储和交换数据的语法。
JSON 是用 JavaScript 对象表示法（JavaScript object notation）编写的文本。
1.Python 中的 JSON
Python 有一个名为 json 的内置包，可用于处理 JSON 数据。

2.解析 JSON - 把 JSON 转换为 Python
若有 JSON 字符串，则可以使用 json.loads() 方法对其进行解析。结果将是 Python 字典。

3.把 Python 转换为 JSON
若有 Python 对象，则可以使用 json.dumps() 方法将其转换为 JSON 字符串。

4.格式化结果
上面的实例打印一个 JSON 字符串，但它不是很容易阅读，没有缩进和换行。
json.dumps() 方法提供了令结果更易读的参数
a.使用 indent 参数定义缩进数

b.还可以定义分隔符，默认值为（", ", ": "），这意味着使用逗号和空格分隔每个对象，
使用冒号和空格将键与值分开,使用 separators 参数来更改默认分隔符

c.使用 sort_keys 参数来指定是否应对结果进行排序

'''

# 一.Python 数学
## 2.导入 math 模块
import math
### a.math.sqrt() 方法返回一个数字的平方根
x = math.sqrt(64)
print(x)

### b.math.ceil() 方法将一个数字向上舍入到最近的整数，
### 而 math.floor() 方法将一个数字向下舍入到最近的整数，并返回结果
x = math.ceil(1.4)
y = math.floor(1.4)
print(x)  # 返回 2
print(y)  # 返回 1

### c.math.pi 常量返回 PI 的值（3.14...）
x = math.pi
print(x)

# 二.python JSON
##1.导入 json 模块：
import json

## 2.把 JSON 转换为 Python
x =  '{ "name":"Bill", "age":63, "city":"Seatle"}'
# 解析 x:
y = json.loads(x)

# 结果是 Python 字典：
print(y["age"])

## 3.把 Python 转换为 JSON
# Python 对象（字典）：
x = {
  "name": "Bill",
  "age": 63,
  "city": "Seatle"
}
# 转换为 JSON：
y = json.dumps(x)

# 结果是 JSON 字符串：
print(y)

'''
当 Python 转换为 JSON 时，Python 对象会被转换为 JSON（JavaScript）等效项：
Python	      JSON
dict	     Object
list	     Array
tuple	     Array
str	         String
int          Number
float	     Number
True	     true
False	     false
None	     null

'''
## 转换包含所有合法数据类型的 Python 对象
x = {
  "name": "Bill",
  "age": 63,
  "married": True,
  "divorced": False,
  "children": ("Jennifer","Rory","Phoebe"),
  "pets": None,
  "cars": [
    {"model": "Porsche", "mpg": 38.2},
    {"model": "BMW M5", "mpg": 26.9}
  ]
}

print(json.dumps(x))

## 4.格式化结果
### a.使用四个缩进使结果更易读
json.dumps(x, indent=4)

### b.使用 . 和空格分隔对象，并用空格、= 和空格分隔键与值：
json.dumps(x, indent=4, separators=(". ", " = "))

### c.按键名字母顺序排序结果
json.dumps(x, indent=4, sort_keys=True)