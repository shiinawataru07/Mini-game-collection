# Mini Game Collection

一个使用 **Python** 和 **Pygame** 开发的经典小游戏合集。

这个仓库用于练习游戏规则设计、图形界面开发和自动化测试，并会持续加入新的小游戏。项目采用简单、清晰的组织方式：每个游戏独立存放，核心规则尽量与 Pygame 界面分离，方便测试和后续扩展。

## 游戏列表

| 游戏 | 状态 | 简介 |
| --- | --- | --- |
| [2048](#2048) | 已完成，可持续优化 | 合并相同数字并挑战更高分数 |

计划后续加入 Snake、Tetris、Minesweeper、Tic-Tac-Toe 和 Maze 等游戏。

## 2048

当前仓库中的第一个游戏，实现了完整的 4×4 经典 2048 玩法。

### 游戏功能

- 标准 4×4 棋盘
- 上、下、左、右四个方向移动
- 正确的数字压缩与合并规则
- 每次有效移动后随机生成 2 或 4
- 当前分数统计与游戏结束检测
- 快速、平滑的方块移动动画
- 随时重新开始游戏
- 暖橙色、淡蓝色和淡绿色三套主题
- 中文和英文界面即时切换
- 可拖动窗口边缘调整大小，界面自动适配
- 自动记录并持久化历史最佳分数
- 使用剪贴板导出和读取 JSON 文本存档

### 操作方式

| 操作 | 功能 |
| --- | --- |
| 方向键或 `WASD` | 移动方块 |
| `R` | 重新开始当前游戏 |
| `Settings / 设置` | 打开设置界面 |
| 拖动窗口边缘 | 调整游戏窗口大小 |
| `Esc` | 关闭设置；设置未打开时退出游戏 |

设置界面支持切换颜色主题和语言、查看历史最佳分数、存档、读档以及重新开始游戏。

### JSON 存档与读档

点击设置中的 `Copy save JSON / 复制存档 JSON`，游戏会生成格式化的 JSON 文本并复制到剪贴板。可以将文本粘贴到任意文本文件中长期保存。

恢复游戏时，先复制完整的存档 JSON，再点击 `Load JSON / 读取 JSON`。存档会记录并恢复：

- 当前棋盘和分数
- 游戏结束状态
- 历史最佳分数
- 颜色主题和界面语言
- 存档格式版本和保存时间

读取前会校验游戏类型、存档版本、棋盘尺寸、方块数字、分数和设置。无效 JSON 不会改变当前游戏。

历史最佳分数还会自动保存在 `games/game_2048/.player_data.json`。这是本地运行时数据，已被 Git 忽略，不会提交到仓库。

## 项目结构

```text
mini-game-collection/
├── main.py                         # 小游戏合集入口
├── games/
│   ├── __init__.py
│   └── game_2048/
│       ├── __init__.py
│       ├── logic.py                # 游戏规则、状态和 JSON 存档校验
│       └── game.py                 # Pygame 界面、输入、设置和动画
├── tests/
│   └── test_2048.py                # 2048 自动化测试
├── requirements.txt                # 项目依赖
├── .gitignore
└── README.md
```

后续增加新游戏时，会在 `games/` 中为每个游戏建立独立目录，并在 `tests/` 中添加对应测试，避免不同游戏之间互相影响。

## 技术栈

- Python 3.10+
- Pygame 2.5+
- unittest（Python 标准库）

2048 的移动、合并、计分、随机方块、结束判断和存档校验都放在不依赖 Pygame 的核心逻辑中，以便独立测试。

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

### 4. 启动游戏

```bash
python main.py
```

当前只有 2048，因此项目入口会直接启动 2048。加入更多游戏后，入口会扩展为游戏选择界面。

## 运行测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖以下关键行为：

- 不同数字组合的压缩与合并
- 四个方向的棋盘移动
- 分数计算和随机方块生成
- 游戏结束与重新开始
- 主题、语言和响应式布局配置
- 动画移动轨迹
- JSON 存档生成、解析与非法数据拒绝
- 历史最佳分数本地保存

## 后续计划

- 继续改善 2048 的动画和交互体验
- 增加 Undo 和不同棋盘尺寸
- 探索 AI 自动游玩 2048
- 加入更多经典小游戏
- 在游戏数量增加后提供统一的游戏选择界面
