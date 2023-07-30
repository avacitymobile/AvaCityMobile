from modules.base import Module


class Billing(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"ren": self.restore_energy,
                         "bs": self.buy_silver}

        self.energy_pack = ((100, 3), (480, 14), (1555, 45),
                            (4800, 135))
        self.silver_price = 100

    async def buy_silver(self, msg, client):
        data: dict = msg["data"]
        gold: int  = data["gld"]

        s_count: int = gold * self.silver_price

        if client.res.gld < gold: return

        await client.res.set("gld", -gold)
        await client.res.set("slvr", s_count)
        await client.res.update()

        return await client.send({"data": {"slvr": client.res.slvr, 
                                           "inslv": s_count},
                                  "command": "b.inslv"}, 34)

    async def restore_energy(self, msg, client):
        data: dict = msg["data"]
        pack: str = data["pk"]

        first_l: str = pack[-1::]

        pack_idx: int = 0 if not first_l.isdigit() \
                          else int(first_l)
        if pack_idx: pack_idx -= 1
        
        energy, price = self.energy_pack[pack_idx]

        if client.res.gld < price: return

        await client.res.set("gld", -price)
        await client.res.set("enrg", energy)
        await client.res.update()

        await client.send({"text": f"Buy {energy} energy", "broadcast": False}, 36)
