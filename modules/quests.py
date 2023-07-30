from modules.base import Module
import time


class Quests(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"get": self.get}

    async def get(self, msg, client):
        quests = [{'dur': 0, 'time': int(time.time()),
                  'qid': 'q31', 'ts': []}]
        
        await client.send({"data": {"qc": quests},
                           "command": "q.get"}, 34)
