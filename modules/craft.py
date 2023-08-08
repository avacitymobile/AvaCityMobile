import logging
import math
from modules.base import Module
import random

import mlparser as parser


class Craft(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"bcp": self.buy_chips,
                         "bc":  self.buy_component,
                         "prd": self.produce}

        self.gold_pack = (100, 350, 800, 2700)
        self.items = parser.parse_craft()

    async def produce(self, msg, client):
        data: dict = msg["data"]
        item_id: str = data["itId"]

        if item_id not in self.items:
            logging.warning(f"Conflict craft item '{item_id}'")
            return
        
        loot_items: dict = {}
        
        loot = client.inv.lt["it"]

        for lt in loot:
            loot_items[lt["tid"]] = lt["c"]

        for item in self.items[item_id]["items"]:
            if item not in loot_items: return

            have = loot_items[item]

            if have < self.items[item_id]["items"][item]: return

        for item in self.items[item_id]["items"]:
            amount = self.items[item_id]["items"][item]

            await client.inv.take(item, amount)

        if "views" in self.items[item_id]:
            views = self.items[item_id]["views"]
            
            if views: item_id += random.choice(views.split(","))

        gender = client.gender()

        if item_id in self.serv.game_items["game"]:
            type_ = "gm"
        elif item_id in self.serv.game_items["craftedActive"]:
            type_ = "act"
        elif item_id in self.serv.game_items["loot"]:
            type_ = "lt"
        elif item_id in self.serv.furniture:
            type_ = "frn"
        elif item_id in self.serv.clothes[gender]:
            await client.clths.add_rating(item_id)
            type_ = "cls"
        else:
            logging.warning(f"Conflict craft item '{item_id}'")
            return
        
        await client.inv.add(item_id, type_, 1)

        await client.refresh()

        await client.send({"data": {"inv": await client.inv.get(),
                                    "crIt": {"c": 1, "lid": "", "tid": item_id}},
                           "command": "crt.prd"}, 34)

    async def buy_component(self, msg, client):
        data: dict = msg["data"]

        item = data["itId"]

        if item not in self.items:
            logging.warning(f"Conflict craft item '{item}'")
            return
        
        to_buy: dict = {}
        
        items = self.serv.game_items["loot"]

        component_ids = data["cmIds"]

        loot_items: dict = {}

        gold: int = 0

        loot = client.inv.lt["it"]

        for lt in loot:
            loot_items[lt["tid"]] = lt["c"]

        for cmt in component_ids:
            price = items[cmt]["gold"] / 100

            if cmt in loot_items:
                have = loot_items[cmt]
            else:
                have = 0

            amount = self.items[item]["items"][cmt] - have

            if amount <= 0: continue

            gold += math.ceil(price * amount)

            to_buy[cmt] = amount

        if client.res.gld < gold: return

        await client.res.set("gld", -gold)
        await client.res.update()

        component_items: list = []

        for loot_id in to_buy:
            await client.inv.add(loot_id, "lt", to_buy[loot_id])
            component_items.append({"c": to_buy[loot_id], "iid": "", "tid": loot_id})

        await client.send({"data": {"itId": item,
                                    "compIts": component_items},
                           "command": "crt.bc"}, 34)

    async def buy_chips(self, msg, client):
        data: dict = msg["data"]
        pack: str  = data["pk"]

        is_avacoin: bool = "AvaCoin" in pack
        args: tuple = (msg, client)

        match int(is_avacoin):
            case 1: return await self.buy_avacoin(*args)
            case 0: return await self.buy_gold(*args)

    async def buy_avacoin(self, msg, client):
        logging.debug(f"Buy avacoin logic")

    async def buy_gold(self, msg, client):
        data: dict = msg["data"]
        pack_idx: int = int(data["pk"][-1::])

        if pack_idx > len(self.gold_pack):
            return
        
        pack_idx -= 1
        
        await client.res.set("gld", self.gold_pack[pack_idx])
        await client.res.update()

        await client.send({"text": f"Buy {self.gold_pack[pack_idx]} gold",
                           "broadcast": False}, 36)
