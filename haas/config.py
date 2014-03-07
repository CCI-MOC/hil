import ConfigParser

cfg = ConfigParser.RawConfigParser()

def load():
    cfg.read('haas.cfg')
