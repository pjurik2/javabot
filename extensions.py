import plugs

class plugins():  
    def __init__(self, parent):
        self.classes = {}
        
        self.modules = plugs._getmodules()
        self.parent = parent
        
    def load_classes(self, get_type=None, new_parent=None, order={}):
        self.classes = {}
        new_order = []

        if new_parent == None:
            parent = self.parent
        else:
            parent = new_parent

        #print 'Loading ' + str(get_type) + '-type plugins...'

        for name, ref in self.modules.iteritems():
            config = {'type': None,
                      'order': 1,
                      'class': None}
            try:
                config.update(ref.config)
            except:
                pass #Nothing to update

            if name in order:
                config['order'] = int(order[name])
            else:
                order[name] = config['order']

            if config['class'] != None:
                newclass = config['class']
            else:
                newclass = ref.__init__

            if config['type'] == get_type and config['order'] != 0:
                new_order.append([config['order'], name, newclass])

        new_order.sort()

        for mod in new_order:
            self.classes[mod[1]] = [mod[2](parent), parent]

    def reset_class(self, name):
        try:
            module = reload(self.modules[name])
        except KeyError:
            return False #Plugin doesn't exist

        try:
            cl = self.classes[name]
        except KeyError:
            return False #No instance of this class
        parent = cl[1]

        try:
            remove = self.parent.events.remove
        except NameError:
            pass #This parent doesn't handle events
        else:
            remove(cl[0])

        if hasattr(cl[0], '__del__'):
            cl[0].__del__()
        del cl
        del self.classes[name]

        self.modules[name] = module
        self.classes[name] = [module.__init__(parent), parent]
    
