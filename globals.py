import json
import esp

# Returns public config
def dumpconf(config):

    return json.dumps(readConf()[0])

# Disables esp debug
def no_debug():

    esp.osdebug(None)

def readConf():
    # Load config file. Put secrets in separate variable
    configFile = open('config.json', 'r')
    config = json.loads(configFile.read().replace('\n', ''))
    secrets = config["private"]
    config = config["public"]
    configFile.close()
    return (config, secrets)

# While this variable is true redraw thread runs. Thread terminates once it is false
redraw_active = True

# Variable used to adjust delay of each frame
frameTime = 0
