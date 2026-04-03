<div align="center">

<h1><img src="src/resources/icons/app.svg" width="24" height="24" alt="icon">&nbsp;HawkingHand</h1>

**Windows 全局热键自动化工具**

绑定热键 → 触发鼠标 / 键盘操作 → 或运行自定义 Python 脚本

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows)](../../releases)
[![Python](https://img.shields.io/badge/Python-3.12-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.10-41cd52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)

</div>

---

## ⚡ 功能

### 事件类型

| 类型 | 说明 |
|:----:|------|
| **Click** | 热键触发一次鼠标点击或键盘按键 |
| **Press** | 热键切换按下 / 释放状态（按一次按下，再按一次释放） |
| **Multi** | 热键开始 / 停止连点，可配置间隔和次数 |
| **Script** | 热键执行自定义 Python 脚本 |

### 窗口作用域（Scope）

事件可限定在特定进程或窗口标题下生效，支持通配符匹配。

```
格式：进程名:窗口标题
示例：notepad.exe:*        — 仅在记事本中生效
      *:*Document*         — 匹配任意含 "Document" 的窗口
```

### 脚本引擎

- 沙箱环境执行，内置 `click()`、`move_to()`、`sleep()`、`position()` 等 API
- 支持 `import` 脚本目录下的其他 `.py` 模块
- 文件修改后自动热重载
- 自动生成 `__builtins__.py` 提供 IDE 补全

### 其他

🎨 主题：深色 / 浅色 &emsp; 🌐 语言：中文 / English &emsp; 📌 系统托盘 &emsp; 🚀 开机自启

---

## 📦 安装

从 [Releases](../../releases) 下载最新的 `HawkingHand-*-windows-x64.zip`，解压即用。

配置文件存储于 `%APPDATA%\CedarHuang\HawkingHand\`

---

## 📜 脚本 API 速览

脚本存放于 `%APPDATA%\CedarHuang\HawkingHand\scripts\` 目录，每个 `.py` 文件即一个可选脚本。

> [!IMPORTANT]
> 以下仅为速览。完整、准确的 API 定义以程序自动生成的 `__builtins__.py` 为准，该文件位于脚本目录下，可直接在 IDE 中查看签名与文档。

```python
# 基本操作
click(MOUSE_LEFT)             # 左键点击
click(MOUSE_LEFT, 100, 200)   # 在指定坐标点击
click('a')                    # 按键 A
down(MOUSE_LEFT)              # 按下左键
up(MOUSE_LEFT)                # 释放左键
move(10, 0)                   # 相对移动
move_to(500, 300)             # 绝对移动
x, y = position()             # 获取鼠标位置

# 流程控制
sleep(500)                    # 暂停 500ms（响应停止信号）
exit()                        # 终止脚本

# 延迟控制（操作之间的自动间隔）
set_delay(50)                 # 设置操作间隔 50ms
with tmp_delay(200):          # 临时使用 200ms 间隔
    click(MOUSE_LEFT)

# 首次运行检测
if init():
    print('首次触发')

# 同脚本内共享数据
set_script_cache('count', get_script_cache('count', 0) + 1)
# 跨脚本间共享数据
set_global_cache('shared_key', 'value')

# 环境信息
process, title = foreground()  # 当前前台窗口
hotkey = event_hotkey()        # 触发此脚本的热键
```

---

## 🛠️ 从源码构建

```bash
# 环境要求：Python == 3.12
pip install -r requirements.txt

python build.py              # 编译 UI / 翻译 / 资源
python src/main.py           # 启动

python build.py dist         # Nuitka 打包 → dist/main.dist
```

<details>
<summary>更多构建命令</summary>

```bash
python build.py ui           # 仅编译 .ui
python build.py tr           # 提取翻译 + 编译 .qm
python build.py rcc          # 仅编译 .qrc 资源
python build.py clean        # 清理构建产物
python build.py check        # 检查哪些文件需要重新构建
```

</details>

---

## 📄 License

[Apache-2.0](LICENSE)
