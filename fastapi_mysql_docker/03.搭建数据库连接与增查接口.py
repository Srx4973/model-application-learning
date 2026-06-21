from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session,declarative_base
from pydantic import BaseModel

app = FastAPI()

#1. 数据库连接字符串（注意密码和数据库名）
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/fastapi_demo?charset=utf8mb4"
#mysql+pymysql	用 pymysql 驱动连 MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)


'''
sessionmaker 是一个“工厂”，专门用来生产数据库会话对象。
1.把 engine（发动机）绑给它，它就能随时帮造出一个 Session 对象。
2.autocommit=False：禁止自动提交，让手动控制事务（commit 或 rollback），更安全。
3.autoflush=False：禁止自动刷新，避免不必要的查询，提高性能。
4.类比：SessionLocal 就像一家餐馆的“点餐机”，按一下按钮（调用 SessionLocal()），
它就给一张能与数据库通话的“餐桌号”（Session 对象）。

'''
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #来生产数据库会话对象。
Base = declarative_base()      # 创建一个基类，后续所有模型都继承它

'''
Base 是一个基类。定义的 Book 类必须继承它。
通过继承 Base，SQLAlchemy 知道 Book 是一个“数据库表的映射”。
Base 会记录所有继承它的子类，并把它们整理到一个“注册表”（Base.metadata）里。
类比：Base 就像一个“蓝图登记处”。拿着它画图纸（定义 class Book(Base)），登记处就知道要造哪几张表。

'''

#2. 定义 Book 模型(定义表结构)
class Book(Base):
    __tablename__ = "books"     # 数据库表名
    id = Column(Integer, primary_key=True, index=True)   # 主键，自增
    title = Column(String(100), index=True)              # 书名，最长100字符
    author = Column(String(50), index=True)              # 作者，最长50字符

# 创建表（第一次运行时会自动创建）
Base.metadata.create_all(bind=engine)   ## 扫描Base下所有模型，生成并执行CREATE TABLE


'''为什么get_books_from_db这个函数不需要 async（异步）？
现在的模式：
驱动（Driver）：现在用的是 pymysql（连接字符串里 mysql+pymysql:// ）。
模式（Mode）：同步（阻塞）模式。pymysql 是纯 Python 编写的同步库，它发送 SQL 请求后，线程会卡在那里干等数据库返回结果。

原因：用的 SQLAlchemy 是同步（阻塞）的 ORM。db.query(Book).all() 在等待数据库返回数据时，会阻塞当前线程。
1.如果把它放在 async def 中，它会阻塞 FastAPI 的事件循环，导致所有请求排队等待，反而拖慢性能。

2.FastAPI 的设计：对于同步的 I/O 操作（如普通 SQLAlchemy），使用普通 def，FastAPI 会自动把它放到外部线程池中运行，
不会阻塞主事件循环。这样既保留了同步代码的简洁性，又不会影响整体并发。

3.如果将来改用异步数据库驱动（如 asyncpg + sqlalchemy.ext.asyncio），那时才需要写 async def 和 await。

'''

# 依赖：获取数据库会话(依赖注入)
def get_db():
    db = SessionLocal()  # 打开数据库连接
    try:
        yield db      # ← 把连接给路由函数用
        # yield 在函数中间"暂停"，把值返回给调用方，等调用方用完后再回来执行后面的代码
    finally:
        db.close()    # ← 用完自动关闭

# 新接口：从数据库查询所有图书  SQLAlchemy ORM（对象关系映射）
@app.get("/books/db")
def get_books_from_db(db: Session = Depends(get_db)):  #传入数据库会话对象（Session）
    books = db.query(Book).all()     #query 是数据库会话（db）提供的一个“查询构建器”
    return books                     #.all() 的作用是：执行这条 SQL，把查询到的所有记录都拉出来，并装进一个 Python 列表里。

'''
1.db: Session传入的是一个数据库会话对象（Session）
db: Session 是类型注解,数据库连接的入口，通过这个入口，才能操作数据库

2.= Depends(get_db) 是 FastAPI 的依赖注入魔法
直白的说，FastAPI 在调用 get_books_from_db 之前，会先跑去执行 get_db() 这个函数。
而get_db() 函数会干两件事：① 创建一个数据库会话（db = SessionLocal()）；② 执行 yield db 把这个会话交出来。
然后 FastAPI 把这个“交出来的会话”赋值给 db 参数，塞进接口函数里。

3.query 是数据库会话（db）提供的一个“查询构建器”。
它的作用不是去查数据，而是先搭好一个 SQL 查询的架子。
把 Book 这个模型类传给它，它就知道要查的是 books 这张表。
此时，SQL 语句还没有发送给 MySQL 数据库，它只是在内存里生成了一条类似于 SELECT * FROM books 的待执行指令。

4..all() 的作用是：执行这条 SQL，把查询到的所有记录都拉出来，并装进一个 Python 列表里。
db.query(Book) 只是搭建了查询架子，并没有真正去数据库跑一圈。.all() 就是那个“扣动扳机”的动作。

'''


class BookCreate(BaseModel):
    title : str
    author : str

@app.post("/books/db")
def add(book : BookCreate, db: Session = Depends(get_db)):

    # 1. 创建 Book 实例（将请求体数据转为 ORM 对象）
    #a. 如果book本身是字典可以用 **解包
    new_book = Book(**book.dict())# 如果 book 是 Pydantic 模型
    # 或 new_book = BookCreate(**book)   # 如果 book 是普通字典

    #b. 直接使用关键字参数
    #new_book = BookCreate(title=book.title, author=book.author)

    #2.添加到会话（暂存到内存）
    db.add(new_book)

    # 3. 真正写入 MySQL
    db.commit()

    # 4. 刷新（获取数据库生成的 id 等）
    db.refresh(new_book)

    #查询并返回所有书
    #books = db.query(Book).all()

    # 5. 返回成功信息
    return {"status": "success", "message": f"已添加《{new_book.title}》", "id": new_book.id}


'''为什么要定义两个模型
模型	                         是否包含 id	                           原因
Book（ORM 模型）	               ✅ 包含	    这是数据库表的一行数据，在查询（SELECT）时，数据库会返回 id，所以这个对象必须能接收 id。

                                            这是客户端（前端）发来的创建请求。id 是数据库自动生成的，不允许前端指定。
BookCreate（Pydantic 请求体）	   ❌ 不包含	    如果前端传了 {"id": 999, "title":"xxx"}，直接拿去 INSERT，要么覆盖已有数据，要么因为主键冲突报错。

1.Book（ORM）对应“数据库的行”,BookCreate（请求体）对应“用户“
这就是为什么需要定义两个类：一个管“怎么写进数据库”（ORM），一个管“用户能填什么”（Pydantic）。
'''