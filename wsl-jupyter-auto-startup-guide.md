# WSL Jupyter 自动化启动 & 环境变量配置指南

## 目录

- [1. 安装 Miniconda 与 Jupyter](#1-安装-miniconda-与-jupyter)
- [2. 配置环境变量（关键！）](#2-配置环境变量关键)
- [3. 创建 WSL 自启动脚本](#3-创建-wsl-自启动脚本)
- [4. 配置 WSL 自启动](#4-配置-wsl-自启动)
- [5. 测试与验证](#5-测试与验证)
- [6. 常见问题排查](#6-常见问题排查)

---

## 1. 安装 Miniconda 与 Jupyter

```bash
# 下载 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建 conda 环境
conda create -n deepseek python=3.13 -y
conda activate deepseek

# 安装 Jupyter Lab
pip install jupyterlab

# 验证路径
which jupyter
# 输出示例: /home/dee/miniconda3/envs/deepseek/bin/jupyter
```

---

## 2. 配置环境变量（关键！）

### 2.1 编辑 `~/.bashrc`

```bash
vim ~/.bashrc
```

### 2.2 添加环境变量

**⚠️ 重要：必须将 `export` 放在交互式检查之前！**

找到 `.bashrc` 中如下代码段：

```bash
# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac
```

**在 `# If not running interactively` 这行之前**，添加你的环境变量：

```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export OTHER_KEY="your-other-key"

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac
```

### 2.3 为什么必须放在这里？

- WSL 自启动脚本使用 `bash -lc`（非交互式登录 shell）启动 Jupyter
- `.bashrc` 默认在非交互式模式下会 `return`，不到达文件末尾的 `export`
- 把环境变量放在 `case` 守卫**之前**，确保**所有场景**都能加载

### 2.4 验证环境变量

```bash
# 重新加载
source ~/.bashrc

# 测试
echo $DEEPSEEK_API_KEY
# 输出: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 模拟 WSL 启动时的非交互式登录 shell
sudo -u dee -H bash -lc 'echo $DEEPSEEK_API_KEY'
# 输出: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 3. 创建 WSL 自启动脚本

### 3.1 确定项目目录

```bash
# 示例
PROJECT_DIR="/home/dee/workspace/jk/deepseek-quickstart"
mkdir -p "$PROJECT_DIR"
```

### 3.2 创建脚本

```bash
sudo vim /usr/local/bin/start-jupyter.sh
```

写入以下内容：

```bash
#!/bin/bash

PROJECT_DIR="/home/dee/workspace/jk/deepseek-quickstart"
JUPYTER="/home/dee/miniconda3/envs/deepseek/bin/jupyter"
LOG_FILE="$PROJECT_DIR/jupyter.log"
BOOT_LOG="$PROJECT_DIR/wsl-boot.log"

echo "start-jupyter.sh executed at $(date)" >> "$BOOT_LOG"

# 如果已经启动，就不要重复启动
if pgrep -u dee -f "jupyter.*--port=8000" > /dev/null; then
  echo "jupyter already running at $(date)" >> "$BOOT_LOG"
  exit 0
fi

# WSL boot command 是 root 执行的，这里切换回 dee 用户启动 Jupyter
sudo -u dee -H bash -lc "
  export PATH=/home/dee/miniconda3/envs/deepseek/bin:/home/dee/miniconda3/bin:\$PATH
  cd $PROJECT_DIR || exit 1

  nohup $JUPYTER lab \
    --no-browser \
    --IdentityProvider.token='123456' \
    --ip=127.0.0.1 \
    --port=8000 \
    --notebook-dir=$PROJECT_DIR \
    >> $LOG_FILE 2>&1 &
"
```

### 3.3 关键路径变量说明

| 变量 | 示例值 | 说明 |
|------|--------|------|
| `PROJECT_DIR` | `/home/dee/workspace/jk/deepseek-quickstart` | Jupyter 工作目录 |
| `JUPYTER` | `/home/dee/miniconda3/envs/deepseek/bin/jupyter` | Jupyter 可执行文件路径 |
| `LOG_FILE` | `$PROJECT_DIR/jupyter.log` | Jupyter 运行时日志 |
| `BOOT_LOG` | `$PROJECT_DIR/wsl-boot.log` | 自启动脚本执行日志 |

**迁移时**只需将 `/home/dee` 替换为新用户名，`deepseek` 替换为新的 conda 环境名。

### 3.4 赋予执行权限

```bash
sudo chmod +x /usr/local/bin/start-jupyter.sh
```

---

## 4. 配置 WSL 自启动

### 4.1 编辑 WSL 配置

```bash
sudo vim /etc/wsl.conf
```

### 4.2 写入配置

```ini
[boot]
command=/usr/local/bin/start-jupyter.sh
```

如果 `/etc/wsl.conf` 已有其他内容，只需追加 `[boot]` 部分。

### 4.3 生效方式

**方案 A：重启 Windows 终端 + 重新进入 WSL**

```bash
exit                    # 退出 WSL
wsl --shutdown          # 在 PowerShell 或 CMD 中执行
wsl                     # 重新进入
```

**方案 B：不退出 WSL，手动测试脚本**

```bash
# 先确保没有旧进程
pkill -f "jupyter lab"

# 手动执行脚本
sudo /usr/local/bin/start-jupyter.sh
```

---

## 5. 测试与验证

### 5.1 检查进程

```bash
ps aux | grep jupyter | grep -v grep
# 应看到 jupyter-lab 进程
```

### 5.2 检查启动日志

```bash
cat /home/dee/workspace/jk/deepseek-quickstart/jupyter.log
# 应看到类似: Jupyter Server 2.18.2 is running at:
```

### 5.3 检查自启动日志

```bash
cat /home/dee/workspace/jk/deepseek-quickstart/wsl-boot.log
# 应看到: start-jupyter.sh executed at ...
```

### 5.4 验证 Jupyter 进程中的环境变量

```bash
# 找到 Jupyter 进程 PID
ps aux | grep jupyter | grep -v grep | awk '{print $2}'

# 查看该进程的环境变量
cat /proc/<PID>/environ | tr '\0' '\n' | grep DEEPSEEK_API_KEY
# 输出: DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 5.5 在 Jupyter Notebook 中验证

打开 `http://127.0.0.1:8000`，密码 `123456`，在 notebook 中运行：

```python
import os
api_key = os.getenv("DEEPSEEK_API_KEY")
print(api_key)
# 应输出你的 key
```

---

## 6. 常见问题排查

### 问题 1：Jupyter 启动但 `os.getenv("DEEPSEEK_API_KEY")` 返回 `None`

**原因**：`.bashrc` 的环境变量 `export` 放在了交互式检查（`case $- in *i*)`）之后，非交互式 shell 启动时未加载。

**解决**：将 `export` 移到交互式检查之前（见 [2.2 节](#22-添加环境变量)）。

### 问题 2：Jupyter 未启动

**检查步骤**：

```bash
# 1. 检查是否已运行（防重复启动逻辑）
tail -5 /home/dee/workspace/jk/deepseek-quickstart/wsl-boot.log

# 2. 检查脚本权限
ls -la /usr/local/bin/start-jupyter.sh
# 应有 -rwxr-xr-x

# 3. 检查 conda 环境是否存在
/home/dee/miniconda3/envs/deepseek/bin/python --version

# 4. 检查 Jupyter 是否安装
/home/dee/miniconda3/envs/deepseek/bin/jupyter --version
```

### 问题 3：端口冲突

```bash
# 检查 8000 端口占用
ss -tlnp | grep 8000

# 修改脚本中的 --port=8000 为其他端口
```

### 问题 4：迁移到新 WSL 后脚本不工作

需修改脚本中的以下路径：

| 原路径 | 替换 |
|--------|------|
| `/home/dee` | `/home/<新用户名>` |
| `miniconda3/envs/deepseek` | `miniconda3/envs/<新环境名>` |
| `dee`（`pgrep -u dee`） | `<新用户名>` |

---

## 完整清单：WSL 迁移步骤

1. 安装 Miniconda + Jupyter Lab
2. 配置 `~/.bashrc` — export 放在交互式检查**之前**
3. 创建 `/usr/local/bin/start-jupyter.sh` — 替换路径为新用户
4. `sudo chmod +x /usr/local/bin/start-jupyter.sh`
5. 配置 `/etc/wsl.conf`
6. `wsl --shutdown && wsl` 重启测试
7. 验证 `os.getenv("DEEPSEEK_API_KEY")`
