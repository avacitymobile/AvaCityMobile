from modules.base import Module
import const
import time
import logging


class Vip(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"buy": self.buy}

        self.day_in_seconds: int = 86400
        self.packs = {5: 176, 14: 425, 30: 720}

    async def buy(self, msg, client):
        if const.BUY_VIP:
            # Logic buying vip status for real money
            return
        
        data: dict = msg["data"]
        expire: int = data["vp"]

        if expire not in self.packs:
            logging.warning(f"Conflict vip expire '{expire}'")
            return
        
        g_price: int = self.packs[expire]

        if g_price > client.res.gld: return
        
        if not client.ci.vip:
            vip_expire: int  = int(time.time()) + (expire * self.day_in_seconds)

            await client.ci.set("vexp", vip_expire)
            await client.ci.set("vip", 1)
        else:
            vip_expire: int  = expire * self.day_in_seconds
            await client.ci.set("vexp", vip_expire, mode=True)

        await client.res.set("gld", -g_price)

        await client.refresh()
        await client.ci.update()
        await client.res.update()

        await client.send({"text": f"Buy vip for {expire} days", "broadcast": False}, 36)
