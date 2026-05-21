# WSL 安装 Open WebUI（捆绑 Ollama 版）

环境：WSL2 / Ubuntu 22.04 / Docker

---

## 1. 拉取镜像

镜像约 12.6GB，需科学上网。

```bash
# 捆绑 Ollama 版（推荐）
docker pull ghcr.io/open-webui/open-webui:ollama

# 纯 WebUI 版（需自行连接外部 Ollama）
docker pull ghcr.io/open-webui/open-webui:main
```

```bash
# 验证拉取成功
docker images ghcr.io/open-webui/open-webui
```

---

## 2. 方法一：Docker Compose（推荐）

### 2.1 创建目录结构

```bash
mkdir -p /home/docker/open-webui/data
mkdir -p /home/docker/open-webui/ollama
```

### 2.2 创建 docker-compose.yml

文件路径：`/home/docker/open-webui/docker-compose.yml`

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:ollama
    container_name: open-webui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      TZ: Asia/Shanghai
    volumes:
      - ./data:/app/backend/data
      - ./ollama:/root/.ollama
    networks:
      - docker-net
    entrypoint:
      [
        "sh",
        "-c",
        "chown -R 0:0 /app/backend/data /root/.ollama && exec bash start.sh",
      ]

networks:
  docker-net:
    external: true
```

### 2.3 确保外部网络存在

```bash
docker network ls | grep docker-net || docker network create docker-net
```

### 2.4 启动容器

```bash
docker compose -f /home/docker/open-webui/docker-compose.yml up -d
```

### 2.5 查看状态

```bash
docker ps --filter name=open-webui
```

---

## 3. 方法二：Docker Run（单行命令）

```bash
docker run -d \
  -p 3000:8080 \
  -v open-webui-data:/app/backend/data \
  -v open-webui-ollama:/root/.ollama \
  --name open-webui \
  --restart unless-stopped \
  ghcr.io/open-webui/open-webui:ollama
```

> 使用 Docker 命名卷（`open-webui-data`、`open-webui-ollama`），数据存储在 `/var/lib/docker/volumes/` 下。
>
> 如果想用绑定挂载（数据放在宿主机路径），替换 `-v` 参数：
> ```bash
> -v /path/to/data:/app/backend/data
> -v /path/to/ollama:/root/.ollama
> ```

---

## 4. 验证

```bash
# 查看健康状态
docker ps --filter name=open-webui --format "table {{.Names}}\t{{.Status}}"

# 测试 HTTP 访问
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000

# 查看日志
docker logs open-webui -f
```

浏览器打开：`http://localhost:3000`

---

## 5. 拉取模型

容器内自带 Ollama，通过 `docker exec` 拉取模型：

```bash
# 拉取模型
docker exec open-webui ollama pull deepseek-r1:1.5b

# 列出已下载的模型
docker exec open-webui ollama list
```

模型文件存储在 `./ollama/models/`（绑定挂载）或命名卷中，容器销毁后数据不丢失。

---

## 6. 常用管理命令

```bash
# 停止
docker compose -f /home/docker/open-webui/docker-compose.yml down

# 启动
docker compose -f /home/docker/open-webui/docker-compose.yml up -d

# 重启
docker compose -f /home/docker/open-webui/docker-compose.yml restart

# 查看实时日志
docker logs -f open-webui

# 进入容器
docker exec -it open-webui sh
```

---

## 7. 注意事项

- 镜像和模型拉取需要科学上网
- 容器以 root 运行，绑定挂载的目录会被写入 root 权限文件，`entrypoint` 中的 `chown` 已在启动时自动修正
- WSL2 会自动把端口转发到 Windows 宿主机，Windows 浏览器直接访问 `http://localhost:3000`
