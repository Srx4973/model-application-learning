'''pydantic 概述
pydantic 库是 python 中用于数据接口 定义检查与设置管理的库。
pydantic 在运行时强制执行类型提示，并在数据无效时提供友好的错误。

具有如下优点：

1.易于使用： Pydantic 很容易安装与使用，并且有一个简单的 API，使得所有开发者都可以快速上手使用。
2.快速验证： Pydantic 快速有效地执行数据验证，使其适合于在高性能的应用程序中使用。
3.自动生成文档： Pydantic 可以为数据模型自动生成文档，节省时间，并且更容易的理解数据结构。
4.类型提示支持： Pydantic 支持类型提示，使开发人员更容易定义数据结构，避免在代码中出现错误。
5.与 FastAPI 集成： Pydantic 可以很容易地与 FastAPI（一个高性能的 Python 网络框架）集成，为 API 提供自动请求和响应验证。
6.自定义验证规则： Pydantic 允许开发人员定义自定义的验证规则，使得在需要的时候可以实现复杂的验证逻辑。
7.一致的数据： Pydantic 确保项目中使用的数据是一致的，并符合所需的标准，减少了错误的风险，使代码库的维护更加容易。
8.与 IDE/linter 完美搭配，不需要学习新的模式，只是使用类型注解定义类的实例
9.多用途，BaseSettings 既可以验证请求数据，也可以从环境变量中读取系统设置
10.可扩展，可以使用 validator 装饰器装饰的模型上的方法来扩展验证
11.数据类集成，dataclass 装饰器可以创建带有输入数据解析和验证的普通 Python 数据类。

一. Pydantic 的工作方式

Pydantic 的工作方式是允许开发人员使用 Python 类来定义数据模型。这些类继承自 Pydantic 提供的 BaseModel 类，可以包括类型提示、默认值和验证规则。
当收到数据时，Pydantic 使用数据模型来验证传入的数据，并确保其符合所定义的要求。在验证过程中，Pydantic 对照数据模型中定义的类型提示和验证规则，检查数据中的每个字段。
如果数据不符合要求，Pydantic 会提出一个错误，并停止验证过程。如果数据是有效的，Pydantic 就会创建一个数据模型的实例，用传入的数据来填充它，并将其返回给用户。
Pydantic 还提供了一些高级功能，例如字段别名，自定义验证函数，以及对嵌套数据模型的支持，使得它可以处理广泛的数据验证场景。
此外，Pydantic 支持序列化和反序列化，允许根据需要将数据转换为 Python 数据结构、JSON 和其他格式。

二. BaseModel（基本模型 ）
在 Pydantic 中，BaseModel 是一个用于定义数据模型的基类。它允许创建一个描述数据结构、验证数据和进行数据转换的类。
BaseModel 基本模型提供了属性和方法来定义字段，校验数据以及序列化数据。

BaseModel 提供的常用功能有：
数据验证：当创建模型实例时，Pydantic 会自动验证传入的数据是否满足字段定义的规则。
数据转换：Pydantic 会尝试将输入数据转换为模型中定义的字段类型，例如将字符串转换为整数或浮点数。
自动文档生成：基于模型的字段定义，Pydantic 可以自动生成文档和模型验证的错误消息。
嵌套模型：可以在模型内部使用其他模型，从而创建复杂的数据结构。
序列化和反序列化：允许根据需要将数据转换为 Python 数据结构、JSON 和其他格式。
'''

from datetime import datetime
from pydantic import BaseModel, PositiveInt
from pydantic import ValidationError

#用户表
class User(BaseModel):
    id: int                      # 字段名: 类型
    name: str = '匿名用户'       # 字段名: 类型 = 默认值
    signup_ts: datetime | None   # 注册时间，可以是 datetime 对象，也可以是 None（表示没有值）。
    tastes: dict[str, PositiveInt]  # 用户的品味偏好，是一个字典。键必须是字符串（如 "wine"），
                                    # 值必须是 正整数（PositiveInt 是 Pydantic 提供的类型，值 > 0）
external_data = {
    'id': 1,
    'signup_ts': '2026-06-01 12:22',
    'tastes': {
        'wine': 9,
        b'cheese': 7,
        'cabbage': '1',
    },
}

user1 = User(**external_data)#在 Python 中, ** 叫字典解包（dict unpacking）。
#当用在函数/类调用时 func(**dict)，它会将字典的 键值对 转换成 关键字参数。

print(user1.id)
print(user1.model_dump())

#验证失败，Pydantic 会引发一个错误并详细说明哪里出错了
data  = {'id':'a', 'tastes':{}}

try:
    User(**data)
except ValidationError as e:
    print(e.errors())