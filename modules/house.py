import logging
from modules.location import Location
import const


class House(Location):
    def __init__(self, server):
        super().__init__(server)
        self.serv = server
        self.commands.update({"minfo": self.my_info,
                              "gr": self.get_room,
                              "r": self.room,
                              "oinfo": self.owner_info})
        
    async def owner_info(self, msg, client):
        owned_id: str = msg["data"]["uid"]

        is_online: bool = False

        if owned_id in self.serv.onl:
            owned = self.serv.onl[owned_id]
            is_online = True

        if is_online:
            apprnc = await owned.apprnc.get()
            lockinfo = owned.ci.location_info()
            usrinf = owned.ci.user_info()
            ci = await owned.ci.get()
            rooms = await owned.rm.get()
            wearing = await owned.clths.get(type_=1)
            clothes = await owned.clths.get(type_=2)
            res = await owned.res.get()
        else:
            apprnc = await client.apprnc.get(uid=owned_id)
            usrinf = client.ci.user_info(uid=owned_id)
            rooms = await client.rm.get(uid=owned_id)
            wearing = await client.clths.get(type_=1, uid=owned_id)
            clothes = await client.clths.get(type_=2, uid=owned_id)

        player = {"uid": owned_id, "apprnc": apprnc,
                  "hs": rooms, "onl": is_online, "cs": wearing,
                  "clths": clothes}
        
        if is_online:
            tmp = {"locinfo": lockinfo, "res": res, "ci": ci,
                   "achc": {"ac": {}}, "qc": {"q": []}, 
                   "wi": {"wss": []}, "usrinf": usrinf}
            player.update(tmp)

            room = owned.room.split("_")

            if room[0] != "house" or room[1] != owned_id:
                is_online = False

        await client.send({"data": {"ath": is_online, "plr": player,
                                    "hs": rooms},
                           "command": "h.oinfo"}, 34)
        
    async def room(self, msg, client):
        subcommand = msg["command"].split(".")[2]
        args: tuple = msg, client

        match subcommand:
            case "info" | "m" | "u": return await super().room(*args)
            case   "ra": return await client.refresh()
            case  "rfr": return await client.rm.update()
            case      _: logging.info(f"House module not have '{subcommand}' instruction")
        
    async def get_room(self, msg, client):
        lct = msg["data"]

        room = lct["lid"], lct["gid"], lct["rid"]
        room = "_".join(room)

        await client.rm.join(room)

        if lct["gid"] == client.uid:
            await client.send({"data": {"ath": True},
                               "command": "h.oah"}, 34)
        
        await client.send({"data": {"rid": client.room},
                           "command": "h.gr"}, 34)

    async def my_info(self, msg, client):
        is_onl: bool = msg["data"]["onl"]
        if is_onl:
            await client.send({"data": {"scs": True, 
                                        "politic": "default"},
                               "command": "h.minfo"}, 34)
            return

        if not await client.apprnc.get():
            await client.send({"data": {"has.avtr": False},
                               "command": "h.minfo"}, 34)
            return
        
        achievements: dict = {}

        redis = self.serv.redis

        for award in await redis.smembers(f"uid:{client.uid}:awards"):
            
            if award not in const.AVARDS: continue

            achievements.update({award: {"p": 0, "nWct": 0, "l": 3, "aId": award}})
        
        await client.send({"data": {"bklst": {"uids": []},
                                    "politic": "default",
                                    "plr": {"locinfo": client.ci.location_info(),
                                            "res": await client.res.get(),
                                            "apprnc": await client.apprnc.get(),
                                            "ci": await client.ci.get(),
                                            "hs": await client.rm.get(), 
                                            "onl": True, "achc": {"ac": achievements}, 
                                            "cs": await client.clths.get(type_=1),
                                            "inv": await client.inv.get(),
                                            "uid": client.uid, "qc": {"q": []},
                                            "wi": {"wss": []},
                                            "clths": await client.clths.get(type_=2),
                                            "usrinf": client.ci.user_info()},
                                    "tm": 0}, 
                           "command": "h.minfo"}, 34)
