# adjust these for your plugin
plugincodename = "FansDBAssistant"
pluginhumanname = "FansDB Assistant URL"

# imports

import os
import sys
import json

try:
    import stashapi.log as log
    from stashapi.stashapp import StashInterface
    from stashapi.stashbox import StashBoxInterface
except ModuleNotFoundError:
    print("You need to install the stashapp-tools (stashapi) python module. (CLI: pip install stashapp-tools)", file=sys.stderr)
    sys.exit()

# plugins don't start in the right directory, let's switch to the local directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# logging functions

def exit_plugin(msg=None, err=None):
    if msg is None and err is None:
        msg = pluginhumanname + " plugin ended"
    output_json = {"output": msg, "error": err}
    print(json.dumps(output_json))
    sys.exit()

# useful functions

def get_ids(obj):
    ids = []
    for item in obj:
        ids.append(item['id'])
    return ids

def get_names(obj):
    names = []
    for item in obj:
        names.append(item['name'])
    return names

# migration functions
def checkTable(table):
  query = """
    mutation QuerySQL($sql: String!) {
        querySQL(sql: $sql) {
            rows
        }
    }
  """
  variables = {
    "sql": "SELECT COUNT(*) FROM %s WHERE endpoint = 'https://fansdb.xyz/graphql'" % table
  }
  res = stash._callGraphQL(query, variables)
  return res["querySQL"]["rows"][0][0]

def checkTables():
  for table in ["scene_stash_ids", "studio_stash_ids", "performer_stash_ids"]:
    table_name = table.split("_")[0]
    count = checkTable(table)
    log.info("Found %d FansDB.xyz URLs in %s" % (count, table_name))

def backup():
  query = """
  mutation backupDatabase {
      backupDatabase(input: { download: false })
  }
  """
  stash._callGraphQL(query)

def updateTable(table):
  query = """
    mutation ExecSQL($sql: String!) {
        execSQL(sql: $sql) {
            rows_affected
        }
    }
  """
  variables = {
    "sql": "UPDATE %s SET endpoint='https://fansdb.cc/graphql' WHERE endpoint='https://fansdb.xyz/graphql';" % table
  }
  res = stash._callGraphQL(query, variables)
  return res["execSQL"]["rows_affected"]

def updateTables():
  for table in ["scene_stash_ids", "studio_stash_ids", "performer_stash_ids"]:
    table_name = table.split("_")[0]
    count = updateTable(table)
    log.info("Replaced %d FansDB.xyz URLs in %s" % (count, table_name))

# add missing URL to local stash performer profile

def scrapeendpointforperformer(performer, stashid = ""):
    stashbox = StashBoxInterface(endpoint)

    if stashid:
       scraped = stashbox.find_performer(stashid)
       #log.debug(scraped)
       updating = {}
       updating["id"] = performer.get('id')
       if scraped:
          for thisurl in scraped["urls"]:
              if thisurl['type'] == "ONLYFANS":
                 updating["url"] = thisurl["url"]
       #log.debug(updating)
       result = stash.update_performer(updating)
       #log.debug(result)
       #getof_id = stash.find_tag(getof_tag, create=True).get('id')
       #stash.update_performers({
       #     'ids': [performer.get('id')],
       #     'tag_ids': {
       #         'mode': 'REMOVE',
       #         'ids': [getof_id]
       #     }
       #})
       return True
    # no stashid, we need to search harder:
    search = {}
    if performer.get("url"):
       search['url'] = performer.get("url")
    else:
       search['url'] = "https://onlyfans.com/" + performer.get("name")
    scraped = stashbox.find_performers(search)
    #log.debug(scraped)
    if scraped and len(scraped) == 1:
        updating = {}
        updating["id"] = performer['id']
        updating["url"] = search['url']
        if performer.get('stash_ids'):
           updating['stash_ids'] = performer.get('stash_ids')
        else:
           updating['stash_ids'] = []
        newid = {}
        newid['endpoint'] = endpoint['endpoint']
        newid['stash_id'] = scraped[0]['id']
        updating['stash_ids'].append(newid)

        #log.debug(updating)
        result = stash.update_performer(updating)
        #log.debug(result)
        query = """ mutation updateperformer($input: StashBoxBatchTagInput!) {stashBoxBatchPerformerTag(input: $input)}"""
        batch_input = {"endpoint": endpointindex,
                       "refresh": True,
                       "performer_ids": [performer['id']],
        	       "createParent": False,
        }
        result = stash._callGraphQL(query, {"input": batch_input})
        return True
    return False

# submit performers to fansdb

def submitperformer(performer):
    perfid = performer.get('id')
    query = """mutation submitPerformerToStashbox($input: StashBoxDraftSubmissionInput!) { submitStashBoxPerformerDraft(input: $input)}"""
    variables = { "input": { "id": perfid, "stash_box_index": endpointindex } }
    result = stash._callGraphQL(query, variables)
    #log.debug(result)
    log.info(f"Submitted {performer.get('name')} as a draft.")
    stash.update_performers({'ids': [perfid], 'tag_ids': {'mode': 'REMOVE', 'ids': [tosubmit_id] }})
    stash.update_performers({'ids': [perfid], 'tag_ids': {'mode': 'ADD', 'ids': [submitted_id] }})
    return

# call OnlyFans scraper silently

