from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, Depends,HTTPException
from sqlalchemy import create_engine, Column, Integer, String,DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, Session,declarative_base


app = FastAPI()

#1. 数据库连接字符串（注意密码和数据库名）
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/fastapi_demo?charset=utf8mb4"
#mysql+pymysql	用 pymysql 驱动连 MySQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) #来生产数据库会话对象。
Base = declarative_base()      # 创建一个基类，后续所有模型都继承它

#2. 定义 Book 模型(定义表结构)
class Book(Base):
    __tablename__ = "books"     # 数据库表名
    id = Column(Integer, primary_key=True, index=True)   # 主键，自增
    title = Column(String(100), index=True)              # 书名，最长100字符
    author = Column(String(50), index=True)              # 作者，最长50字符
    stock = Column(Integer, default=1)                   # 新增库存字段

class BorrowRecord(Base):
    __tablename__ = "borrow_records"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))  #外键，添加约束，必须得是 books 表里已经存在的 id，不能瞎填
    borrower = Column(String(50))          # 借阅人姓名
    borrow_date = Column(DateTime, default=datetime.utcnow) #插入这条记录时，自动把当前时间填进去
    return_date = Column(DateTime, nullable=True)  # 还书时填

# 创建表（第一次运行时会自动创建）
Base.metadata.create_all(bind=engine)   ## 扫描Base下所有模型，生成并执行CREATE TABLE

#3. 依赖：获取数据库会话(依赖注入)
def get_db():
    db = SessionLocal()  # 打开数据库连接
    try:
        yield db      # ← 把连接给路由函数用
        # yield 在函数中间"暂停"，把值返回给调用方，等调用方用完后再回来执行后面的代码
    finally:
        db.close()    # ← 用完自动关闭


#添加书请求
class BookCreate(BaseModel):
    title : str
    author : str
    stock : int

#添加图书接口
@app.post("/books")
def add(book : BookCreate, db: Session = Depends(get_db)):

    # 1. 创建 Book 实例（将请求体数据转为 ORM 对象）
    #a. 如果book本身是字典可以用 **解包
    new_book = Book(**book.dict())# 如果 book 是 Pydantic 模型
    # 或 new_book = Book(**book)   # 如果 book 是普通字典

    #b. 直接使用关键字参数
    #new_book = Book(title=book.title, author=book.author)

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


# 借书请求
class BorrowRequest(BaseModel):
    book_id: int
    borrower: str

#编写借书接口
@app.post("/borrow")
def borrow_book(req: BorrowRequest, db: Session = Depends(get_db)):
    # 1. 查询图书，检查库存
    book = db.query(Book).filter(Book.id == req.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    if book.stock <= 0:
        raise HTTPException(status_code=400, detail="库存不足")

    # 2. 减少库存
    book.stock -= 1

    # 3. 创建借阅记录
    record = BorrowRecord(book_id=req.book_id, borrower=req.borrower)
    db.add(record)

    # 4. 提交事务
    db.commit()
    db.refresh(record)

    return {"status": "success", "message": f"{req.borrower} 借阅成功", "record_id": record.id}

'''为什么用raise不用return
这是 Web 开发的核心规则：
1.return（返回）：代表 “请求处理成功”，HTTP 状态码默认是 200（正常）。浏览器/前端拿到数据去渲染。
2.raise HTTPException（抛异常）：代表 “请求出错了”，FastAPI 会立刻拦截，
自动把 HTTP 状态码改为 400（请求有误）或 404（找不到），并返回错误信息。
必须用 raise，否则前端（或调用方）会以为“借书成功”，但实际上库存没变，造成数据错乱。

'''

# 还书请求（只需 book_id）
class ReturnRequest(BaseModel):
    book_id: int

#编写还书接口
@app.post("/return")
def return_book(req: ReturnRequest, db: Session = Depends(get_db)):
    # 1. 查询图书
    book = db.query(Book).filter(Book.id == req.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")

    # 2. 查找该图书最新的未归还借阅记录
    record = db.query(BorrowRecord).filter(   #两个筛选条件
        BorrowRecord.book_id == req.book_id,  #1.在书库里
        BorrowRecord.return_date.is_(None)    #2.归还日期为空，.is_(None) 是 SQLAlchemy 特有的写法，对应SQL里的 IS NULL。
    ).order_by(BorrowRecord.borrow_date.desc()).first()  #order_by是 SQL 排序语句，.desc()：降序的意思
    if not record:
        raise HTTPException(status_code=400, detail="该书没有被借出")

    # 3. 更新借阅记录，标记归还日期
    record.return_date = datetime.utcnow()

    # 4. 增加库存
    book.stock += 1

    # 5. 提交
    db.commit()

    return {"status": "success", "message": f"《{book.title}》已归还"}

'''
场景	                               标准动作	                   是否需要 add	     是否需要 refresh
创建新数据（借书记录	           创建对象 → db.add() → 
,添加图书）                      db.commit() → db.refresh()	     必须	          如果需要自增 ID（主键）就加

更新已有数据（还书、改库存）	   查询拿到对象 → 改属性 → db.commit()	     不需要	           不需要

'''

#查询所有借阅记录接口
@app.get("/borrow_records")
def br(db: Session = Depends(get_db)):
    borrow_records = db.query(BorrowRecord).all()
    return borrow_records
