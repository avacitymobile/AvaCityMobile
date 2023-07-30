import logging

from modules.base import Module


class Avatar(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"apprnc": self.appearance,
                         "clths": self.clothes}
        
    async def clothes(self, msg, client):
        subcommand = msg["command"].split(".")[2]
        args: tuple = msg, client

        match subcommand:
            case "wear": return await self.wear_cloth(*args)
            case  "buy": return await self.buy_cloth(*args)
            case      _: logging.info(f"Avatar module not have '{subcommand}' instruction")

    async def appearance(self, msg, client):
        subcommand = msg["command"].split(".")[2]
        args: tuple = msg, client

        match subcommand:
            case  "chn": return await self.change_name(*args)
            case  "rnn": return await self.rename(*args)
            case "save": return await self.save(*args)
            case      _: logging.info(f"Avatar module not have '{subcommand}' instruction")

    async def rename(self, msg, client):
        name: str = msg["data"]["unm"]
        redis = self.serv.redis

        if client.res.gld < 50: return

        await client.res.set("gld", -50)
        await client.res.update()

        await redis.lset(f"uid:{client.uid}:apprnc", 0, name)
        client.apprnc.n = name

        await client.send({"data": {"unm": name},
                           "command": "a.apprnc.rnn"}, 34)

    async def buy_cloth(self, msg, client):
        gender = client.gender()
        data: dict = msg["data"]

        cloth = data["tpid"]

        if cloth not in self.serv.clothes[gender]:
            logging.warning(f"Conflict cloth '{cloth}'")
            return
        
        item = self.serv.clothes[gender][cloth]

        if "canBuy" in item and not item["canBuy"] or\
             "gold" in item and item["gold"] > client.res.gld or\
             "silver" in item and item["silver"] > client.res.slvr:
            return
        
        if "gold" in item:
            await client.res.set("gld", -item["gold"])
        if "silver" in item:
            await client.res.set("slvr", -item["silver"])

        await client.inv.add(cloth, "cls", 1)
        await client.clths.add_rating(cloth)
        await client.clths.change(cloth, True)

        await client.res.update()

        await client.send({"data": {"inv": await client.inv.get(),
                                    "clths": await client.clths.get(type_=2),
                                    "ccltn": await client.clths.get(type_=3),
                                    "crt": client.ci.crt},
                           "command": "a.clths.buy"}, 34)
        
    async def wear_cloth(self, msg, client):
        data: dict = msg["data"]
        clothes_type: str = data["ctp"]

        redis = client.serv.redis

        if clothes_type not in client.clths.clothes_type:
            return
        
        await client.clths.change_type(clothes_type)

        wearing = await redis.smembers(f"uid:{client.uid}:{clothes_type}")
        
        for cloth in wearing:
            await client.clths.change(cloth, False)

        clothes = data["clths"]

        for cloth in clothes:
            await client.clths.change(cloth["tpid"], True)

        await client.send({"data": {"inv": await client.inv.get(),
                                    "clths": await client.clths.get(type_=2),
                                    "ccltn": await client.clths.get(type_=3)},
                           "command": "a.clths.wear"}, 34)

    async def save(self, msg, client):
        apprnc: dict = msg["data"]["apprnc"]

        if any(True for attr in ('et', 'ht', 'brt', 'mt') 
        if not apprnc[attr]):
            return
        
        if client.has_atr:
            if client.apprnc.g != apprnc["g"]: return
        else:

            if apprnc["g"] == 1:
                weared = ["boyShoes8", "boyPants10", "boyShirt14"]
                available = ["boyUnderdress1"]
            else:
                weared = ["girlShoes14", "girlPants9", "girlShirt12"]
                available = ["girlUnderdress1", "girlUnderdress2"]

            await client.apprnc.update(apprnc)

            for item in weared + available:

                if item in weared:
                    await client.clths.add_rating(item)
                    await client.clths.change(item, True)

                await client.inv.add(item, "cls", 1)

            for ctp in client.clths.clothes_type:
                if ctp == "casual": continue

                for item in available:
                    await client.clths.change(item, True, ctp)

            await client.rm.add("livingroom", "#livingRoom", 1)
            
        await client.apprnc.update(apprnc)

        await client.send({"data": {"apprnc": await client.apprnc.get()}, 
                           "command": "a.apprnc.save"}, 34)

    async def change_name(self, msg, client):
        name: str = msg["data"]["unm"]
        await client.send({"data": {"unm": name}, "command": "a.apprnc.rnn"}, 34)
