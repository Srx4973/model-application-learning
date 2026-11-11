'''Python 文件处理
文件处理是任何 Web 应用程序的重要组成部分。
Python 有几个用于创建、读取、更新和删除文件的函数。
1.文件处理
在 Python 中使用文件的关键函数是 open() 函数。open() 函数有两个参数：文件名和模式。

有四种打开文件的不同方法（模式）：
"r" - 读取 - 默认值。打开文件进行读取，如果文件不存在则报错。
"a" - 追加 - 打开供追加的文件，如果不存在则创建该文件。
"w" - 写入 - 打开文件进行写入，如果文件不存在则创建该文件。
"x" - 创建 - 创建指定的文件，如果文件存在则返回错误。

此外，您可以指定文件是应该作为二进制还是文本模式进行处理。
"t" - 文本 - 默认值。文本模式。
"b" - 二进制 - 二进制模式（例如图像）。

2.文件读取
a.如需打开文件，请使用内建的 open() 函数。
open() 函数返回文件对象，此对象有一个 read() 方法用于读取文件的内容

b.读行
您可以使用 readline() 方法返回一行

c.关闭文件
完成后始终关闭文件是一个好习惯。

3.Python 文件写入
a.如需写入已有的文件，必须向 open() 函数添加参数
"a" - 追加 - 会追加到文件的末尾
"w" - 写入 - 会覆盖任何已有的内容

b.如需在 Python 中创建新文件，请使用 open() 方法，并使用以下参数之一：
"x" - 创建 - 将创建一个文件，如果文件存在则返回错误
"a" - 追加 - 如果指定的文件不存在，将创建一个文件
"w" - 写入 - 如果指定的文件不存在，将创建一个文件

4.Python 删除文件
如需删除文件，必须导入 OS 模块，并运行其 os.remove() 函数：
如需删除整个文件夹，请使用 os.rmdir() 方法(只能删除空文件夹。)
'''
# 最优写法，写完自动关
with open('demo.txt', 'a') as x:
    x.write('Hello')
# 自动关闭，不用你写 close()

# 读完自动关
with open('demo.txt', 'r') as x:
    print(x.read())
#  自动关闭


# 1.文件处理
#您可以指定文件是应该作为二进制还是文本模式进行处理：
f = open("demofile.txt")

#以上代码等同于下面,因为 "r" (读取)和 "t" (文本)是默认值，所以不需要指定它们。
f = open("demofile.txt", "rt")

# 2.文件读取
## a.方法read()
f = open("demofile.txt", "r")
print(f.read())

##只读取文件的一部分，返回文件中的前五个字符：
f = open("demofile.txt", "r")
print(f.read(5))

## b.读行,读取文件中的一行
f = open("demofile.txt", "r")
print(f.readline())

##文件对象本身就是可迭代的，默认按行遍历
f = open("demofile.txt", "r")
for x in f:      #  这里没有用readline()，但默认就是按行
    print(x)

## c.完成后关闭文件(在某些情况下，由于缓冲，您应该始终关闭文件，在关闭文件之前，对文件所做的更改可能不会显示)
f = open("demofile.txt", "r")
print(f.readline())
f.close()

# 3.文件写入
## a.写入已有的文件
# 打开文件 "demofile.txt" 并将内容追加到文件中：
f = open("demofile.txt", "a")
f.write("Now the file has more content!")
f.close()

## 追加后，打开并读取该文件：
f = open("demofile2.txt", "r")
print(f.read())

##如果使用"w" 方法会覆盖全部内容。

## b.创建新文件
##创建名为 "myfile.txt" 的文件：
f = open("myfile.txt", "x")#已创建新的空文件

##如果不存在，则创建新文件：
f = open("myfile.txt", "w")

#4.文件删除
#删除文件 "demofile.txt"：
import os
os.remove("demofile.txt")

#检查文件是否存在，为避免出现错误，需要在尝试删除文件之前检查该文件是否存在
import os
if os.path.exists("demofile.txt"):
  os.remove("demofile.txt")
else:
  print("The file does not exist")

#如需删除整个文件夹，请使用 os.rmdir() 方法
#删除文件夹 "myfolder"
import os
os.rmdir("myfolder")