def scrape_of_performer(performer, url):
    scraped = stash.scrape_performer_url(url)
    #log.debug(scraped)
    updating = {}
    updating["id"] = performer.get('id')
    if scraped:
       updating['name'] = scraped.get('name')
       if updating['name'] is None:
           updating['name'] = performer.get('name')
       else:
           updating["disambiguation"] = performer.get('name')
       updating["url"] = scraped["url"]
       if performer.get('aliases'):
          updating["aliases"] = performer.get('aliases').append(scraped["aliases"])
       else:
          updating["aliases"] = scraped["aliases"]
       updating["details"] = scraped.get("details")
       if scraped.get("images"):
          updating["image"] = scraped.get("images")[0]
       log.info(f"OnlyFans account found - {updating['name']} - {updating['url']}")
       if scraped.get('career_length') == "No Posts No Media":
           updating['name'] = performer.get('name') + " - UNVERIFIED USER"
           log.info(f"Unverified OnlyFans account - flagging this")
    else:
       log.info(f"No OnlyFans account found for {performer.get('name')}")
       updating["disambiguation"] = "OnlyFans not found"
    #log.debug(updating)
    result = stash.update_performer(updating)
    #log.debug(result)
    return

# main code logic
def main():
    global stash

    json_input = json.loads(sys.stdin.read())
    #log.debug(json_input)
    FRAGMENT_SERVER = json_input["server_connection"]
    PLUGIN_ARGS = False
    HOOKCONTEXT = False

    global endpointindex
    global endpoint

    stash = StashInterface(FRAGMENT_SERVER)

    try:
        PLUGIN_ARGS = json_input['args']["mode"]
    except:
        pass

    if PLUGIN_ARGS:
        log.debug("--Starting " + pluginhumanname + " Plugin --")

        if PLUGIN_ARGS == "check":
           log.info("Checking for old fansdb.xyz stashids")
           checkTables()
           exit_plugin(f"{pluginhumanname} checked for old fansdb stashids and exited normally.")
        elif PLUGIN_ARGS == "migrate":
           log.info("Backing up DB for safety...")
           backup()
           log.info("Updating stashids from fansdb.xyz to fansdb.cc")
           updateTables()
           log.warning("If you haven't yet, change your FansDB endpoint url from fansdb.xyz to fansdb.cc!")
           exit_plugin(f"{pluginhumanname} migrated to new fansdb urls  and exited normally.")

        exit_plugin(pluginhumanname + " plugin finished")

    try:
        HOOKCONTEXT = json_input['args']["hookContext"]
    except:
        exit_plugin(pluginhumanname + ": No hook context")

    log.debug("--Starting Hook '"+ pluginhumanname + "' --")

    config = stash.get_configuration()
    allstashboxes = config['general']['stashBoxes']
    #log.debug(allstashboxes)

    for boxindex, box in enumerate(allstashboxes):
        if 'fansdb' in box.get('endpoint'):
           #log.debug(box)
           endpoint = box
           endpointindex = boxindex
    #log.debug(endpoint)

    global getof_tag, getof_id
    global getfansly_tag, getfansly_id

    getof_tag = "AddOFUrl"
    getfansly_tag = "AddFanslyUrl"
    getof_id = stash.find_tag(getof_tag, create=True).get('id')
    getfansly_id = stash.find_tag(getfansly_tag, create=True).get('id')

    global submitted_id, tosubmit_id
    submitted_id = stash.find_tag("SubmittedtoFansDB", create=True).get("id")
    tosubmit_id = stash.find_tag("SubmittoFansDB", create=True).get("id")

    # logic:

    # which hook?
    # for now, only on performer updates - creates can work, but needs more logic

    performerID = HOOKCONTEXT['id']
    performer = stash.find_performer(performerID)
    # log.debug(performer)
    url = performer.get('url')
    name = performer.get('name')
    disamb = performer.get('disambiguation')
    tags = get_names(performer.get('tags'))
    stashids = performer.get('stash_ids')

    # do we have a stash id?
    stashid = ""
    for ends in stashids:
        if 'fansdb' in ends.get('endpoint'):
           stashid = ends.get("stash_id")
    # log.debug(stashid)

    if stashid and not url:
       # we have a stashid, but no url, so trust fansdb for getting that info:
       scrapeendpointforperformer(performer, stashid)
       exit_plugin(f"{pluginhumanname} scraped fansdb and exited normally.")

    if stashid:
       # we have a stashid and a url:
       exit_plugin(f"{pluginhumanname} - no action required and exiting normally.")

    # no stashid
    if url:
       # we have no stashid but we have a url
       # since we have a url, we're probably good to check if it exists in fansdb already:
       result = scrapeendpointforperformer(performer)
       if not result and "SubmittoFansDB" in tags:
          # we've been asked to submit the performer to fansdb, and it's not there yet.
          submitperformer(performer)
       exit_plugin(f"{pluginhumanname} - exiting normally")

    # no url
    # so we have no stashid and no url
    if " " not in name and not disamb:
         # the name has no space, so it's likely a username:
         # first let's try a scrape from fansdb
         result = scrapeendpointforperformer(performer)
         if not result:
            # not found on FansDB, is it OF?  Scraper?
            url = "https://onlyfans.com/" + name
            scrape_of_performer(performer, url)
         exit_plugin(f"{pluginhumanname} - exiting normally")

    exit_plugin(pluginhumanname + " hook completed")

# calls main logic
main()

# by Scruffy  [fansdb migration code by feederbox826]
# Last Updated 2023-11-21
