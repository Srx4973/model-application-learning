## Docker 核心（容器化与编排）

### 1.1 Docker 基础概念（面试高频）

- **镜像（Image）**：只读模板，包含运行应用所需的代码、依赖、环境变量等。
- **容器（Container）**：镜像的运行实例，轻量级隔离环境。
- **Dockerfile**：描述如何构建镜像的文本文件。
- **requirements.txt**:环境依赖文本文件。
- **镜像分层**：Docker 镜像由多层组成，每层对应 Dockerfile 中的一条指令。分层复用能加速构建和传输。

> 面试题：镜像和容器的区别？  
> 答：镜像是静态文件，容器是动态运行的进程；同一镜像可启动多个容器。

### 1.2 Dockerfile 核心指令（必会）

####a. 生成依赖清单（统一环境依赖）

```bash
pip freeze > requirements.txt  #生成依赖清单`
```
####b. 创建dockerfile文件

```dockerfile
FROM python:3.10-slim          # 指定基础镜像
WORKDIR /app                   # 设置容器内工作目录
COPY requirements.txt .        # 复制文件到容器
RUN pip install -r requirements.txt   # 构建时执行命令（安装依赖）
COPY . .                       # 复制项目代码
#我的项目代码全在book_management.py文件，所以使用  COPY book_management.py . 
EXPOSE 8000                    # 声明容器监听端口（仅文档作用）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]   # 容器启动时执行的命令
```

> 面试题：CMD 与 ENTRYPOINT 的区别？  
> - CMD：提供默认命令，可被 `docker run` 后的参数覆盖。  
> - ENTRYPOINT：定义容器的主进程，参数不可被覆盖（除非 `--entrypoint`）。  
> 通常组合使用：ENTRYPOINT 指定固定命令，CMD 提供默认参数。

### 1.3 构建与运行镜像

```bash
docker build -t 镜像名 .      # 构建镜像（注意末尾的点表示当前目录）
docker run -d -p 宿主机端口:容器端口 --name 容器名 镜像名
```

- `-d`：后台运行  
- `-p`：端口映射，宿主机端口与容器端口绑定  
- `--name`：为容器命名  

> 面试题：端口映射的作用？  
> 使外部（宿主机）能访问容器内部服务。容器有自己的网络命名空间，通过映射暴露服务。

### 1.4 docker-compose：多容器编排

**核心文件 `docker-compose.yml` 骨架**

```yaml
version: '3.1'

services:
  服务名:                  # 自定义名称，同时也是容器内的 DNS 域名
    build: .               # 使用 Dockerfile 构建
    image: 镜像名           # 或直接指定镜像
    container_name: 容器名  # 可选，自定义容器名
    ports:
      - "宿主机端口:容器端口"
    environment:
      - 环境变量=值
    depends_on:
      - 依赖服务名         # 决定启动顺序，但不保证依赖已就绪
    volumes:
      - 数据卷名:/容器内路径   # 持久化存储
    restart: always        # 崩溃后自动重启

volumes:
  数据卷名:                # 声明数据卷（用于持久化）
```

**常用命令**

```bash
docker-compose up -d      # 后台启动所有服务
docker-compose down       # 停止并删除所有容器（保留数据卷）
docker-compose down -v    # 停止并删除容器、数据卷（彻底清理）
docker-compose logs 服务名 # 查看某个服务的日志
docker-compose exec 服务名 bash  # 进入容器内部
```

### 1.5 容器间通信（核心问题）

**问题：如何让两个容器互相通信？**

- **原理**：docker-compose 会为所有服务创建一个**默认的虚拟网络**，所有容器都接入该网络。  
- **机制**：网络内置了 **DNS 服务**，容器的服务名（如 `mysql`）会被自动解析为容器的 IP 地址。  
- **使用**：在代码（如 FastAPI）中，数据库连接字符串使用服务名代替 IP：`mysql+pymysql://root:123456@mysql:3306/db`，无需关心具体 IP。  
- **注意**：容器内不能使用 `localhost` 访问宿主机或其他容器，因为每个容器的 `localhost` 指向自己。若需要访问宿主机服务，应使用 `host.docker.internal`（仅限开发环境）。

**depends_on 的局限性**

- `depends_on` 只保证**启动顺序**（先启动依赖服务），但不保证依赖服务**已准备就绪**（如 MySQL 已可接受连接）。  
- 若业务代码在依赖就绪前尝试连接，可能报错。常见解决方案：
  - 在应用代码中加入重试逻辑（如 `restart: always`）。
  - 使用健康检查（`condition: service_healthy`）或等待脚本。

> 面试题：如何确保服务启动顺序和就绪状态？  
> 答：`depends_on` 解决启动顺序，健康检查结合 `condition` 可确保就绪，或使用外部工具如 `wait-for-it.sh`。

### 1.6 数据持久化（Volume）

容器是无状态的，重启后内部数据丢失。`volumes` 将数据存储在宿主机上，容器重启后重新挂载即可恢复。

- **命名卷**：`volumes: - mysql_data:/var/lib/mysql`，由 Docker 管理存储位置。
- **绑定挂载**：`- /宿主机路径:/容器路径`，直接映射宿主机目录，便于开发调试。

> 面试题：容器数据持久化的方式有哪些？  
> 答：volumes、bind mounts、tmpfs。生产环境推荐 volumes，便于备份和迁移。

### 1.7 面试高频追问

- **容器与虚拟机的区别**：容器共享宿主机内核，轻量快速；虚拟机有完整 OS，资源开销大。
- **镜像分层原理**：每层只存储差异，拉取时复用已有层，节省空间和时间。
- **如何减少镜像体积**：使用 Alpine 基础镜像、合并 RUN 指令、清理缓存（`apt clean`、`pip --no-cache-dir`）。
- **Docker 网络模式**：bridge（默认）、host（共享宿主机网络）、none（隔离）。compose 默认使用自定义 bridge 网络。
- **如何调试容器内服务**：`docker logs` 查看日志，`docker exec -it 容器名 bash` 进入容器，`docker inspect` 查看元数据。
- **多阶段构建**：在 Dockerfile 中使用多个 `FROM`，第一阶段编译，第二阶段只复制产物，大幅缩小最终镜像。

### 1.8 实战注意事项

- **环境变量替代硬编码**：生产环境应将数据库密码等敏感信息通过环境变量传入，而非写死在 Dockerfile 或代码中。
- **`.dockerignore`**：类似 `.gitignore`，避免将本地无关文件（如虚拟环境、日志）复制到镜像，影响构建速度和体积。
- **启动顺序**：若 FastAPI 启动时需要连接 MySQL，建议在应用启动前执行迁移脚本，或使用重试机制。

**docker-compose 中常用的环境变量注入方式**
```yaml
environment:
  - DATABASE_URL=mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@mysql:3306/db
```
或者在 `.env` 文件中定义，由 docker-compose 自动读取。