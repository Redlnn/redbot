## 如何部署 redbot

### 1. 环境要求

虽然 `redbot` 所依赖的 [`Ariadne`](https://github.com/GraiaProject/Ariadne) 框架目前要求的 Python 版本为 3.8 ~ 3.10

但 `redbot` 使用了 Python 3.10 的新特性因此仅能使用 Python 3.10.x 运行

### 2. 配置 Mirai

请参阅[Ariadne官方文档关于mah的配置方法](https://graia.readthedocs.io/appendix/mah-install/)

### 3. 安装 Poetry

> 注1：假设你不想用 `Poetry`，你可直接跳过  
> 注2：此处假设你已在你的计算机或服务器上安装好 Python 3.10

`redbot` 使用 `Poetry` 来管理项目依赖关系

#### Poetry 官方推荐的安装方法

##### macOS / Linux / BashOnWindows

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

##### Windows

> 注：请使用 Windows 8 以上版本的 Windows，并通过 `Windows Powershell` 而不是 `Powershell Core` 执行下面的命令

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

#### 通过 `pip` 来安装 `Poetry`

假如你没有通过科学的姿势连接网络，上面的命令也许会超时失败  
因此你也可以直接通过 `pip` 来安装 `Poetry`

> 注：在 Windows 上使用 pip 时请不要设置系统代理，请通过设置镜像源来提升 pip 的下载速度

##### macOS / Linux（此处假设你的 Python 3.10.x 版本的解释器是从源码通过 `make altinstall` 命令安装的）

```bash
python3.10 -m pip install poetry
```

##### Windows（请自行确保环境变量中的 Python 解释器版本符合要求）

```powershell
python -m pip install poetry
```

### 4. 克隆 redbot 到本地并进入项目目录中

```bash
git clone https://github.com/Graiax-Community/redbot.git
cd redbot
```

### 5. 创建虚拟环境并安装依赖

> 此处假设你所使用的 Python 版本为 3.10.1

```bash
poetry env use 3.10.1
poetry install
```

### 6. 启动 redbot

请不要将以下命令写入 `*.sh`、`*.bat`、`*.cmd`、`*.ps1` 等脚本中使用

```bash
poetry run python main.py
```

### 注意

首次启动之后会生成配置文件并退出，请在 bot 退出后填写配置文件

- 其中，数据库链接使用 uri 形式，填写格式如下
  - SQLite: `sqlite+aiosqlite:///data/database.db`，一般情况下只需更改 `database.db` 的 `database`，参考 👉 [sqlalchemy的文档](https://docs.sqlalchemy.org/en/14/dialects/sqlite.html?highlight=aiosqlite#aiosqlite)
  - MySQL / MariaDB: `mysql+asyncmy://{user}:{password}@{hostname}:{port}/{dbname}?charset=utf8mb4`，此为示例，具体参数请参考[sqlalchemy的文档](https://docs.sqlalchemy.org/en/14/dialects/mysql.html?highlight=aiomysql#asyncmy)

## 让 redbot 保持在后台运行

### Windows / macOS

~~不会吧不会吧，不会有人连最小化都不会吧~~

## Linux

### 安装 screen

#### CentOS 等 RPM 系

```bash
sudo yum install repl-release
sudo yum install screen
```

#### Ubuntu 等 dpkg 系

```bash
sudo apt update
sudo apt install screen
```

### 使用 screen

1. 创建一个 screen

   ```bash
   screen -S redbot
   ```

2. 将 screen 放到后台

   > 在 screen 内先按下 `ctrl + a` 组合键，再按下 `d` 键

3. 将后台的 screen 调出来

   ```bash
   screen -x redbot  # 回到名为 redbot 的 screen
   screen -x  # 回到最近用过的 screen
   screen -r  # 回到最近用过的 screen
   ```
