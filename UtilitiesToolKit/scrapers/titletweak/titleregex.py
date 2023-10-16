import json
import sys
import os
import re
from itertools import islice

'''  This scraper adjusts titles by regex, configured by the user '''

# since all we need right now is a simple scene load, not replaced with stashapi (yet)
# if you put this into a subdirectory of scrapers, and pycommon is in scraper
sys.path.insert(0,'..')

try:
    import py_common.graphql as graphql
    import py_common.log as log
except ModuleNotFoundError:
    print("You need to download the folder 'py_common' from the community repo! (CommunityScrapers/tree/master/scrapers/py_common)", file=sys.stderr)
    sys.exit()

# configuration/settings
if not os.path.exists("config.py"):
    with open("titleregex_defaults.py", 'r') as default:
        config_lines = default.readlines()
    with open("config.py", 'w') as firstrun:
        firstrun.write("from titleregex_defaults import *\n")
        for line in config_lines:
            if not line.startswith("##"):
                firstrun.write(f"#{line}")
    print("FIRST RUN - Created the config file for you to edit and change as desired", file=sys.stderr)
    sys.exit()

import config

# complex but speedy setup for multiple regexes
# to call:  results = ReplWrapper(REPL_DICT).multiple_replace(ORIGINAL_STRING)

class ReplWrapper:
    def __init__(self, repl_dict):
        self.repl_dict = repl_dict
        self.groups_no = [re.compile(pattern).groups for pattern in repl_dict]
        self.full_pattern = '|'.join(f'({pattern})' for pattern in repl_dict)

    def get_pattern_repl(self, pos):
        return next(islice(self.repl_dict.items(), pos, pos + 1))

    def multiple_replace(self, s):
        def repl_func(m):
            all_groups = m.groups()

            # Use 'i' as the index within 'all_groups' and 'j' as the main
            # group index.
            i, j = 0, 0

            while i < len(all_groups) and all_groups[i] is None:
                # Skip the inner groups and move on to the next group.
                i += (self.groups_no[j] + 1)

                # Advance the main group index.
                j += 1

            return re.sub(*self.get_pattern_repl(j), all_groups[i])

        return re.sub(self.full_pattern, repl_func, s)

def tweak_title(scene):
    log.debug(scene)
    newtitle = scene['title']
    # handle empty title by using filename
    if newtitle == '':
       newtitle = os.path.basename(scene['path'])
    titlefinal = ReplWrapper(config.regex_dict).multiple_replace(newtitle)
    return titlefinal.strip()

FRAGMENT = json.loads(sys.stdin.read())
SCENE_ID = FRAGMENT.get("id")
scene = graphql.getScene(SCENE_ID)
results = {}
results["title"] = tweak_title(scene)
log.debug(results)
print(json.dumps(results))
# Last Updated Oct 15, 2023
