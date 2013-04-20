import ConfigParser

class config_class():
    def __init__(self):
        pass
    def load_config(self, loc=''):
        self.config = {}
        self.config.update(self.load_settings(loc))
        
    def load_settings(self, loc=''):
        settings = {}
        if loc == '':
            loc = self.cfg_file
            
        cp_config = ConfigParser.ConfigParser()
        
        fail = cp_config.read(loc)

        if fail == loc:
            return {}  #No files read successfully

        try:
            for sect in cp_config.sections():
                settings[sect] = {}
                for opt in cp_config.options(sect):
                    settings[sect][opt] = cp_config.get(sect, opt)
        except ConfigParser.NoSectionError:
            return {}  #No section. OK.

        return settings

    def get_bool(self, val):
        if type(val) == bool:
            return val
        if val == '':
            return False
        if val[0].upper() in ['1', 'T', 'Y']:
            return True
        else:
            return False
