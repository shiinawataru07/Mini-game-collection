# Mini Game Collection

一个使用 **Python** 和 **Pygame** 开发的经典小游戏合集。

当前稳定版本：**v1.3.0**。可以从 [GitHub Releases](https://github.com/shiinawataru07/Mini-game-collection/releases) 下载免安装的 Windows x64 压缩包，解压后运行 `MiniGameCollection.exe`。

项目用于练习游戏规则设计、图形界面开发和自动化测试。每个游戏拥有独立的代码目录和说明文档，核心规则尽量与 Pygame 界面分离，便于测试、维护和继续扩展。

## 游戏列表

| 游戏 | 状态 | 简介 | 详细说明 |
| --- | --- | --- | --- |
| 2048 | 已完成，可持续优化 | 移动棋盘并合并相同数字，在有限空间内挑战更高分数。支持多种棋盘尺寸、动画、JSON 存档和 AI 自动游玩。 | [查看玩法与功能](games/game_2048/README.md) |
| 贪吃蛇 | 已完成，可持续优化 | 控制不断成长的蛇寻找食物并避开危险。支持多张内置地图、地图编辑器和 JSON 地图文件导入导出。 | [查看玩法与功能](games/game_snake/README.md) |
| 扫雷 | 已完成，可持续优化 | 翻开安全格并标记地雷。支持纯逻辑棋盘、求解器提示、三种经典难度、自定义棋盘和最佳时间记录。 | [查看玩法与功能](games/game_minesweeper/README.md) |
| 俄罗斯方块 | 已完成，可持续优化 | 支持马拉松、40 行冲刺和两分钟计时模式，保留 SRS、7-bag、Hold 与 Ghost Piece。 | [查看玩法与功能](games/game_tetris/README.md) |
| 五子棋 | 已完成，可持续强化 AI | 支持本地双人和三档人机对战，AI 具备即时攻防、复合棋型分类、VCF 与 PVS 搜索。 | [查看玩法与功能](games/game_gomoku/README.md) |
| 飞机大战 | 已完成，可持续优化 | 从三款像素战机中选择座驾，迎战普通、精英和 Boss 敌机，收集强化道具并挑战更高波次。 | [查看玩法与功能](games/game_aircraft/README.md) |
| 数独 | 已完成，可持续扩充关卡 | 三档难度共 60 关，支持候选笔记、冲突提示、提示、撤销/重做和逐关最佳时间。 | [查看玩法与功能](games/game_sudoku/README.md) |

计划继续强化五子棋专家 AI，并逐步加入 Maze、黑白棋等适合集合定位的新游戏。

## 安装与运行

### Windows 免安装版

从 [Releases](https://github.com/shiinawataru07/Mini-game-collection/releases) 下载 `Mini-Game-Collection-v1.3.0-Windows-x64.zip`，完整解压后运行 `MiniGameCollection.exe`。同名 `.sha256` 文件可用于校验下载完整性。

### 从源代码运行

#### 1. 获取项目

```bash
git clone https://github.com/shiinawataru07/Mini-game-collection.git
cd Mini-game-collection
```

#### 2. 创建虚拟环境（推荐）

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

#### 3. 安装依赖

```bash
python -m pip install -r requirements.txt
```

#### 4. 启动合集

```bash
python main.py
```

入口会显示游戏选择界面。可以使用鼠标选择，也可以按 `1` 启动 2048、按 `2` 启动贪吃蛇、按 `3` 启动扫雷、按 `4` 启动俄罗斯方块、按 `5` 启动五子棋、按 `6` 启动飞机大战、按 `7` 启动数独。游戏内按 `Esc` 可以返回选择界面。

合集提供跨游戏共享的音频和显示设置，可从主菜单右上角的“全局设置”进入：

- `M`：静音或取消静音
- `-` / `+`：降低或提高主音量
- `F11`：进入或退出全屏
- `F10`：在主菜单打开或关闭全局设置

音量、静音和全屏状态会自动保存，并应用于所有游戏。2048、贪吃蛇、扫雷、俄罗斯方块、五子棋、飞机大战和数独均提供合成音效，不需要额外的音频资源文件。

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
│   ├── common/                     # 跨游戏类型、翻译、JSON、字体、控件和窗口工具
│   ├── game_2048/
│   │   ├── README.md               # 2048 详细介绍和玩法
│   │   ├── logic.py                # 棋盘、移动、合并和游戏状态
│   │   ├── ai.py                   # Expectimax 搜索和棋盘评价
│   │   ├── animation.py            # 移动轨迹与动画关键帧
│   │   ├── persistence.py          # JSON 存档和历史最佳分数
│   │   ├── config.py               # 主题、文案和界面配置
│   │   ├── ui.py                   # Pygame 布局与绘制
│   │   └── game.py                 # 输入处理和游戏主循环
│   ├── game_snake/                 # 贪吃蛇规则、界面和主循环
│   ├── game_minesweeper/
│   │   ├── README.md               # 扫雷详细介绍和玩法
│   │   ├── logic.py                # 布雷、展开、标记和胜负规则
│   │   ├── solver.py               # 纯逻辑求解、生成验证和提示
│   │   ├── persistence.py          # 各难度最佳时间和偏好
│   │   ├── config.py               # 难度、主题、文案和界面配置
│   │   ├── ui.py                   # 响应式棋盘与绘制
│   │   └── game.py                 # 输入、计时和游戏主循环
│   ├── game_tetris/                # 俄罗斯方块规则、SRS、输入、界面和主循环
│   ├── game_gomoku/                # 五子棋规则、搜索 AI、木棋盘界面和主循环
│   ├── game_aircraft/              # 像素飞机大战规则、界面、音效和主循环
│   └── game_sudoku/                # 数独题库、求解校验、界面和主循环
├── docs/
│   └── images/                     # 游戏说明文档使用的图片
├── tests/
│   ├── common/                     # 注册表和合集菜单测试
│   ├── game_2048/                  # 2048 自动化测试
│   ├── game_snake/                 # 贪吃蛇自动化测试
│   ├── game_minesweeper/           # 扫雷自动化测试
│   ├── game_tetris/                # 俄罗斯方块自动化测试
│   ├── game_gomoku/                # 五子棋自动化测试
│   ├── game_aircraft/              # 飞机大战自动化测试
│   └── game_sudoku/                # 数独自动化测试
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

- 实施五子棋 M3：VCT、威胁延伸、对称规约、开局库和 Elo 联赛
- 逐步加入 Maze、黑白棋等新游戏
- 只在多个游戏确实需要时提取共享组件和通用设置
- 为新增游戏补充截图或演示 GIF
- 继续完善各游戏的音效层次和动画反馈
- 使用 PyInstaller 提供无需安装 Python 的可执行版本
- 通过 GitHub Releases 发布带版本号的稳定构建
