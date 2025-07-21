FROM python:3.9.21

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# 复制项目文件
COPY . .

RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONPATH=/app
ENV TZ=UTC

# 启动命令
CMD ["python", "app/main.py"]
