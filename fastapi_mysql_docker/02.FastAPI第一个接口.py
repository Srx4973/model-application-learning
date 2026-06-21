'''FastAPI
是一个用 Python 写的高性能 Web 框架，专门用来快速构建 API 接口‌，官方中文文档在 fastapi.tiangolo.com/zh/ 。
它最大的特点是写代码少、运行速度快，还能自动生成接口文档，特别适合做后端服务。

有什么厉害的地方
‌性能特别高‌：基于异步编程，处理并发请求比 Flask 等传统框架快 3-5 倍，尤其在数据库查询、外部 API 调用这些场景优势明显 。
‌开发效率高‌：靠 Python 类型提示自动补全代码，减少手动写验证逻辑的时间，开发速度能提升 200%～300%。
‌自动出文档‌：写完接口自动生成 Swagger 交互式文档，不用额外写说明，直接在线测试接口 。
‌错误少‌：请求数据自动验证类型，比如该传数字却传了文字，框架会自动返回 422 错误并提示哪里不对

*GET 查，POST 增，PUT 改，DELETE 删

方法	                 作用	       图书场景	           类比
GET /books	          查 全部	  拿到书单     	      翻目录
POST /books	          增 一本	  新书上架	          往书架放书
PUT /books/{id}	      改 整本	  修改某本书的全部信息	  把旧书拿走，放一本新的
DELETE /books/{id}	  删 一本	  下架某本书	          从书架拿走

 '''

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")             #app.get("/") 调用后返回一个装饰器函数，再用这个装饰器包裹 root函数。
async def root():         #async 标记这个函数是"异步函数"。
    return {"message": "Hello World"}

# 新增：返回图书列表的接口
@app.get("/books")
async def get_books():
    return [
        {"id": 1, "title": "Python入门", "author": "张三"},
        {"id": 2, "title": "FastAPI实战", "author": "李四"},
        {"id": 3, "title": "AI应用开发", "author": "王五"},
    ]

'''
一句话说
需要写好路由规则，FastAPI 来监听端口，有人访问 /books 就自动调用 get_books()，把返回值转成 JSON 扔回去。

流程拆解
用户浏览器 → 访问 http://localhost:8000/books
                    ↓
            FastAPI 收到请求，匹配路径 "/books"
                    ↓
            找到 @app.get("/books") 注册的函数
                    ↓
            执行 get_books() → 得到那个列表
                    ↓
            自动转成 JSON → 返给浏览器
'''

# 定义请求体的数据模型
class BorrowRequest(BaseModel):
    user_id: int
    book_id: int
    days: int = 14   # 默认借14天

@app.post("/borrow")
async def borrow_book(borrow: BorrowRequest):
    print(f"收到借书请求：用户{borrow.user_id} 借了书籍{borrow.book_id}，天数{borrow.days}")
    return {"status": "success", "message": f"用户{borrow.user_id}已借出书籍{borrow.book_id}"}