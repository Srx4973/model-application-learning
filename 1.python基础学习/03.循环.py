'''Python 循环(Python 有两个原始的循环命令)
1.while 循环
如果使用 while 循环，只要条件为真，我们就可以执行一组语句。
如果使用 break 语句，即使 while 条件为真，我们也可以停止循环。
如果使用 continue 语句，我们可以停止当前的迭代，并继续下一个。
2.for 循环
for 循环用于迭代序列（即列表，元组，字典，集合或字符串）。
这与其他编程语言中的 for 关键字不太相似，而是更像其他面向对象编程语言中的迭代器方法。
通过使用 for 循环，我们可以为列表、元组、集合中的每个项目等执行一组语句
range() 函数
如需循环一组代码指定的次数，我们可以使用 range() 函数，
range() 函数返回一个数字序列，默认情况下从 0 开始，并递增 1（默认地），并以指定的数字结束。
range() 函数默认 0 为起始值，不过可以通过添加参数来指定起始值：range(3, 10)，这意味着值为 3 到 10（但不包括 10）
range() 函数默认将序列递增 1，但是可以通过添加第三个参数来指定增量值：range(2, 30, 3)
'''

#1.while循环（while 循环需要准备好相关的变量）
##a.break语句：在 i 等于 3 时退出循环
i = 1
while i < 7:
  print(i)
  if i == 3:
    break
  i += 1

##b.continue 语句：如果 i 等于 3，则继续下一个迭代：
i = 0
while i <5:
  i +=1
  if i == 3:
    continue
  print(i)

#2.for循环（for 循环不需要预先设置索引变量）
fruits = ["apple", "banana", "cherry"]
for x in fruits:
  print(x)
##a.循环遍历字符串(甚至连字符串都是可迭代的对象，它们包含一系列的字符)
###循环遍历单词 "banana" 中的字母：
for x in "banana":
  print(x)
##b.range()函数
for x in range(10):     #range(10) 不是 0 到 10 的值，而是值 0 到 9。
  print(x)
##range() 函数默认将序列递增 1，但是可以通过添加第三个参数来指定增量值
for x in range(3, 50, 6):
  print(x)
