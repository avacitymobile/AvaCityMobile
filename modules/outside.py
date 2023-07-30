import logging
from modules.location import Location
import const


class Outside(Location):
    def __init__(self, server):
        super().__init__(server)

        self.serv = server
        self.commands.update({"gr": self.get_room, "r": self.room,
                              "bi": self.buy_item})
        
    async def buy_item(self, msg, client):
        item_id: str = msg["data"]["tpid"]

        if item_id not in self.serv.game_items["game"]:
            logging.debug(f"Outside buy_item conflict '{item_id}'")
            return
        
        item = self.serv.game_items["game"][item_id]

        if client.res.gld < item["gold"] or\
           client.res.slvr < item["silver"]:
            return
        
        if "energy" not in item: return
        
        await client.res.set("gld", -item["gold"])
        await client.res.set("slvr", -item["silver"])
        await client.res.set("enrg", item["energy"])
        
        await client.res.update()

        await client.send(msg, 34)
        
    async def room(self, msg, client):
        subcommand = msg["command"].split(".")[2]
        args: tuple = (msg, client)

        match subcommand:
            case "info" | "m" | "u": return await super().room(*args)
            case   _: logging.info(f"Outside module not have '{subcommand}' instruction")

    async def get_room(self, msg, client):
        data: dict = msg["data"]
        room_id: int = 1

        room = (data["lid"], data["gid"], str(room_id))

        while self.users_in_location(room) >= const.USERS_IN_LOCATION:
            
            room_id += 1
            room = (data["lid"], data["gid"], str(room_id))

        room = "_".join(room)

        if "dx" in data and "dy" in data:
            client.pos.x = data["dx"]
            client.pos.y = data["dy"]
        
        await client.rm.join(room)

        await client.send({"data": {"rid": room}, "command": "o.gr"}, 34)

    def users_in_location(self, room):
        users: int = 0

        room = "_".join(room)

        for uid in self.serv.onl:
            tmp = self.serv.onl[uid]

            if tmp.room == room:
                users += 1

        return users
