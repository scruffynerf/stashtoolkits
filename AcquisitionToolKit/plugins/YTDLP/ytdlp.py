import os
import sys
import json

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

if not os.path.exists(config.urls_file):
   with open(config.urls_file, 'w') as firstrun:
     firstrun.write("")
if not os.path.exists(config.grabbed_urls_txt):
   with open(config.grabbed_urls_txt, 'w') as firstrun:
     firstrun.write("")
if not os.path.exists(config.error_urls_txt):
   with open(config.error_urls_txt, 'w') as firstrun:
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

    global stash
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
    tag_scene(scene)
    output["output"] = "ok"
    return


def tag_scene(scene):
    if scene.get('urls') != []:
       log.debug(f"already has URL - skipping")
       return
    locations = scene.get("files")
    jsonfile = ""
    for location in locations:
       path = location['path']
       jsonpath = os.path.splitext(path)[0] + '.json'
       if os.path.exists(jsonpath):
          jsonfile = jsonpath
          log.debug(jsonpath)
    if jsonfile == "":
       log.debug(f"No json found - skipping")
       return
    with open(jsonfile, 'r') as videoinfo:
         video = json.load(videoinfo)

    ## currently optimized for PH, could be adjusted for other sites' json
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

    stash.update_scenes(scene_data)

    #time to add thumbnail
    update = {}
    update['id'] = scene.get('id')
    update['cover_image'] = video.get('thumbnail')
    stash.update_scene(update)

def read_urls_and_download(stash):
    if config.urls_type == "text":
        with open(config.urls_file, 'r') as url_file:
            urls = url_file.readlines()
    elif config.urls_type == "json":
        with open(config.urls_file, 'r') as url_file:
            urls = json.load(url_file)
    else:
        log.error(f"You need to configure the config.py with your url filename and type")
        sys.exit()

    with open(config.grabbed_urls_txt, 'r') as url_file:
        grabbed_urls = url_file.read()
    with open(config.error_urls_txt, 'r') as url_file:
        error_urls = url_file.read()
    
    total = len(urls)
    if total > config.batchsize:
       total = config.batchsize
    i = -1
    
    for url in urls:
        if config.urls_type == "text":
            this_url = url.strip()
        elif config.urls_type == "json":
            this_url = url.get(config.url_json_urlname)    

        if this_url in grabbed_urls:
            log.debug(f"Already grabbed {this_url}")
            continue
        if this_url in error_urls:
            log.debug(f"Already had an error with {this_url}")
            continue
        if not check_url_valid(this_url):
            log.error(f"Bad URL: {this_url}")
            with open(config.error_urls_txt, 'a') as url_file:
                  url_file.write(this_url+"\n")
            continue
        i += 1
        if i >= config.batchsize:
            stash.metadata_scan(paths=[config.download_dir])
            stash.run_plugin_task("ytdlp", "Download Videos", args={"mode": "download"})
            return
        log.progress(i/total)
        fileid = download(this_url)
        if fileid == 0:
            log.error(f"Problem downloading {this_url}")
            i += -1
            continue
    stash.metadata_scan(paths=[config.download_dir])
    return

def check_url_valid(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None

def download(url):
    ytdl_options = config.ytdl_options
    download_dir = config.download_dir.rstrip("/") + "/"
    log.info("Downloading " + url + " to: " + download_dir)

    ydl = yt_dlp.YoutubeDL({
        'outtmpl': download_dir + '%(id)s.%(ext)s',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        **ytdl_options,
    })

    meta = {}
    with ydl:
        try:
            info = ydl.extract_info(url=url, download=True)
            #ydl.sanitize_info makes the info json-serializable
            meta = ydl.sanitize_info(info)
            log.debug(f"File {meta.get('id')} - Download finished!")
        except Exception as e:
            if "Error 404" in str(e) or "This video has been disabled" in str(e):
               with open(config.error_urls_txt, 'a') as url_file:
                  url_file.write(url+"\n")
               return 0
            log.warning(str(e))

    # save the metadata, so we can read it on create/scan
    if meta.get('id') and not os.path.exists(download_dir + meta.get('id') + '.json'):
       with open(download_dir + meta.get('id') + '.json', 'w') as outfile:
          json.dump(meta, outfile)
       with open(config.grabbed_urls_txt, 'a') as url_file:
          url_file.write(url+"\n")
       return meta.get('id')
    log.debug(f"No ID found for this video, problem likely, so no json saved")
    return 0

main()
