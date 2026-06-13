'''3. 链表结构
顾名思义，链表是一种节点相互链接的列表。每个节点包含数据和一个指针。
它们链接的方式是，每个节点指向下一个节点在内存中的位置。
*a. 链表与数组的比较
比较维度	                             数组	                                                链表
内存	                  连续内存块，长度固定。若设定内存为7，只传入3个，则剩余4个浪费。         由分散的内存块构成，每块包含数据和指向下一块的指针，
                      数组满时需申请更大的内存块并复制原有内容，时间开销大。	               用几块申请几块，不会造成内存浪费。
查找元素时间复杂度	      O(1)，连续内存，可通过索引直接定位。	                           O(n)，必须从头遍历到第 n 个。
插入/删除成本
- 开头插入	          整个数组元素后移，O(n)。	                                       将新元素指针指向原第一个元素地址. O(1)
- 结尾插入	          数组未满时 O(1)；满时需创建更大数组并复制，O(n)。	               需从头遍历到最后一个元素. O(n)
- 中间插入	          O(n)，第 n个及之后元素索引都需更新。	                           需先遍历到第 n 个元素，再插入。O(n)
使用/实现	          容易实现。	                                                   容易出现内存分段和泄漏。

b. 链表的类型
#单向链表
单向链表是最简单的链表类型。它在内存中占用的空间更少，因为每个节点只有一个指向下一个节点的地址，如下图所示
[ data | next ] --> [ data | next ] --> [ data | next ] --> [ data | next ] - - > null

#双向链表
双向链表的节点同时包含指向前一个节点和后一个节点的地址，如下图所示，因此占用的内存更多。但双向链表的好处是，可以在列表中双向移动。
null ⇄ [prev|data|next] ⇄ [prev|data|next] ⇄ [prev|data|next] ⇄ null

#循环链表
循环链表类似于单向或双向链表，但第一个节点（“头”）和最后一个节点（“尾”）是相连的。
在单向或双向链表中，只需检查链接是否为 null，即可找到列表的开始和结束。
但对于循环链表，在某些应用中需要更复杂的代码来显式检查起始和结束节点。
循环链表适用于需要连续循环遍历的列表。
##单向循环链表： [data1|next] → [data2|next] → [data3|next] → [data4|next]
                 ↑___________________________________________________┘
##双向循环链表：
 ┌────────────────────────────────────────────────────────────────────┐
 │                                                                    ↓
[prev|data1|next] ⇄ [prev|data2|next] ⇄ [prev|data3|next] ⇄ [prev|data4|next]
       ↑                                                                   │
       └───────────────────────────────────────────────────────────────────┘
'''

#3. 链表
#a. 单向链表
class linklist:
    def __init__(self,data):
        self.node = data
        self.next = None
#遍历单向链表
def traveral(head):
    tmp = head
    while tmp:
        print(tmp.node, end=" -> ")
        tmp = tmp.next
    print('null')

'''
迭代和递归有什么区别：
迭代就是单向推进，递归就是先一层一层递下去，然后再回头一层一层归回来

递归的三个条件
1.大问题可以拆成两个子问题。
2.子问题求解方式和大问题一样。
3.存在最小值子问题。
'''

#递归反转链表
def digui(head):
    if not head or not head.next:           # 先判断 head
        return head                         #如果链表是空或者只有一个节点，直接返回为头节点
    p = digui(head.next)                     #递归调用，设置p因为递归到最后一次会执行上面的if，返回一个新头节点
    head.next.next = head                    #让此节点的下一个节点反过来指向此节点
    head.next = None                        #本节点指向空
    return p                                 #返回新头节点

#迭代反转链表
def reverse(head):
    pre = None                     #设置前节点
    curr = head                    #创建指针
    while curr:
        next_node = curr.next      #提前储存下一个节点
        curr.next = pre            #让下一个节点指向前节点
        pre  = curr                #更新前节点为本节点
        curr = next_node           #更新为下一个节点
    return pre

head = linklist(1)
head.next = linklist(2)
head.next.next = linklist(3)
traveral(head)

#迭代反转链表验证
head = reverse(head)
traveral(head)

#递归反转链表验证
head = digui(head)
traveral(head)

#b. 双向链表
class doublelinklist:
    def __init__(self,data):
        self.node = data
        self.pre = None
        self.next = None

#插入元素
def insert(head,node,data):
    new_node = doublelinklist(data)         #构造新节点
    tmp = head
    while tmp:
        if tmp.node == node:                #找到插入位置
            new_node.next = tmp.next
            new_node.pre = tmp
            if tmp.next:                    #不是尾节点，执行下面两句
                tmp.next.pre = new_node
            tmp.next = new_node             #如果是尾节点，只用执行这一句，让tmp指向新节点
            return                          #因为只能让新节点指向null，不能让null指向新节点
        tmp = tmp.next
    print('null')

#删除元素
def shan(head,data):
    tmp = head
    while tmp:
        if tmp.node == data:              #找到元素
            if tmp.pre:                   #如果不是头节点
                tmp.pre.next = tmp.next   #让上一个节点跳过本节点连接到下一个节点
            else:                         #如果是头节点
                head = tmp.next           #设置头节点为下一个节点
            if tmp.next:                  #如果不是尾节点
                tmp.next.pre = tmp.pre    #让下一个节点跳过本节点连接到上一个节点
        tmp = tmp.next                    #循环
    return  head                          #如果删除的是头节点，返回一个新头

#遍历双向链表
def doubletraveral(head):
    tmp = head
    while tmp:
        print(tmp.node, end=" <-> ")
        tmp = tmp.next
    print('null')

head1 = doublelinklist(2)
head1.next = doublelinklist(3)
head1.next.pre = head1
head1.next.next = doublelinklist(4)
head1.next.next.pre = head1.next

insert(head1,3,5)

head1 = shan(head1,2)

doubletraveral(head1)


'''以后在写或调用链表函数时，注意一个问题：

“这个操作会不会改变链表的头节点？”

1.如果会（比如删除头节点） -> 这个函数必须 return 新的头指针，
并且在调用它时必须用 head = func(head) 的形式来接收并更新头指针。

2.如果不会（比如在中间插入、遍历、修改节点值） -> 这个函数不需要 return，
调用它时直接写 func(head) 即可，不要赋值。
'''