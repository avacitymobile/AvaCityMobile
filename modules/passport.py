from modules.base import Module
import const


######### ADD AWARD #########
# sadd uid:1:awards award_id


class Passport(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"psp": self.passport,
                         "pspdr": self.display_relations}
        
    async def display_relations(self, msg, client):
        if not client.ci.vip: return

        dress_status: bool = not bool(msg["data"]["dr"])

        await client.ci.set("dr", int(dress_status))
        await client.ci.update()

    async def passport(self, msg, client):
        user_id: str = msg["data"]["uid"]

        achievements: dict = {}

        redis = self.serv.redis

        for award in await redis.smembers(f"uid:{user_id}:awards"):
            
            if award not in const.AVARDS: continue

            achievements.update({award: {"p": 0, "nWct": 0, "l": 3, "aId": award}})

        await client.send({"data": {"psp": {"uid": user_id,
                                            "ach": {"ac": achievements},
                                            "rel": {}}},
                           "command": "psp.psp"}, 34)
