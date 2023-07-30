from modules.base import Module
import time


class Event(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"gse": self.get_self_event,
                         "get": self.get_events,
                         "cse": self.close,
                         "crt": self.create}

        self.events: dict = {}

    async def create(self, msg, client):
        if client.uid in self.events: return

        event = msg["data"]["ev"]

        event = {"ds": event["ds"], "uid": client.uid,
                 "tt": event["tt"], "c": event["c"],
                 "ml": event["ml"], "id": len(self.events) + 1,
                 "lg": event["lg"], "st": int(time.time()),
                 "l": event["l"], "ft": int(time.time()) + event["lg"] * 60,
                 "unm": client.apprnc.n, "r": event["r"], "tp": event["tp"]}
        
        self.events[client.uid] = event

        await client.send({"data": {"ev": event},
                           "command": "ev.crt"}, 34)

    async def close(self, msg, client):
        if client.uid not in self.events: return

        del self.events[client.uid]

        await client.send({"data": {},
                           "command": "ev.cse"}, 34)

    async def get_events(self, msg, client):
        category: int = msg["data"]["c"]
        events: list = []

        for uid in self.events:
            event = self.events[uid]

            if int(time.time()) - event["ft"] > 0:
                del self.events[uid]
                continue

            if category == -1:
                events.append(event)
            elif category == event["c"]:
                event.append(event)

        await client.send({"data": {"c": category,
                                    "evlst": events},
                           "command": "ev.get"}, 34)

    async def get_self_event(self, msg, client):
        if client.uid not in self.events:

            await client.send({"data": {},
                               "command": "ev.gse"}, 34)
            return
        
        await client.send({"data": {"ev": self.events[client.uid]},
                               "command": "ev.gse"}, 34) 