from modules.base import Module
import time


######### ADD QUEST #########

# sadd uid:1:q quest_id 
# sadd uid:1:q:quest_id:ts step
# set  uid:1:q:quest_id:ts:step:pr 0


class Quests(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"get": self.get}

    async def get(self, msg, client):
        redis = self.serv.redis

        user_quests: list = await redis.smembers(f"uid:{client.uid}:q")

        quests: list = []

        for quest in user_quests:
            quest_steps: list = []

            steps: list = await redis.smembers(f"uid:{client.uid}:q:{quest}:ts")

            for step in steps:
                progress: int = int(await redis.get(f"uid:{client.uid}:q:{quest}:ts:{step}:pr"))

                quest_steps.append({"bt": False, "pr": progress, "tp": step})

            quest: dict = {'dur': 0, 'time': int(time.time()),
                           'qid': quest, 'ts': quest_steps}
            
            quests.append(quest)
        
        await client.send({"data": {"qc": {"q": quests}},
                           "command": "q.get"}, 34)
