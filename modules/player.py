from modules.base import Module


class Player(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"gid": self.get_buy_id,
                         "flw": self.follow}

    async def get_buy_id(self, msg, client):
        redis = self.serv.redis
        players: list = []

        for uid in msg["data"]["uids"]:
            crt = await redis.get(f"uid:{uid}:crt")
            hrt = await redis.get(f"uid:{uid}:hrt")
            exp = await redis.get(f"uid:{uid}:exp")

            players.append({"apprnc": await client.apprnc.get(uid),
                            "uid": uid,
                            "clths": await client.clths.get(2, uid),
                            "ci": {"crt": int(crt), "hrt": int(hrt),
                                   "exp": int(exp)},
                            "usrinf": client.ci.user_info(uid)})
            
        await client.send({"data": {"plrs": players,
                                    "clid": msg["data"]["clid"]},
                           "command": "pl.get"}, 34)
        
    async def follow(self, msg, client):
        uid = str(msg["data"]["uid"])

        if uid in self.serv.onl:
            tmp = self.serv.onl[uid]

            await client.send({"data": {"locinfo": tmp.ci.location_info()},
                               "command": "pl.flw"}, 34)
            return
        await client.send({"data": {"code": 155, 
                                    "message": f"code: 155; msg : user with id {uid}"
                                    " is offline."}, 
                           "command": "err"}, 34)
