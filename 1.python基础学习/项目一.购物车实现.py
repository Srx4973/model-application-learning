#购物车
# 商品库存字典

'''
知识点1
类还没完全建好，装饰器没法正常工作，指的是：类体里的代码在定义阶段执行，
它还不是一个能直接使用的装饰器（因为它在类还没创建完成时，不能作为独立的对象被调用）
此时实例方法只是原始函数，无法像已经绑定好的方法那样被直接调用。因此用实例方法作为装饰器去装饰类中的其他方法会报错。
把它移到类外，让它成为一个独立函数，它在类定义时已经存在且可以正常工作了。

知识点2
 zeng、shan、gai 都是实例方法，第一个参数一定是 self。装饰器里的 wrapper 用 *args, **kwargs 能抓到它们，
 但这样 self 就藏在 args[0] 里，不够清晰。标准做法是直接写明 self。

'''

# 装饰器独立出来，方便复用
def shopping_log(func):
    """装饰器：操作前显示库存/购物车，操作后再次显示"""
    def wrapper(self,*args, **kwargs):
        print(f'您的购物车以及库存详情如下')
        self.show()

        print(f'执行操作{func.__name__}')
        result = func(self,*args, **kwargs)

        print(f'操作 {func.__name__} 完成，当前状态：')
        self.show()
        return result
    return wrapper

class shopping_cart:
    def __init__(self,products,cart):
        self.products = products
        self.cart = cart
        self.main()
    #查
    def show(self):
        print("-------当前库存-------")
        products_show = {name:numbers for name,numbers in self.products.items() if numbers >0}
        for name,numbers in products_show.items():
            print(f'商品：{name}，库存：{numbers}个')
    
        print("\n-------您的购物车-------")
        if not self.cart:
            print('您的购物车是空的，快去选购商品吧')
        else:
            for name, numbers in self.cart.items():
                print(f'商品：{name}，数量：{numbers}个')


    #增
    @shopping_log
    def zeng(self):
        shangpin = input('请输入您要的商品：').strip().lower()
        if shangpin in self.products:
            a = input("请输入您要的数量：")
            try:
                a = int(a)  # 转换为整数
                if a <= 0:
                    print("数量必须是正整数！")
                else:
                    if self.products[shangpin]>= a:
                        self.products[shangpin] -= a
                        self.cart[shangpin] = self.cart.get(shangpin, 0) + a #如果 cart 中有 shangpin 这个键，就返回它的值；如果没有，就返回 0。
                    elif self.products[shangpin] == 0:
                        print('当前商品库存不足，如有会及时通知您')
                    else:
                        print(f'不好意思商品库存只有{products[shangpin]}个，已经全加到您的购物车了')
                        self.cart[shangpin] = self.cart.get(shangpin, 0) + self.products[shangpin]
                        self.products[shangpin] = 0
            except ValueError:
                print("请输入有效的数字!")
        else:
            print('您的输入有误请重新输入')

    #删
    @shopping_log
    def shan(self):
        if not self.cart:
            print('您的购物车是空的，快去选购商品吧')
            return
        s_products = input('请选择您要删除的商品：').strip().lower()
        if s_products in self.cart:
            n_products = input('请输入您要删除的数量：')
            try:
                n_products = int(n_products)
                if n_products <= 0:
                    print('请输入一个正整数！')
                else:
                    if self.cart[s_products] >= n_products:
                        self.cart[s_products] -=  n_products
                        self.products[s_products] += n_products
                        if self.cart[s_products] == 0:
                            del self.cart[s_products]
                    else:
                        print(f'您购物车里只有{self.cart[s_products]}个，已经帮您全部删除了')
                        self.products[s_products] += self.cart[s_products]
                        del self.cart[s_products]
            except ValueError:
                print('请输入有效的数字!')
        else:
            print('您的输入有误请重新输入')

    #改
    @shopping_log
    def gai(self):
        if not self.cart:
            print('您的购物车是空的，快去选购商品吧')
            return
        name = input('请输入您要修改的商品：')
        if name in self.cart:
            numbers = input('您要修改数量为：')
            try:
                numbers = int(numbers)
                if numbers < 0:
                    print('请输入一个非负整数！')
                else:
                    if self.cart[name] >= numbers:
                        buyao = self.cart[name] - numbers
                        self.products[name] = self.products.get(name,0) + buyao
                        self.cart[name] = numbers
                        if self.cart[name] == 0:
                            del self.cart[name]
                    else:
                        haiyao = numbers - self.cart[name]
                        if haiyao > self.products[name]:
                            if self.products[name] != 0:
                                print(f'库存里只有{self.products[name]}个，已全部放入购物车，您现有 {self.cart[name] + self.products[name]} 个。')
                                self.cart[name] += self.products[name]
                                self.products[name] = 0
                            else:
                                print('当前商品库存不足，如有会及时通知您')
                        else:
                            self.cart[name] += haiyao
                            self.products[name] -= haiyao
            except ValueError:
                print('您的输入有误，请重新输入')
        else:
            print('您的输入有误请重新输入')

    #主函数
    def main(self):
        while True:
            print('\n-------购物车系统--------')
            print('查看购物车商品请输入：1')
            print('增加购物车商品请输入：2')
            print('删除购物车商品请输入：3')
            print('修改购物车商品请输入：4')
            print('退出请输入：0')
            choice = input('请输入要进行的操作:')
            try:
                choice = int(choice)
                if choice == 1:
                    self.show()
                elif choice == 2:
                    self.zeng()
                elif choice == 3:
                    self.shan()
                elif choice == 4:
                    self.gai()
                elif choice == 0:
                    print('感谢使用，欢迎下次再来')
                    break
                else:
                    print('您的输入有误请重新输入')
            except ValueError:
                print('您的输入有误请重新输入')
