from threading import Timer
from time import time as now

class __init__():
    def __init__(self, bot):
        self.bot = bot
        
        self.queue = []
        self.delay = 0

        self.bot.events.add(self, 'IO', 250, 0,
                            'send', self.AddQ)

        self.bot.events.add(self, 'bot', 1, 0,
                            'clear_queue', self.clear_queue)

    def clear_queue(self, *rest):
        for x in range(len(self.queue)):
            self.queue[x].cancel()

        self.delay = 0
        self.queue = []

    def AddQ(self, msg):
        if 'queued' in msg:
            return True
        
        time = now()
        diff = self.delay - time
        new_delay = 2.75 + (len(msg['text']) + 1) / 35

        if diff < 0:
            self.delay = time + new_delay
            return True

        diff += new_delay
        self.delay += new_delay
        
        if diff <= 8:
            return True

        msg['queued'] = True

        new = Timer((diff - 8), self.do_queue, [msg])
        new.start()
        self.queue.append(new)

        return False

    def do_queue(self, msg):
        self.bot.send(**msg)
        self.queue.pop(0)
