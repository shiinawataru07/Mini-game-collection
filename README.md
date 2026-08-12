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
- 快速、平滑的移动、合并弹跳和新方块出现动画
- 动画期间缓存最后一个方向输入，支持连续操作
- 合并后显示短暂的分数增加提示
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
│       ├── logic.py                # 棋盘、移动、合并和游戏状态
│       ├── animation.py            # 移动轨迹与动画关键帧
│       ├── persistence.py          # JSON 存档和历史最佳分数
│       ├── config.py               # 主题、文案和界面配置
│       ├── ui.py                   # Pygame 布局与绘制
│       └── game.py                 # 输入处理和游戏主循环
├── tests/
│   ├── support.py                  # 测试共用工具
│   ├── test_logic.py               # 核心规则测试
│   ├── test_animation.py           # 动画计算测试
│   ├── test_persistence.py         # 存档与最佳分数测试
│   └── test_ui.py                  # 主题、语言和布局测试
├── requirements.txt                # 项目依赖
├── .gitignore
└── README.md
```

后续增加新游戏时，会在 `games/` 中为每个游戏建立独立目录，并在 `tests/` 中添加对应测试，避免不同游戏之间互相影响。

## 技术栈

- Python 3.10+
- Pygame 2.5+
- unittest（Python 标准库）

2048 按职责划分模块：核心规则和动画计算不依赖 Pygame，存档逻辑不依赖界面，`ui.py` 只负责绘制，`game.py` 负责协调输入和状态。这样修改某一部分时，不需要同时理解整个游戏。

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
- 动画移动轨迹、合并位置和缩放关键帧
- JSON 存档生成、解析与非法数据拒绝
- 历史最佳分数本地保存

## 后续计划

- 继续改善 2048 的动画和交互体验
- 增加 Undo 和不同棋盘尺寸
- 探索 AI 自动游玩 2048
- 加入更多经典小游戏
- 在游戏数量增加后提供统一的游戏选择界面
