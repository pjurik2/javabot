from types import ClassType, FunctionType, MethodType, InstanceType


class Events():
    def __init__(self):
        self.events = {}

    def remove_ident(self, ident, cd, place=0):
        queue = [None]
        
        while cd != None:
            keys = cd.keys()
            for k in keys:
                if type(cd[k]) == dict:
                    queue.append(cd[k])
                elif type(cd[k]) == list:
                    for x in range(len(cd[k])):
                        if x >= len(cd[k]):
                            break #I thought this would be obvious...
                        if cd[k][x][place] == ident:
                            del cd[k][x]
                            x -= x
                            
                    if cd[k] == []:
                        del cd[k]

            cd = queue.pop()

    def remove_instance(self, instance, cd):
        self.remove_ident(instance, cd, 3)

    def remove_func(self, func, cd):
        self.remove_ident(func, cd, 2)

    def remove(self, *args):
        if type(args[0]) == InstanceType:
            self.remove_instance(args[0], self.events)
            return

        if type(args[0]) in [FunctionType, MethodType]:
            self.remove_func(args[0], self.events)
            return

        if MethodType in map(type, args[1:]):
            self._remove(*args)
            return

        cd = self.events

        for sub in args[:-1]:
            try:
                cd = cd[sub]
            except KeyError:
                return #Doesn't exist anyway
        try:
            del cd[args[-1]]
        except KeyError:
            return
    
    def _remove(self, sect, sub=None, *func):
        if sub == None:
            try:
                del self.events[sect]
            except KeyError:
                pass
            return

        if func == ():
            try:
                del self.events[sect][sub]     
            except KeyError:
                pass
        else:
            try:
                to_delete = []
                
                for x in range(len(self.events[sect][sub])):
                    if self.events[sect][sub][x][2] in func:
                        to_delete.append(x)

                for x in to_delete:
                    del self.events[sect][sub][x]

                if self.events[sect][sub] == {}:
                    del self.events[sect][sub]
            except KeyError:
                pass
                
        try:
            if self.events[sect] == {}:
                del self.events[sect]
        except KeyError:
            pass

    def add(self, *args):
        x = 0
        if type(args[0]) in [InstanceType, ClassType]:
            parent = args[0]
            args = args[1:]
        else:
            parent = None
            
        cd = self.events

        try:
            types = map(type, args)
            first_func = types.index(MethodType)
        except ValueError:
            try: #I guess.
                first_func = types.index(FunctionType)
            except ValueError:
                return

        for x in range(0, first_func - 3):
            if (args[x] in cd) == False:
                cd[args[x]] = {}

            cd = cd[args[x]]
            x += 1

        priority = args[x]
        flags = args[x+1]
        x += 2

        for x in range(x, len(args), 2):
            if (args[x] in cd) == False:
                cd[args[x]] = []

            cd[args[x]].append([priority, flags, args[x+1], parent])
            cd[args[x]].sort()

    def call(self, *args):
        called = False
        x = 0
        cd = self.events

        l_args = ()
        d_args = {}
        
        while x < len(args) and type(args[x]) in [str, int]:
            try:
                cd = cd[args[x]]
            except KeyError:
                return False #Section or sub is missing
            x += 1

        for arg in args[x:]:
            if type(arg) == list:
                l_args += tuple(arg)
            elif type(arg) == dict:
                d_args.update(arg)

        for handler in cd:
            if handler[1] == 1 and len(cd) > 1:
                pass
            else:
                result = handler[2](*l_args, **d_args)

                if handler[1] == -1 or result == False:
                    return True #Unique/interrupt, stop handling

                called = True

        return called
