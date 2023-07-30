from modules.base import Module


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

        await client.send({"data": {"psp": {"uid": user_id,
                                            "ach": {"ac": {}},
                                            "rel": {}}},
                           "command": "psp.psp"}, 34)