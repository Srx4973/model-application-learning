import pytest
from fastapi.testclient import TestClient
from book_management import app  # 你的 FastAPI 应用
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from book_management import Base, get_db  # 导入你的模型和依赖

# 1. 配置测试数据库（使用 SQLite 内存数据库，避免污染真实数据）
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"  # 也可以用 ":memory:"，但为了方便查看，用文件
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. 创建测试数据库表
Base.metadata.create_all(bind=engine)

# 3. 覆写依赖，让测试用测试数据库
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db    #dependency_overrides覆盖原有依赖项

# 4. 创建测试客户端
client = TestClient(app)   # 创建“虚拟浏览器”

# 5. 每个测试前准备：插入一本库存为 1 的书
@pytest.fixture      #@pytest.fixture 的写法是固定模式：准备数据
def setup_book():
    # 直接操作测试数据库插入一本书
    db = TestingSessionLocal()
    from book_management import Book
    test_book = Book(title="测试书", author="测试员", stock=1)
    db.add(test_book)
    db.commit()
    db.refresh(test_book)
    book_id = test_book.id
    db.close()
    return book_id

# ========== 三个测试用例 ==========

# 测试 1：正常借书成功
def test_borrow_success(setup_book):
    book_id = setup_book
    response = client.post(
        "/borrow",
        json={"book_id": book_id, "borrower": "张三"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "张三" in data["message"]

# 测试 2：库存不足时借书失败
def test_borrow_out_of_stock(setup_book):
    book_id = setup_book
    # 先借一次（把库存用完）
    client.post("/borrow", json={"book_id": book_id, "borrower": "李四"})
    # 再借第二次，应该报错
    response = client.post(
        "/borrow",
        json={"book_id": book_id, "borrower": "王五"}
    )
    assert response.status_code == 400
    assert "库存不足" in response.json()["detail"]

# 测试 3：图书不存在时借书失败
def test_borrow_book_not_found():
    response = client.post(
        "/borrow",
        json={"book_id": 9999, "borrower": "赵六"}  # 不存在的 ID
    )
    assert response.status_code == 404
    assert "图书不存在" in response.json()["detail"]