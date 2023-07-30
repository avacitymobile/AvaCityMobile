from modules.base import Module
import const
import time


class Rating(Module):
    def __init__(self, server):
        self.serv = server
        self.commands = {"get": self.get}

        self.update_time = 3600
        self.last_update = None

        self.rating_top: list = []

    async def update(self):
        redis = self.serv.redis
        users: dict = {}

        for uid in range(1, int(await redis.get("uids")) + 1):
            house_rating = await redis.get(f"uid:{uid}:hrt")

            if not house_rating: continue

            apprnc = await redis.lrange(f"uid:{uid}:apprnc", 0, -1)

            if not apprnc: continue

            users[uid] = int(house_rating)

        sorted_users = sorted(users.items(), key=lambda key: key[1], reverse=True)
        sorted_users = sorted_users[:const.USER_RATING_COUNT]

        rating_top: list = []

        for user in sorted_users:
            clothes_rating = int(await redis.get(f"uid:{user[0]}:crt"))
            rating_top.append({"uid": user[0], "hr": user[1], "cr": clothes_rating})

        self.last_update = int(time.time())
        self.rating_top = rating_top

    async def get(self, _, client):
        if not self.last_update or (self.last_update + self.update_time) -\
                                int(time.time()) < 0:
            await self.update()

        await client.send({"data": {"bt": self.rating_top},
                           "command": "ur.get"}, 34)