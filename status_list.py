class status_list():
    def __init__(self, bot, title):
        self.bot = bot
        self.title = title
        self.user = {}
        self.order = []
        self.count = 0

        self.list = ['order']
        self.dict = ['user']

    def add(self, name='', data=[], **kwargs):
        if kwargs != {}:
            for k, v in kwargs:
                setattr(self, k, v)
                self.remember(name, type(v))

        if name != '':
            setattr(self, name, data)
            self.remember(name, type(data))

    def remember(self, name, kind):
        if kind == list:
            self.lists.append(name)
        else:
            self.dict.append(name)

    def add_persistent(self, name='', data=[], **kwargs):
        if kwargs != {}:
            for k, v in kwargs:
                setattr(self, k, v)
        if name != '':
            setattr(self, name, data)

    def add_user(self, name, data, idx=-1):
        if idx == -1:
            self.order.append(name)
        else:
            self.order.insert(idx, name)
        
        self.user[name] = data
        self.count += 1

        self.bot.events.call('bot', 'list', self.title, 'add',
                             [name, self.user[name]])

    def del_user(self, name):
        try:
            old = self.user[name]
        except KeyError:
            old = None

        for k in self.list:
            try:
                del self.__dict__[k][self.__dict__[k].index(name.lower())]
            except IndexError:
                pass
            
        for k in self.dict:
            try:
                del self.__dict__[k][name]
            except KeyError:
                pass

        self.count -= 1

        self.bot.events.call('bot', 'list', self.title, 'remove',
                             [name, old])

    def clear(self):
        for k in self.list:
            self.__dict__[k] = []
            
        for k in self.dict:
            self.__dict__[k] = {}

        self.count = 0
        self.bot.events.call('bot', 'list', self.title, 'clear')

    def user_from_idx(self, idx):
        return self.user[self.order[idx]]

    def name_from_idx(self, idx):
        return self.user[self.order[idx]]['username']

    def has_user(self, name):
        try:
            self.order.index(name.lower())
        except:
            return False
        
        return True

class cookie_handler():
    def __init__(self):
        self.clear()
    def add(self, args):
        self.count += 1
        self.jar[self.count] = args

        return self.count
    def pop(self, idx):
        ret = self.jar[idx]
        del self.jar[idx]
        return ret
    def clear(self):
        self.jar = {}
        self.count = -1
            
if __name__ == '__main__':
    x = status_list(None, 'channel')
