# Mini Game Collection

一个使用 Python 和 Pygame 编写的小游戏合集。目前包含第一个游戏：2048。

## 当前游戏

- 2048

后续可以继续加入 Snake、Tetris、Minesweeper、Tic-Tac-Toe 和 Maze 等小游戏。

## 2048 功能

- 4×4 棋盘与标准数字合并规则
- 方向键或 WASD 控制
- 随机生成 2 或 4
- 分数统计与游戏结束检测
- 随时重新开始游戏
- 暖橙、淡蓝和淡绿三套颜色主题
- 可拖动窗口边缘调整大小，棋盘会自动适配

## 项目结构

```text
mini-game-collection/
├── main.py
├── games/
│   └── game_2048/
│       ├── logic.py   # 与 Pygame 无关的游戏规则
│       └── game.py    # 输入、设置、绘制和游戏循环
├── tests/
│   └── test_2048.py
├── requirements.txt
└── README.md
```

## 运行环境

- Python 3.10+

安装依赖：

```bash
python -m pip install -r requirements.txt
```

启动游戏：

```bash
python main.py
```

## 操作方式

- 方向键或 `WASD`：移动数字
- `R`：重新开始
- `Settings`：打开设置，可以切换主题或重新开始
- 拖动窗口边缘：调整窗口大小
- `Esc`：关闭设置；设置未打开时退出游戏

## 运行测试

```bash
python -m unittest discover -s tests -v
```

核心规则与 Pygame 界面分离，因此移动、合并、计分、随机方块和游戏结束判断都可以独立验证。
