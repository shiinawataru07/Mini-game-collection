# Mini Game Collection

一个使用 **Python** 和 **Pygame** 开发的经典小游戏合集。

项目用于练习游戏规则设计、图形界面开发和自动化测试。每个游戏拥有独立的代码目录和说明文档，核心规则尽量与 Pygame 界面分离，便于测试、维护和继续扩展。

## 游戏列表

| 游戏 | 状态 | 简介 | 详细说明 |
| --- | --- | --- | --- |
| 2048 | 已完成，可持续优化 | 移动棋盘并合并相同数字，在有限空间内挑战更高分数。支持多种棋盘尺寸、动画、JSON 存档和 AI 自动游玩。 | [查看玩法与功能](games/game_2048/README.md) |
| 贪吃蛇 | 已完成，可持续优化 | 控制不断成长的蛇寻找食物并避开危险。支持三种模式、限时奖励食物和暂停设置。 | [查看玩法与功能](games/game_snake/README.md) |

计划后续加入 Tetris、Minesweeper、Tic-Tac-Toe 和 Maze 等游戏。

## 安装与运行

### 1. 获取项目

```bash
git clone https://github.com/shiinawataru07/Mini-game-collection.git
cd Mini-game-collection
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 3. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 4. 启动合集

```bash
python main.py
```

入口会显示游戏选择界面。可以使用鼠标选择，也可以按 `1` 启动 2048、按 `2` 启动贪吃蛇。游戏内按 `Esc` 可以返回选择界面。

## 项目结构

```text
mini-game-collection/
├── .github/
│   └── workflows/
│       └── ci.yml                  # 测试与 Ruff 自动检查
├── main.py                         # 小游戏合集入口
├── games/
│   ├── __init__.py
│   ├── registry.py                 # 游戏元数据和启动入口注册表
│   ├── menu.py                     # 由注册表驱动的游戏选择界面
│   ├── common/                     # 少量跨游戏复用的字体、按钮和窗口工具
│   ├── game_2048/
│   │   ├── README.md               # 2048 详细介绍和玩法
│   │   ├── logic.py                # 棋盘、移动、合并和游戏状态
│   │   ├── ai.py                   # Expectimax 搜索和棋盘评价
│   │   ├── animation.py            # 移动轨迹与动画关键帧
│   │   ├── persistence.py          # JSON 存档和历史最佳分数
│   │   ├── config.py               # 主题、文案和界面配置
│   │   ├── ui.py                   # Pygame 布局与绘制
│   │   └── game.py                 # 输入处理和游戏主循环
│   └── game_snake/
│       ├── README.md               # 贪吃蛇详细介绍和玩法
│       ├── logic.py                # 移动、成长、食物和碰撞规则
│       ├── persistence.py          # 历史最佳分数和偏好
│       ├── config.py               # 速度、主题、文案和界面配置
│       ├── ui.py                   # 响应式布局与绘制
│       └── game.py                 # 输入缓冲和固定步进主循环
├── docs/
│   └── images/                     # 游戏说明文档使用的图片
├── tests/
│   ├── common/                     # 注册表和合集菜单测试
│   ├── game_2048/                  # 2048 自动化测试
│   └── game_snake/                 # 贪吃蛇自动化测试
├── pyproject.toml                  # 项目元数据、依赖和 Ruff 配置
├── requirements.txt
├── .gitignore
└── README.md                       # 项目概览
```

新增游戏时，应在 `games/` 中建立独立目录，在 `games/registry.py` 注册元数据、预览图和启动入口，并在游戏目录内提供 `README.md`。对应测试放入 `tests/<游戏名>/`，跨游戏基础设施测试放入 `tests/common/`。

## 技术栈

- Python 3.10+
- Pygame 2.5+
- unittest（Python 标准库）
- Ruff（代码检查与格式化）

## 运行测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖核心规则、动画计算、AI 决策、持久化、响应式布局和合集菜单等关键行为。

## 开发与代码质量

安装项目及开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行 Ruff 代码检查：

```bash
python -m ruff check .
```

格式化代码并验证格式：

```bash
python -m ruff format .
python -m ruff format --check .
```

GitHub Actions 会在每次推送和拉取请求时执行 Ruff，并在 Python 3.10、3.11、3.12 和 3.13 上运行完整测试。Pygame 测试使用无窗口驱动，因此可以在 CI 环境中运行。

## 后续计划

- 逐步加入 Tetris、Minesweeper、Tic-Tac-Toe 和 Maze
- 只在多个游戏确实需要时提取共享组件和通用设置
- 为新增游戏补充截图或演示 GIF
- 使用 PyInstaller 提供无需安装 Python 的可执行版本
- 通过 GitHub Releases 发布带版本号的稳定构建
