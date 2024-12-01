本项目是基于[cap153/bili-sync-yt-dlp](https://github.com/cap153/bili-sync-yt-dlp)项目的修改，将程序中调用的下载视频工具[yt-dlp](https://github.com/yt-dlp/yt-dlp)更换为[yutto](https://github.com/yutto-dev/yutto)。


> 首次运行时，程序会扫描目录，并记录成功下载和现存的视频信息到`data.sqlite3`数据库文件中。该文件与配置文件存放于同一目录。
> 若需重新扫描并记录所有视频，删除 data.sqlite3 文件后重新运行程序即可。

# 安装

目前只打包了 Linux/amd64 平台的 Docker镜像，其他平台如需使用Docker运行请[自行编译](#Dockerfile编译运行)，
DockerCompose示例：

```yml
services:
  bili-sync-yutto:
    image: suyiyi/bili-sync-yutto:latest #镜像地址
    hostname: bili-sync-yutto #主机名
    container_name: bili-sync-yutto #容器名
    restart: unless-stopped #重启策略
    network_mode: host #网络模式
    environment:
      - TZ=Asia/Shanghai #时区
    volumes:
      - ${配置文件保存位置}:/app/.config/bili-sync #配置文件挂载
      # 下面挂载的目录数量不限，根据你的需求填写
      - ${视频保存位置}:<容器内保存的路径>
      - ${视频保存位置}:<容器内保存的路径>
      # 这里的容器内保存的路径 务必完全按照你的配置文件内设置的挂载，<容器内保存的路径>请参照下面配置文件内填写；
      # 这些目录不是固定的，只需要确保此处的挂载与 bili-sync-yutto 的配置文件相匹配，
      # 这样才能将视频同步到你指定的目录，特指：${视频保存位置}.
```

# 配置文件

当前版本的默认示例文件如下：

在运行程序前务必创建并配置好 配置文件，而且要放到正确的存储位置上，特指你在DockerCompose中 `{配置文件保存位置}`

```toml
#你的bilibili账号 Cookie
sessdata = ""

#需要同步的收藏夹
[favorite_list]
<收藏夹id> = "<容器内保存的路径>"
<收藏夹id> = "<容器内保存的路径>"
```

- `credential`:哔哩哔哩账号的身份凭据，请参考凭据获取[流程获取](https://nemo2011.github.io/bilibili-api/#/get-credential)并对应填写至配置文件中，后续 bili-sync 会在必要时自动刷新身份凭据，不再需要手动管理。推荐使用匿名窗口获取，避免潜在的冲突。
- `favorite_list`:你想要下载的收藏夹与想要保存的位置。简单示例：

- `<收藏夹id> = "<容器内保存的路径>"`:视频会保存在容器内部的路径
举例：
```bash
[favorite_list]
3115878158 = "/bili-sync/测试收藏夹"
```
程序会对 ID为3115878158的收藏夹进行扫描，没有下载的视频将会下载到 容器内 "/bili-sync/测试收藏夹"目录下。
如果我想要将这个收藏夹的视频存储到容器外的指定位置，则需要在DockerCompose中挂载相应的目录。
举例：

```bash
    volumes:
     - /vol2/1000/Media:/bili-sync/测试收藏夹
```
这样就可以将 

`程序对 ID为3115878158的收藏夹进行扫描后，下载到 容器内 "/bili-sync/测试收藏夹"目录 的视频存储到容器外 /vol2/1000/Media 目录。`

<保存的路径>  和 ${还需要有视频下载位置} 可以根据自己的情况和习惯调整，没有特定要求



# 收藏夹id获取方法

[什么值得买的文章有详细介绍](https://post.smzdm.com/p/a4xl63gk/)，打开收藏夹

![image](https://github.com/user-attachments/assets/02efefe9-0a3a-46d6-8646-a6aa462d62c2)

浏览器可以看到“mlxxxxxxx”，只需要后面数字即可（不需要“ml“）

![image](https://github.com/user-attachments/assets/270c7f2f-b1b1-49a1-a450-a133f0d459fa)

# 目录结构

```bash
├── {video_name}
│   ├── {video_name} {page_name}.mp4
│   ├── {video_name} {page_name}.jpg
│   ├── {video_name} {page_name}.mp4
│   └── {video_name} {page_name}.jpg
```

# Dockerfile编译运行

```bash
# 下载最新源码
git clone --depth 1 https://github.com/suyiyi/bili-sync-yutto
# 进入项目目录
cd bili-sync-yutto
# 构建docker镜像
docker build -t bili-sync-yutto ./
# 创建容器并运行，自行修改相关参数
docker run -it --restart=always --name bili-sync-yutto  -v <配置文件路径>:/app/.config/bili-sync -v <视频保存位置>:<容器内保存的路径> bili-sync-yutto
```

# 源码运行

1. 安装[ffmpeg](https://www.ffmpeg.org/)并配置环境变量；
2. 安装[yutto](https://github.com/yutto-dev/yutto)并配置环境变量；
3. 安装python环境，本项目使用python3.12，其他版本不保证其兼容性；
4. 配置文件请放在如下路径`~/.config/bili-sync/config.toml` # Windows系统环境下的配置文件一般存放在C:\Users\<Your User ID>\.config\bili-sync 目录下
5. 命令行运行（Git，CMD都可以）

```bash
git clone --depth 1 https://github.com/suyiyi/bili-sync-yutto
# 进入项目目录
cd bili-sync-yutto
# 安装依赖
pip install -r requirements.txt
# 运行代码
python main.py
```


