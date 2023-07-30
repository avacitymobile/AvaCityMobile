from modules.base import Module
import logging
import const


class Furniture(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"buy": self.buy_item,
                         "save": self.save_layout,
                         "bnrm": self.buy_new_room}
        
    async def buy_new_room(self, msg, client):
        if not const.BUY_ROOM: return

        redis = self.serv.redis

        rooms = await redis.lrange(f"rooms:{client.uid}", 0, -1)
        room = "room" + str(len(rooms))

        item = msg["data"]["ltml"]
        item["rid"] = room

        room_c = client.room.split("_")

        await client.rm.add_item(item, room_c[2])
        await client.rm.add(room, room, len(rooms) + 1)
        await client.rm.update()

        rooms = await client.rm.get()

        room, = [r for r in rooms["r"] if r["id"] == room]

        await client.ci.update()

        await client.send({"data": {"r": room},
                           "command": "frn.bnrm"}, 34)

        
    async def save_layout(self, msg, client):
        data: dict = msg["data"]
        items: list = data["f"]

        for item in items:
            item_t: int = item["t"]
            args: tuple = (item, client)

            match item_t:
                case 0: await self.add_item(*args)
                case 1: await client.rm.update_item(item)
                case 2: await client.rm.del_item(item)
                case 3: await client.rm.replace_door(item)
                case _: logging.warning(f"Wrong save layout type '{item_t}'")

        cur_room = client.room.split("_")[2]
        rooms = await client.rm.get()

        room, = [r for r in rooms["r"] if r["id"] == cur_room]

        await client.inv.update()

        await client.send({"data": {"ci": await client.ci.get(),
                                    "hs": room},
                           "command": "frn.save"}, 34)

    async def add_item(self, item, client):
        item_id = item["tpid"]

        if not await client.inv.take(item_id, 1): return

        if any(ext for ext in ("wll", "wall")\
                if ext in item_id.lower()):
            return await self.add_wall(item, client)
        
        if any(ext for ext in ("flr", "floor")\
                if ext in item_id.lower()):
            return await self.add_floor(item, client)
        
    async def add_floor(self, params, client):
        room = client.room.split("_")

        items, = [r for r in client.rm.rooms["r"] if r["id"] == room[2]]
        items = items["f"]

        for item in items:
            type_id = item["tpid"]

            if "flr" in type_id or "floor" in type_id:
                await client.rm.del_item(item)

        params["x"] = float(0)
        params["y"] = float(0)
        params["z"] = float(0)
        params["d"] = 5

        await client.rm.add_item(params, room[2])

    async def add_wall(self, params, client):
        room = client.room.split("_")

        items, = [r for r in client.rm.rooms["r"] if r["id"] == room[2]]
        items = items["f"]

        walls: list = []

        for item in items:
            type_id = item["tpid"]

            if "wll" in type_id or "wall" in type_id:
                add_item = True

                if type_id not in walls:
                    walls.append(type_id)
                else:
                    add_item = False

                await client.rm.del_item(item, add_item)

        params["x"] = float(0)
        params["y"] = float(0)
        params["z"] = float(0)
        params["d"] = 3

        await client.rm.add_item(params, room[2])

        params["x"] = float(13)
        params["d"] = 5

        params["lid"] += 1

        await client.rm.add_item(params, room[2])

    async def buy_item(self, msg, client):
        data: dict = msg["data"]
        item: str = data["tpid"]

        if item not in self.serv.furniture:
            logging.warning(f"Conflict Furniture")
            logging.warning(f"Can't buy item '{item}'")
            return
        
        item_i = self.serv.furniture[item]

        if not item_i["canBuy"] or item_i["gold"] > client.res.gld or\
               item_i["silver"] > client.res.slvr:
            return
        
        await client.res.set("gld", -item_i["gold"])
        await client.res.set("slvr", -item_i["silver"])

        await client.inv.add(item, "frn", 1)

        await client.res.update()
        await client.inv.update()
