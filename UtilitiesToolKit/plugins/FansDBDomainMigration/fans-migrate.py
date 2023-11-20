import json
import sys
import stashapi.log as log
from stashapi.stashapp import StashInterface

FRAGMENT = json.loads(sys.stdin.read())
MODE = FRAGMENT['args']['mode']
stash = StashInterface(FRAGMENT["server_connection"])

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

def backup():
  query = """
  mutation backupDatabase {
      backupDatabase(input: { download: false })
  }
  """
  stash._callGraphQL(query)

def main():
  if MODE == "check":
    checkTables()
  elif MODE == "migrate":
    backup()
    updateTables()
  log.exit("Plugin exited normally.")

if __name__ == '__main__':
  main()
