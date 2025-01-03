from time import sleep
from os import path
from re import sub as sub
from subprocess import CalledProcessError, run as subprocess_run
from asyncio import run as asyncio_run
from toml import load
from bilibili_api import Credential,video,favorite_list,settings,sync
from load_data import SQLiteManager

# 读取配置文件
with open(path.expanduser("~/.config/bili-sync/config.toml"), 'r', encoding='utf-8') as f:
    bili_sync_config = load(f)
# 收藏夹的id列表
media_id_list = list(bili_sync_config['favorite_list'].keys())
credential = Credential(sessdata=bili_sync_config['credential']['sessdata'], bili_jct=bili_sync_config['credential']['bili_jct'], dedeuserid=bili_sync_config['credential']['dedeuserid'], ac_time_value=bili_sync_config['credential']['ac_time_value'])
sessdata = bili_sync_config['credential']['sessdata']
# 需要下载的视频
need_download_bvids = dict()

# 自动刷新cookie
def refresh_cookie():
    if(sync(credential.check_refresh())):
        print(f"[info] 发现cookie过期，正在刷新")
        sync(credential.refresh())
        bili_sync_config['credential']['sessdata'] = credential.sessdata
        bili_sync_config['credential']['bili_jct'] = credential.bili_jct
        bili_sync_config['credential']['dedeuserid'] = credential.dedeuserid
        bili_sync_config['credential']['ac_time_value'] = credential.ac_time_value
        save_cookies_to_txt()

async def get_bvids(media_id):
    """
    获取收藏夹下面的所有视频bvid，如果有未下载的新视频会更新字典

    :param media_id: 收藏夹id
    """
    # 实例化 FavoriteList 类，用于获取指定收藏夹信息
    fav_list = favorite_list.FavoriteList(media_id = media_id,credential = credential)
    try:
        ids = await fav_list.get_content_ids_info()
    except Exception as e:
        print(f"发生错误: {e}，下一次同步时重试")
        return
    for id in ids:
        # 未下载的新视频更新字典
        if id['bvid'] not in already_download_bvids(media_id).copy():
            need_download_bvids[media_id].add(id['bvid'])

async def get_video_info(media_id,bvid):
    """
    获取视频信息。

    :param media_id: 收藏夹id
    :param bvid: 视频bvid

    Returns:
        dict: title的值为视频标题，pages为视频分p信息，如果pages的长度大于1表示存在多分p
    """
    # 实例化 Video 类，用于获取指定视频信息
    v = video.Video(bvid=bvid, credential=credential)
    # 获取视频信息
    info = dict()
    try:
        info['title'] = (await v.get_info())['title']
        info['upname'] = ((await v.get_info())['owner'])['name']
    except Exception:
        # 失效的视频添加到已经下载集合
        already_download_bvids_add(media_id=media_id,bvid=bvid)
        print(bvid+"视频失效")
    return info

def download_video(media_id,bvid,video_dir):
    """
    使用 yutto 下载视频。
    :param media_id: 收藏夹的id
    :param bvid: 视频的bvid
    :param video_dir: 存放视频的文件夹路径
    """
    command = [
        "yutto",
        bvid, 
        "-b", 
        "-c", sessdata, 
        "-d", video_dir, 
        "-tp", "{name}", 
        "--with-metadata", 
        "--vip-strict", 
        "--login-strict", 
        "--download-interval", 
        "30",
        "--banned-mirrors-pattern",
        "mirrorali",
        "-n", 
        "1"
    ]
    try:
        subprocess_run(command, check=True)
        # 下载成功，更新字典数据
        already_download_bvids_add(media_id=media_id,bvid=bvid)
        print(f"[info] {video_dir} 视频下载成功")
    except CalledProcessError:
        print(f"[error] {video_dir} 视频下载失败")

# 数据库读取已经下载的视频bvids
def already_download_bvids(media_id):
    with SQLiteManager(path.expanduser("~/.config/bili-sync/data.sqlite3")) as db_manager:
        return db_manager.get_values(table_name=media_id)

# 数据库添加下载成功的视频
def already_download_bvids_add(media_id,bvid):
    with SQLiteManager(path.expanduser("~/.config/bili-sync/data.sqlite3")) as db_manager:
        db_manager.insert_data(table_name=media_id,value=bvid)

# 初始化
def init_download():
    # 根据收藏夹id初始化字典数据
    for media_id in media_id_list:
        need_download_bvids.setdefault(media_id, set())

# 间隔指定时间检查收藏夹是否更新并下载
def check_updates_download():
    while True:
        refresh_cookie() # 检测是否需要刷新cookie
        for media_id in media_id_list:
            # 根据收藏夹id读取配置文件中的保存路径
            download_path = bili_sync_config['favorite_list'][media_id]
            # 获取收藏夹中未下载的视频的bvid
            asyncio_run(get_bvids(media_id))
            # 获取未失效的视频信息并下载
            for bvid in need_download_bvids[media_id].copy(): 
            # 遍历的时候使用copy()方法创建副本，这样即使在迭代过程中修改了原集合，也不会影响到迭代器
                video_info = asyncio_run(get_video_info(media_id,bvid)) # 获取视频信息
                yutto -v
                if len(video_info)>0: # 仅下载可以获取到信息的视频
                    upname = video_info["upname"]
                    videotitle = video_info["title"]
                    video_dir = path.join(download_path, upname, videotitle.replace(':', '-').replace('|', '♥️').replace('"', '⚡').replace('/', '_').replace('<', '-').replace('>', '-').replace('?', '.').replace('*', '♥️'))
                    sleep(2)
                    download_video(media_id,bvid,video_dir)
                    print(f"[info] {"30"}秒后下载下一个视频")
                    sleep(28)
            # 对比已经下载的数据批量更新需要下载的数据
            for bvid in already_download_bvids(media_id):
                try: # 如果need_download_bvids不存在该bvid表示已经更新过数据，直接跳过
                    need_download_bvids[media_id].remove(bvid)
                except KeyError:
                    pass
        print(f"[info] {5}分钟后更新并同步收藏夹")
        sleep(300)

if __name__ == "__main__":
    init_download() # 第一次运行同步本地已经下载的视频信息
    check_updates_download() # 后续只下载收藏夹新增视频和之前下载失败的视频
