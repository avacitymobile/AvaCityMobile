import asyncio
import logging
import conf
import common
import const
import time
import importlib

import redis.asyncio as aioredis 
from client import Client
import mlparser as parser


class Server:
    def __init__(self, debug=False):
        self.debug: bool = debug
        self.onl: dict = {}

        modules = {"h": "house",
                   "a": "avatar",
                   "o": "outside",
                   "crt": "craft",
                   "b": "billing",
                   "vp": "vip",
                   "tr": "inventory",
                   "frn": "furniture",
                   "q": "quests",
                   "ur": "rating",
                   "pl": "player",
                   "ev": "event",
                   "psp": "passport"}

        for prefix in modules:
            m_name = modules[prefix]
            c_name = m_name.title()
            module = importlib.import_module(f"modules.{m_name}")
            class_ = getattr(module, c_name)
            modules[prefix] = class_(self)

        self.modules = modules

        self.clothes = parser.parse_clothes()
        self.game_items = parser.parse_game()
        self.furniture = parser.parse_furniture()

    async def start(self):
        self.redis = await aioredis.from_url("redis://localhost",
                                             decode_responses=True)
        self.connection = await asyncio.start_server(self.conn, 
                                                     conf.HOST, 
                                                     conf.PORT)
        loop = asyncio.get_event_loop()
        loop.create_task(self.__debuger())

    async def process(self, msg, client):
        message: dict = msg["msg"]
        ms_type: int = msg["type"]
        
        args: tuple = message, client

        match ms_type:
            case 1:  return await self.auth(*args)
            case 17: return await client.rm.leave()
            case 32: return await self.chat(*args)
            case 34: return await self.on_module(*args)
            case _: logging.warning(f"Wrong message type: {ms_type}")

    async def chat(self, msg, client):
        broadcast: bool = True
        send_list: tuple = ()

        if msg["text"].startwith("!"):
            # chat commands
            return

        if "recipients" in msg:
            broadcast = False
            tmid = msg["recipients"][0]

            send_list = (tmid, client.uid)

        for uid in self.onl:
            if not broadcast and uid not in send_list:
                continue

            tmp = self.onl[uid]

            if tmp.room == client.room:
                await tmp.send({"sender": {"roomIds": [client.room],
                                           "name": client.apprnc.n,
                                           "zoneId": client.zone_id,
                                           "userId": client.uid},
                                "text": msg["text"], 
                                "broadcast": broadcast}, 32)

    async def on_module(self, msg, client):
        prefix = msg["command"].split(".")[0]

        if prefix not in self.modules:
            logging.warning(f"Command {msg['command']} not found")
            return
        
        await self.modules[prefix].on_message(msg, client)

    async def auth(self, msg, client):
        jwt_token = msg["login"]
        uid, token = await common.check_account(jwt_token, self.redis)

        if not client.role:
            client.role = int(await self.redis.get(f"uid:{uid}:role"))

        if conf.TECHNICAL_WORKING and client.role\
               < const.ROLE.AVATAR_MODERATOR_ROLE:
            await client.send({'zoneId': msg['zoneId'],
                                'error': {'code': 10, 'data': {'duration': 3600,
                                    'reason': "Технические работы", 'banTime': int(time.time()),
                                    'reasonId': 4, 'unbanType': 'admin panel',
                                    'leftTime': 3600, 'userId': None,
                                    'moderatorId': "1"},
                                'message': 'User is banned'}}, 2)
            client.writer.close()
            return

        if not client.uid:

            if uid in self.onl:
                tmp = self.onl[uid]
                tmp.writer.close()
                del self.onl[uid]
                
            client.uid = uid

        if uid not in self.onl:
            self.onl[uid] = client

        client.zone_id = msg["zoneId"]
        
        return await client.send({"secretKey": token, "zoneId": client.zone_id,
                                  "user": {"roomIds": [], "name": None,
                                           "zoneId": client.zone_id,
                                           "userId": client.uid},
                                  "userId": uid}, 1)

    async def conn(self, reader, writer):
        loop = asyncio.get_event_loop()
        loop.create_task(Client(self).handle(reader, writer))

    async def stop(self):
        self.connection.close()
        await self.connection.wait_closed()

    async def restore_energy(self):
        uids = await self.redis.get("uids")

        if not uids: return

        for uid in range(1, int(uids) + 1):
            uid = str(uid)

            if uid in self.onl:
                tmp = self.onl[uid]

                if tmp.res.enrg and tmp.res.enrg < 100:
                    await tmp.res.set("enrg", 1)
                    await tmp.res.update()

            else:
                energy = await self.redis.get(f"uid:{uid}:enrg")
                
                if not energy: continue

                await self.redis.incr(f"uid:{uid}:enrg")

    async def __debuger(self):
        while True:
            logging.info(f"Players online: {len(self.onl)}")

            if const.RESTORE_ENERGY:
                asyncio.create_task(self.restore_energy())

            await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)-8s [%(asctime)s]  %(message)s",
                        datefmt="%H:%M:%S", level=logging.DEBUG)
    server = Server(debug=conf.DEBUG)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(server.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(server.stop())
    loop.close()
