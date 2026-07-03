# 1. 基础镜像：轻量级 Python 3.10
FROM python:3.10-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 只复制依赖文件（先复制这个，是为了利用 Docker 缓存，下次构建更快）
COPY requirements.txt .

#升级pip
RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 4. 安装依赖（-no-cache-dir 可以减小镜像体积，使用阿里云 PyPI 镜像加速）
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com

# 5. 复制项目所有代码到容器内
COPY book_management.py .

# 6. 暴露端口（告诉 Docker 容器监听 8000）
EXPOSE 8000

# 7. 启动命令（用 uvicorn 跑你的 main.py）
CMD ["uvicorn", "book_management:app", "--host", "0.0.0.0", "--port", "8000"]