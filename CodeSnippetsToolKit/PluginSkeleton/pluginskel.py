global plugincodename, pluginhumanname

# Adjust these for your plugin, the name of the plugin's .yml and the Human readable name of your plugin
plugincodename = "pluginskel"
pluginhumanname = "Plugin Skeleton"

# imports
import os
import sys
import json

# plugins don't start in the right directory, let's switch to the local directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# we use the python StashAPI library because it just makes it all so much easier
try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (CLI: pip install stashapp-tools)", file=sys.stderr)

# Configuration/settings file... because not everything can be easily built/controlled via the UI plugin settings
# If you don't need this level of configuration, just define the default_settings here directly in code, 
#    and you can remove the _defaults.py file and the below code
if not os.path.exists("config.py"):
    with open(plugincodename + "_defaults.py", 'r') as default:
        config_lines = default.readlines()
    with open("config.py", 'w') as firstrun:
        firstrun.write("from " + plugincodename + "_defaults import *\n")
        for line in config_lines:
            if not line.startswith("##"):
                firstrun.write(f"#{line}")
import config
global default_settings
default_settings = config.default_settings

# Optional but useful utilities - Not used by default but here for the ease of development

def configfile_edit(configfile, name: str, state: str):
    # you can write back to the user's config.py here, adding or updating items
    # alternatively: you can update the settings in the Plugin UI using stash.configure_plugin()
    found = 0
    with open(configfile, 'r') as file:
        config_lines = file.readlines()
    with open(configfile, 'w') as file_w:
        for line in config_lines:
            if name == line.split("=")[0].strip():
                file_w.write(f"{name} = {state}\n")
                found += 1
            elif "#" + name == line.split("=")[0].strip():
                file_w.write(f"{name} = {state}\n")
                found += 1
            else:
                file_w.write(line)
        if not found:
            file_w.write(f"#\n{name} = {state}\n")
            found = 1
    return found

def get_ids(obj):
    # sometimes you just want the ids
    ids = []
    if isinstance(obj, dict):
       for item in obj:
           ids.append(item['id'])
    return ids

def get_names(obj):
    # sometimes you just want the names
    names = []
    if isinstance(obj, dict):
       for item in obj:
           names.append(item['name'])
    return names

# logging function(s)

def exit_plugin(msg=None, err=None):
    if msg is None and err is None:
        msg = pluginhumanname + " plugin ended"
    output_json = {"output": msg, "error": err}
    log.debug(f"{msg}")
    log.debug(f"{err}")
    print(json.dumps(output_json))
    sys.exit()

# your hook and task and other functions will go here

def nameofyourcodeloop1torun():
    log.info(f"{pluginhumanname} Button 1")
    return

def nameofyourcodeloop2torun():
    log.info(f"{pluginhumanname} Button 2")
    return

def hookcode1(scene):
    log.info(f"{pluginhumanname} Hook - {scene['title']}")
    return

# main code
def main():
    global stash, settings
    json_input = json.loads(sys.stdin.read())
    FRAGMENT_SERVER = json_input["server_connection"]
    #log.debug(FRAGMENT_SERVER)

    stash = StashInterface(FRAGMENT_SERVER)

    settings = stash.find_plugin_config(plugincodename, default_settings)
    #log.debug(settings)

    PLUGIN_ARGS = False
    HOOKCONTEXT = False

    # Task Button handling
    try:
        PLUGIN_ARGS = json_input['args']["mode"]
    except:
        pass

    if PLUGIN_ARGS:
        log.debug("--Starting " + pluginhumanname + " Plugin --")

        if "task1codetorun" in PLUGIN_ARGS:
            log.debug("running task1codetorun")
            nameofyourcodeloop1torun()

        if "task2codetorun" in PLUGIN_ARGS:
            log.debug("running task1codetorun")
            nameofyourcodeloop2torun()

        exit_plugin(pluginhumanname + " plugin finished")

    # Hook handling

    try:
        HOOKCONTEXT = json_input['args']["hookContext"]
    except:
        exit_plugin(pluginhumanname + " hooks: No hook context")

    log.debug("--Starting " + pluginhumanname + "Hooks --")
    log.debug(HOOKCONTEXT)

    #put your result msg, if any,  in this
    results = {}

    # potentially, you could handle multiple different hook types here, using logic to decide what to do...
    # simple example logic - we only get called on hook scene update
    # for a scene, get the scene id, load the scene...

    sceneID = HOOKCONTEXT['id']
    scene = stash.find_scene(sceneID)

    # your custom plugin logic/code would go here
    results = hookcode1(scene)

    # print/log the results and exit cleanly
    exit_plugin(results)

# final: call main loop
main()
