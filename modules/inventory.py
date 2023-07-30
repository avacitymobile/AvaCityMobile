from modules.base import Module
import logging


class Inventory(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"use": self.use_item}

    async def use_item(self, msg, client):
        data: dict = msg["data"]
        item_id: str = data["tpid"]

        game_items = self.serv.game_items

        item = None

        if item_id in game_items["craftedActive"]:
            item = game_items["craftedActive"][item_id]
        
        elif item_id in game_items["active"]:
            item = game_items["active"][item_id]

        if not item:
            logging.warning(f"Conflict Inventory")
            logging.warning(f"Can't use '{item_id}'")
            return
            
        if "energy" not in item: return

        if not await client.inv.take(item_id, 1):
            return

        await client.res.set("enrg", item["energy"])
        await client.res.update()

        await client.inv.update()