#实现
products = {
    'apple': 5,
    'banana': 3,
    'orange': 8,
    'pear': 2
}

cart = {}

shopping_cart(products,cart)



'''购物车系统核心知识点笔记
一、可变对象的引用传递
- Python 字典是可变对象，函数接收的是同一对象的引用（地址），不是副本。
- 通过引用修改内容（如 `car['apple'] = 5`）会直接影响全局对象。
- 重新赋值（如 `car = {'banana': 1}`）会在函数内创建新的局部变量，不会改变全局变量。

二、show() 中的过滤为何无效
- 在 show() 内部用推导式创建新字典只产生临时局部变量，函数结束后销毁，全局数据未被修改。
- 过滤只为“展示时好看”，并非真正的数据清理。真正的清理必须在增删改函数中完成。

三、空购物车判断失效的原因
- 使用 `if not cart:` 判断时，若字典中有值为 0 的键（如 `{'apple': 0}`），字典非空，导致误判购物车不为空。
- 解决方法：当商品数量变为 0 时，立即用 `del cart[key]` 删除键，确保字典为空时判断可靠。

四、del 与赋值为 0 的区别
- 赋值为 0：键保留，`in` 判断为 True，内存中残留无效数据（僵尸数据）。
- del 删除：键消失，`in` 判断为 False，数据彻底干净。
- 数量归零必须使用 `del`，从源头保证数据一致性。

五、单一职责原则
- show() 只负责展示，直接读取全局数据并打印，不修改、不过滤。
- 增删改函数负责修改数据，并在数量降为 0 时执行 `del` 清理。
- 展示与修改分离，各司其职，代码意图明确，易于维护。

六、最终方案：show() 无需传参和过滤
- 前提：增删改函数已通过 `del` 保持数据干净（无 0 值残留）。
- show() 直接遍历 products 和 cart 打印，不接收参数，不做任何过滤。
- 数据干净 → 展示简单 → 代码优雅。

七、传参 vs. 使用全局变量
- 函数需修改全局数据（增删改）：直接操作全局变量，利用引用修改。
- 函数仅展示数据（show）：直接读取全局变量，只读不写。
- 只有当函数需要操作多个不同字典，或需要独立于全局环境时，才通过参数传入。

八、认知升级过程
1.  发现 show() 中的过滤未能真正清理数据，产生困惑。
2.  尝试修改判空逻辑（检查所有值是否为零），属于临时修补。
3.  让 show() 也参与清理数据，看似方便，实则违反单一职责，导致职责混乱。
4.  最终理解：应在增删改函数中用 `del` 彻底清理，show() 只负责展示。至此真正掌握单一职责与数据一致性。
'''
