import json
import sys
import os

'''  This scraper adds a URL by looking up the filename from a file'''

# since all we need right now is a simple scene load, not replaced with stashapi (yet)
# if you put this into a subdirectory of scrapers, and pycommon is in scraper
sys.path.insert(0,'..')

from config import stashconfig, datafile, separator, splitorder, scrapeafter

try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    log.error("You need to install the stashapp-tools (stashapi) python module. (cmd): pip install stashapp-tools", file=sys.stderr)
    sys.exit()

log.info(f"Reading from {datafile}, using {separator} to split and taking the {splitorder}th item")

def lookupurl(scene):
    basename = os.path.basename(scene['files'][0]['path'])
    #log.debug(basename)
    with open(datafile, 'r') as fp:
      for l_no, line in enumerate(fp):
        # search string
        if basename in line:
            #log.debug(f"found: {line}")
            url = line.split(separator)[splitorder]
            #log.debug(f"url: {url}")
            return url
    return


# define stash globally
stash = StashInterface(stashconfig)
FRAGMENT = json.loads(sys.stdin.read())
SCENE_ID = FRAGMENT.get("id")
scene = stash.find_scene(SCENE_ID)
#log.debug(scene)
results = {}
results["url"] = lookupurl(scene)
if scrapeafter:
   results = stash.scrape_scene_url(results["url"])
#log.debug(results)
print(json.dumps(results))
# Last Updated Nov 24, 2023
