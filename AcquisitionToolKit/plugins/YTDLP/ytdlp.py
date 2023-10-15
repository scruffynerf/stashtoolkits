import pathlib
import re
import sys
import json
import os
import shutil

# plugins don't start in the right directory, let's switch to the local directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (CLI: pip install stashapp-tools)", file=sys.stderr)

try:
    import yt_dlp
except ModuleNotFoundError:
    print("You need to install the Youtube Downloader (yt-dlp) python module. (CLI: pip install ytdlp)", file=sys.stderr)

# configuration/settings
if not os.path.exists("config.py"):
    with open("ytdlp_defaults.py", 'r') as default:
        config_lines = default.readlines()
    with open("config.py", 'w') as firstrun:
        firstrun.write("from ytdlp_defaults import *\n")
        for line in config_lines:
            if not line.startswith("##"):
                firstrun.write(f"#{line}")
    log.warning(f"Config file config.py was created, you probably need to edit it now...")
    sys.exit()

import config

if not os.path.exists(config.urls_txt):
   with open(config.urls_txt, 'w') as firstrun:
     firstrun.write("")
if not os.path.exists(config.grabbed_urls_txt):
   with open(config.grabbed_urls_txt, 'w') as firstrun:
     firstrun.write("")

def main():
    json_input = read_json_input()
    output = {}
    run(json_input, output)
    out = json.dumps(output)
    print(out + "\n")

def read_json_input():
    json_input = sys.stdin.read()
    return json.loads(json_input)

def run(json_input, output):
    PLUGIN_ARGS = False
    HOOKCONTEXT = False

    try:
        stash = StashInterface(json_input["server_connection"])
    except Exception:
        raise

    try:
        PLUGIN_ARGS = json_input['args']["mode"]
    except:
        pass
    if PLUGIN_ARGS == "download":
            read_urls_and_download(stash)
            stash.metadata_scan(paths=[config.download_dir])
            output["output"] = "ok"
            return

    try:
        HOOKCONTEXT = json_input['args']["hookContext"]
    except:
        output["output"] = "ok"
        return

    log.debug("--Starting YTDLP Hooks --")
    sceneID = HOOKCONTEXT['id']
    scene = stash.find_scene(sceneID)
    tag_scene(scene, stash)
    output["output"] = "ok"
    return


def tag_scene(scene, stash):
    downloaded = False
    if not os.path.isfile(config.downloaded_json) and not os.path.isfile(config.downloaded_backup_json):
       return
    if not os.path.isfile(config.downloaded_json) and os.path.isfile(config.downloaded_backup_json):
        shutil.copyfile(config.downloaded_backup_json, config.downloaded_json)
    locations = scene.get("files")
    for location in locations:
        if config.download_dir in location['path']:
           downloaded = True
    if downloaded == False:
       log.debug(f"Not a Download - skipping")
       return
    if scene.get('urls') != []:
       log.debug(f"already has URL - skipping")
       return
    with open(config.downloaded_json) as json_file:
        data = json.load(json_file)
        basename = scene.get('files')[0]['basename']
        filename = os.path.splitext(basename)[0]
        found_video = None
        for video in data:
            if video['id'] in filename:
               found_video = video
               break
        if found_video is not None:
                  ## currently optimized for PH, could be adjusted for other sites
                  scene_data = {
                    'ids': [scene.get('id')],
                    'url': video['webpage_url'],
                    'title': video['fulltitle']
                  }

                  tag_ids = []
                  if video.get('tags') is not None:
                    for tag in video.get('tags'):
                        tag_id = stash.find_tag(tag, create=True)
                        tag_ids.append(tag_id.get('id'))
                  if video.get('categories') is not None:
                    for tag in video.get('categories'):
                        tag_id = stash.find_tag(tag, create=True)
                        tag_ids.append(tag_id.get('id'))
                  if tag_ids:
                     scene_data['tag_ids'] = { "ids": tag_ids, "mode": "ADD" }

                  performer_ids = []
                  if video.get('cast') is not None:
                    for performer in video.get('cast'):
                        performer_ids.append(stash.find_performer(performer, create=True).get('id'))
                    scene_data['performer_ids'] = { "ids": performer_ids, "mode": "ADD" }

                  if video.get('uploader') is not None:
                    scene_data['studio_id'] = stash.find_studio(video.get('uploader'), create=True).get('id')

                  if video.get('upload_date') is not None:
                    scene_data['date'] = video.get('upload_date')[0:4] + "-" + video.get('upload_date')[4:6] + "-" + video.get('upload_date')[6:8]
                    log.debug(scene_data['date'])

                  stash.update_scenes(scene_data)

                  #time to add thumbnail
                  update = {}
                  update['id'] = scene.get('id')
                  update['cover_image'] = video.get('thumbnail')
                  stash.update_scene(update)

def read_urls_and_download(stash):
    with open(config.urls_txt, 'r') as url_file:
        urls = url_file.readlines()
    with open(config.grabbed_urls_txt, 'r') as url_file:
        grabbed_urls = url_file.read()
    downloaded = []
    total = len(urls)
    i = -1
    for url in urls:
        i += 1
        log.progress(i/total)
        this_url = url.strip()
        if this_url in grabbed_urls:
            log.debug(f"Already grabbed {this_url}")
        elif check_url_valid(this_url):
            download(this_url, downloaded)
            with open(config.grabbed_urls_txt, 'a') as url_file:
                url_file.write(this_url+"\n")
    if os.path.isfile(config.downloaded_json):
        shutil.move(config.downloaded_json, config.downloaded_backup_json)
    with open(config.downloaded_json, 'w') as outfile:
        json.dump(downloaded, outfile)

def check_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None

def download(url, downloaded):
    ytdl_options = config.ytdl_options
    download_dir = config.download_dir.rstrip("/") + "/"
    log.debug("Downloading " + url + " to: " + download_dir)

    ydl = yt_dlp.YoutubeDL({
        'outtmpl': download_dir + '%(id)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        **ytdl_options,
    })

    with ydl:
        try:
            info = ydl.extract_info(url=url, download=True)
            #ydl.sanitize_info makes the info json-serializable
            meta = ydl.sanitize_info(info)
            log.debug(meta['id'])
            log.debug("Download finished!")
            downloaded.append(meta)
        except Exception as e:
            log.warning(str(e))

main()
