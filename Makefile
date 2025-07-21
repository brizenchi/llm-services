# 变量定义
APP_NAME := llm-services
USERNAME := root
SERVER_IP := 47.116.173.33
SERVER_PATH := /$(USERNAME)/$(APP_NAME)
DOCKER_TAG := latest
PORT := 8130
BUILD_TIME := $(shell date "+%F %T")
COMMIT_SHA1 := $(shell git rev-parse HEAD)


# 编译标志
LDFLAGS := -X 'main.BuildTime=$(BUILD_TIME)' \
           -X 'main.CommitID=$(COMMIT_SHA1)' \
           -w -s

.PHONY: all build clean test lint docker-build docker-push run stop restart logs help

# 默认目标
all: build

# 清理
clean:
	@echo "Cleaning..."
	@rm -f $(APP_NAME)
	@docker system prune -f

# 运行测试
test:
	@echo "Running tests..."
	@go test -v ./...

# 代码检查
lint:
	@echo "Running linter..."
	@golangci-lint run ./...

# 重启服务
restart: stop run

# 开发环境相关命令
dev: export ENV=dev
dev: build run

# 测试环境相关命令
test: export ENV=test
test: build docker-build docker-push run

# 生产环境相关命令
prod: export ENV=prod
prod: test docker-build docker-push


# 构建 Docker 镜像
build:
	@echo "Building Docker image ..."
	@docker build -t $(APP_NAME):$(DOCKER_TAG) \
		-f deployment/Dockerfile .

# 推送 Docker 镜像到仓库
push:
	@echo "Pushing Docker image for $(ENV) environment..."
	@docker push $(APP_NAME):$(DOCKER_TAG)

remove:
	@docker rm -f $(APP_NAME)
	
run:
	@echo "Starting Docker container in $(ENV) environment..."
	@mkdir -p deployment/logs
	@touch deployment/.env
	@docker run -d \
		--name $(APP_NAME) \
		-e TZ=UTC \
		-v $(SERVER_PATH)/deployment/logs:/app/deployment/logs:delegated \
		-v $(SERVER_PATH)/deployment/.env:/app/deployment/.env:rw \
		-p ${PORT}:8000 \
		$(APP_NAME):$(DOCKER_TAG)

# 停止服务
stop:
	@echo "Stopping Docker container..."
	@docker stop $(APP_NAME)-$(ENV) || true
	@docker rm $(APP_NAME)-$(ENV) || true

# 查看日志
logs:
	@echo "Viewing logs for $(ENV) environment..."
	@docker logs -f $(APP_NAME)-$(ENV)

backup:
	@image_id=$$(docker images -q $(APP_NAME):latest); \
	if [ ! -z "$$image_id" ]; then \
		docker rmi $(APP_NAME):previous; \
		docker tag $(APP_NAME):latest $(APP_NAME):previous; \
		echo "Backed up $(APP_NAME):latest to $(APP_NAME):previous"; \
	else \
		echo "No previous $(APP_NAME):latest found, skipping backup"; \
	fi


deploy:
	@echo "Deploying to production server..."
	ssh $(USERNAME)@$(SERVER_IP) '\
		cd $(SERVER_PATH) && \
		git pull origin main && \
		git checkout main && \
		sudo make backup && \
		sudo make docker-build && \
		sudo make remove && \
		sudo make run'

rollback:
	@echo "Rolling back to previous version..."
	ssh $(USERNAME)@$(SERVER_IP) '\
		current_time=$$(date +%s); \
		docker tag $(APP_NAME):latest $(APP_NAME):$$current_time; \
		docker tag $(APP_NAME):previous $(APP_NAME):latest; \
		sudo make remove && \
		sudo make run'


# 帮助信息
help:
	@echo "Available commands:"
	@echo "  make build          - Build the application"
	@echo "  make clean          - Clean build files"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linter"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-push    - Push Docker image"
	@echo "  make run            - Start services"
	@echo "  make stop           - Stop services"
	@echo "  make restart        - Restart services"
	@echo "  make logs           - View logs"
	@echo ""
	@echo "Environment variables:"
	@echo "  ENV                 - Environment (dev/test/prod)"

# 设置默认环境变量
export DB_USER ?= deep_reading
export DB_PASSWORD ?= your_password
export DB_NAME ?= deep_reading
