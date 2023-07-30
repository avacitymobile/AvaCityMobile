from modules.base import Module
import logging


class Location(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"r": self.room}

        self.avatar_actions = [("dance", "crying", "angry")]

    async def room(self, msg, client):
        subcommand = msg["command"].split(".")[2]
        args: tuple = (msg, client)

        match subcommand:
            case "info": return await self.info(*args)
            case "m": return await self.move(*args)
            case "u": return await self.action(*args)
            case   _: logging.info(f"Location module not have '{subcommand}' instruction")

    async def info(self, msg, client):
        room_members: list = []

        for uid in self.serv.onl:
            tmp = self.serv.onl[uid]

            if tmp.room == client.room:
                room_members.append({"uid": tmp.uid, "locinfo": tmp.ci.location_info(),
                                     "apprnc": await tmp.apprnc.get(), "clths": await tmp.clths.get(type_=2),
                                     "ci": await tmp.ci.get(), "usrinf": tmp.ci.user_info()})
                
        message: dict = {"data": {"rmmb": room_members}, 
                         "command": msg["command"]}
        
        if msg["command"][:1] == "h":

            room_items: list = []

            _, room_owner_id, room_id = msg["roomId"].split("_")

            if room_owner_id in self.serv.onl:
                owner = self.serv.onl[room_owner_id]

                rooms_list = await owner.rm.get()
            else:
                rooms_list = await client.rm.get(uid=room_owner_id)

            room_items, = [room for room in rooms_list["r"] if room["id"] == room_id]

            message["data"].update({"rm": room_items})

        await client.send(message, 34)

    async def action(self, msg, client):
        data: dict = msg["data"]

        client.action = data["at"]
        client.state  = data["st"]

        client.pos.direction = data["d"]
        client.pos.x = data["x"]
        client.pos.y = data["y"]

        if data["at"] in self.avatar_actions[0]:
            if client.res.enrg < 5: return

            await client.res.set("enrg", -5)
            await client.res.update()

        await self.send(msg, client.room)

    async def move(self, msg, client):
        data: dict = msg["data"]
        dx, dy = data["dx"], data["dy"]

        direction: int = int(abs(dx - dy))

        client.pos.direction = direction
        client.pos.x = dx
        client.pos.y = dy

        client.action = None
        client.state = 0

        await self.send(msg, client.room)

    async def send(self, msg, room):
        for uid in self.serv.onl:
            tmp = self.serv.onl[uid]

            if tmp.room == room:
                await tmp.send(msg, 34)