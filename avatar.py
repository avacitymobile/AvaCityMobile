import const


class Avatar:
    def __init__(self, client):
        self.uid:     str = ""
        self.action:  str = ""
        self.zone_id: str = ""
        self.state:   int = 0
        self.room:    str = ""
        self.role:    int = 0
        self.has_atr: bool = False

        self.pos = self.Position()
        self.apprnc = self.Appearance(client)
        self.res = self.Resources(client)
        self.inv = self.Inventory(client)
        self.ci = self.Info(client)
        self.clths = self.Clothes(client)
        self.rm = self.Room(client)

        self.client = client

    def gender(self):
        gender = self.client.apprnc.g

        match gender:
            case 1: return "boy"
            case _: return "girl"

    async def refresh(self):
        client = self.client

        prefix: str = self.rm.get_prefix(client.room)

        for uid in client.serv.onl:
            tmp = client.serv.onl[uid]

            if tmp.room == client.room:
                await tmp.send({"data": {"plr": {"uid": client.uid,
                                                 "locinfo": self.ci.location_info(),
                                                 "apprnc": await self.apprnc.get(),
                                                 "clths": await self.clths.get(type_=2),
                                                 "ci": await self.ci.get(),
                                                 "usrinf": self.ci.user_info()}},
                                "command": f"{prefix}.r.ra"}, 34)

    class Position:
        x: float = 4.0
        y: float = 1.0
        direction: int = 3

        def default(self):
            self.x = 4.0
            self.y = 1.0
            self.direction = 3

    class Appearance:
        def __init__(self, client):
            self.n:   str = None # name
            self.g:   int = None # gender
            self.sc:  int = None # skin color
            self.ht:  int = None # hair type
            self.hc:  int = None # hair color
            self.brt: int = None # brows type
            self.brc: int = None # brows color
            self.et:  int = None # eyes type
            self.ec:  int = None # eyes color
            self.mt:  int = None # mouth type
            self.mc:  int = None # mouth color
            self.bt:  int = None # beard type
            self.bc:  int = None # beard color
            self.rg:  int = None # rouge type
            self.rc:  int = None # rouge color
            self.sh:  int = None # shadow type
            self.shc: int = None # shadow color
            self.ss:  int = None # strass type

            self.apr: tuple = ("n", "g", "sc", "ht",
                        "hc", "brt", "brc", "et",
                        "ec", "mt", "mc", "bt", "bc",
                        "rg", "rc", "sh", "shc", "ss")
            self.client = client

        async def get(self, uid: str = None):
            client = self.client
            apprnc: dict = {}

            if not client.has_atr or uid:
                apprn = await self.get_by_id(client.uid if not uid else uid)
                if not apprn:
                    return False
                for idx, attr in enumerate(self.apr):
                    value = apprn[idx]

                    if value.isdigit():
                        value = int(value)

                    if not uid:
                        setattr(self, attr, value)
                    else:
                        apprnc[attr] = value

                if not uid:
                    client.has_atr = True

            if not apprnc:
                for key in self.apr:
                    apprnc[key] = getattr(self, key)

            return apprnc
        
        async def get_by_id(self, uid):
            redis = self.client.serv.redis
            apprnc = await redis.lrange(f"uid:{uid}:apprnc", 0, -1)
            if not apprnc:
                return False
            return apprnc

        async def update(self, apprnc):
            client = self.client
            if client.has_atr:
                avatar_name = self.n
            else:
                avatar_name = apprnc["n"]
            new_apprnc: list = [avatar_name]
            for attr in self.apr[1:]:
                value = apprnc[attr]
                new_apprnc.append(value)
                setattr(self, attr, value)
            redis = client.serv.redis
            await redis.delete(f"uid:{client.uid}:apprnc")
            await redis.rpush(f"uid:{client.uid}:apprnc", *new_apprnc)

    class Resources:
        def __init__(self, client):
            self.gld:  int = 0
            self.slvr: int = 0
            self.enrg: int = 0
            self.emd:  int = 0

            self.client = client
            self.res = ("gld", "slvr",
                            "enrg")

        async def get(self):
            if not any((self.gld, self.slvr, self.enrg)):

                uid = self.client.uid
                redis = self.client.serv.redis

                for attr in self.res:
                    val = int(await redis.get(f"uid:{uid}:{attr}"))
                    setattr(self, attr, val)
            
            return {"gld": self.gld, "slvr": self.slvr, 
                    "enrg": self.enrg, "emd": self.emd}
        
        async def update(self):
            await self.client.send({"command": "ntf.res",
                                    "data": {"res": await self.client.res.get()}}, 34)
        
        async def set(self, res: str, count: int):
            uid = self.client.uid
            redis = self.client.serv.redis

            setattr(self, res, getattr(self, res) + count)
            await redis.incrby(f"uid:{uid}:{res}", count)

    class Inventory:
        def __init__(self, client):
            self.frn: dict = None # furniture
            self.act: dict = None # activity
            self.cls: dict = None # clothes
            self.gm:  dict = None # game
            self.lt:  dict = None # loot

            self.tps: tuple = ("frn", "act", "gm",
                               "lt", "cls")

            self.client = client

        async def update(self, send=True):
            inv = await self.get()
            if send:
                await self.client.send({"data": {"inv": inv},
                                        "command": "ntf.inv"}, 34)

        async def get(self):
            client = self.client
            redis = client.serv.redis

            if not all((self.frn, self.act, self.cls,
                       self.gm, self.lt)):
                
                for inv_t in self.tps:
                    setattr(self, inv_t, {"id": inv_t, "it": []})

                clths_t = await redis.get(f"uid:{client.uid}:wearing")
                dressed_clths = await redis.smembers(f"uid:{client.uid}:{clths_t}")

                items = await redis.smembers(f"uid:{client.uid}:items")
                for item in items:

                    if item in dressed_clths:
                        continue

                    item_t, item_c = await redis.lrange(f"uid:{client.uid}:items:{item}", 0, -1)

                    inv_t = getattr(self, item_t)
                    inv_t["it"].append({"c": int(item_c), "iid": "", "tid": item})

                    setattr(self, item_t, inv_t)

            return {"c": {attr: getattr(self, attr)\
                          for attr in self.tps}}

        async def add(self, name, type_, count):
            client = self.client
            redis = client.serv.redis

            item = await redis.lrange(f"uid:{client.uid}:items:{name}", 0, -1)
            attr = getattr(self, type_)
            
            if item:
                if type_ != "cls":
                    old_count = int(item[1])
                    new_count = int(item[1]) + count

                    await redis.lset(f"uid:{client.uid}:items:{name}", 1, new_count)

                    idx = attr["it"].index({"c": old_count, "iid": "", "tid": name})
                    del attr["it"][idx]

                    attr["it"].append({"c": new_count, "iid": "", "tid": name})
                    setattr(self, type_, attr)
                else:
                    return False
            else:
                await redis.sadd(f"uid:{client.uid}:items", name)
                await redis.rpush(f"uid:{client.uid}:items:{name}", type_, count)

                if attr:
                    attr["it"].append({"c": count, "iid": "", "tid": name})
                    setattr(self, type_, attr)
            
            return True

        async def take(self, item, count):
            client = self.client
            redis = client.serv.redis

            items = await redis.smembers(f"uid:{client.uid}:items")
            if item in items:
                type_, have_c = await redis.lrange(f"uid:{client.uid}:items:{item}", 0, -1)
                have_c = int(have_c)

                if have_c < count:
                    return False
                
                inv_t = getattr(self, type_)
                
                if have_c > count:
                    new_count = have_c - count

                    await redis.lset(f"uid:{client.uid}:items:{item}", 1, new_count)

                    idx = inv_t["it"].index({"c": have_c, "iid": "", "tid": item})
                    del inv_t["it"][idx]

                    inv_t["it"].append({"c": new_count, "iid": "", "tid": item})
                else:
                    await redis.delete(f"uid:{client.uid}:items:{item}")
                    await redis.srem(f"uid:{client.uid}:items", item)

                    idx = inv_t["it"].index({"c": have_c, "iid": "", "tid": item})
                    del inv_t["it"][idx]

                setattr(self, type_, inv_t)

                return True
            
            return False

    class Info:
        def __init__(self, client):
            self.dr:  bool = None  # display relations
            self.vexp: int = None  # vip expired at
            self.ceid: int = None  # co engaged id
            self.cmid: int = None  # co married id
            self.exp:  int = None  # exp
            self.vip: bool = None  # vip
            self.crt:  int = None  # clothes rating
            self.hrt:  int = None  # house rating

            self.cps: tuple = ("dr", "vexp", "ceid", 
                               "cmid", "exp", "vip", 
                               "crt", "hrt")
            
            self.client = client

        async def get(self):
            client = self.client
            redis = client.serv.redis

            if self.dr is None:
                for cp in self.cps:
                    value = int(await redis.get(f"uid:{client.uid}:{cp}"))
                    setattr(self, cp, value)
            
            return {"eml": None, "ldrt": 0, "dr": bool(self.dr), "vexp": self.vexp,
                    "fak": None, "ceid": self.ceid, "fexp": 0, "lgt": 0, "ys": 0,
                    "exp": self.exp, "vret": 0, "vip": bool(self.vip), "crt": self.crt,
                    "drli": 1, "gdc": 0, "ldc": 19, "cmid": self.cmid, "hrt": self.hrt,
                    "ckid": None, "shcr": True, "spp": 0, "tts": None, "ysct": 0, "llt": 0,
                    "vfgc": 0, "drlp": 4}
        
        async def set(self, attr, val, mode=False):
            client = self.client
            redis = client.serv.redis

            if not mode:
                await redis.set(f"uid:{client.uid}:{attr}", val)
            else:
                await redis.incrby(f"uid:{client.uid}:{attr}", val)
                
                attrib = getattr(self, attr)
                if attrib: val += attrib
            
            setattr(self, attr, val)

        def location_info(self):
            client = self.client
            c_pos = client.pos

            return {"st": client.state,  "s": "127.0.0.1",
                    "at": client.action, "d": c_pos.direction,
                    "x":  c_pos.x, "y": c_pos.y, "pl": "",
                    "l":  client.room}
    
        def user_info(self, uid=None):
            client = self.client
            c_apprnc = client.apprnc

            return {"gdr": c_apprnc.g, "lng": "default",
                    "lcl": "RU", "rl": client.role, "al": 2,
                    "sid": client.uid if not uid else uid}

        async def update(self):
            client = self.client

            await client.send({"data": {"ci": await client.ci.get()},
                               "command": "ntf.ci"}, 34)

    class Clothes:
        def __init__(self, client):
            self.clothes_type: tuple = ("casual", "club", 
                                        "official", "swimwear", 
                                        "underdress")

            self.client = client

        async def get(self, type_: int, uid: str = None):
            client = self.client
            redis = client.serv.redis

            if not uid: uid = client.uid

            items: list = []

            clths_t = await redis.get(f"uid:{uid}:wearing")
            wearing: list = await redis.smembers(f"uid:{uid}:{clths_t}")

            for item in wearing:
                items.append({"id": item, "clid": ""})

            del wearing

            clothes: dict = {}

            match type_:
                case 1:
                    clothes.update({"cc": clths_t, "ccltns": {}})
                    for ctp in self.clothes_type:
                        if ctp == clths_t: continue

                        wearing = await redis.smembers(f"uid:{uid}:{ctp}")

                        clothes["ccltns"][ctp] = {"cct": [], "cn": "", "ctp": ctp}

                        for item in wearing:
                            clothes["ccltns"][ctp]["cct"].append(item)
                case 2:
                    clothes.update({"clths": []})

                    for item in items:
                        clothes["clths"].append({"tpid": item["id"]})
                case 3:
                    clothes.update({"cct": [], "cn": "", "ctp": clths_t})

                    for item in items:
                        clothes["cct"].append(item["id"])

            return clothes
        
        async def change(self, cloth, wearing, ctp=None):
            client = self.client
            redis = client.serv.redis

            if not ctp:
                ctp = await redis.get(f"uid:{client.uid}:wearing")

            if wearing:
                await redis.sadd(f"uid:{client.uid}:{ctp}", cloth)
                return
            
            weared = await redis.smembers(f"uid:{client.uid}:{ctp}")
            if cloth not in weared: return

            await redis.srem(f"uid:{client.uid}:{ctp}", cloth)

        async def change_type(self, clothes_type):
            client = self.client
            redis = client.serv.redis

            current_type = await redis.get(f"uid:{client.uid}:wearing")
            if current_type == clothes_type: return

            await redis.set(f"uid:{client.uid}:wearing", clothes_type)

        async def add_rating(self, item):
            client = self.client
            clothes = client.serv.clothes[client.gender()]

            if item not in clothes: return

            item = clothes[item]

            if "rating" not in item: return

            clothes_rating = int(item["rating"])

            await client.ci.set("crt", clothes_rating, True)

    class Room:
        def __init__(self, client):
            self.rooms_ids: list = None
            self.rooms: dict = None

            self.client = client

        async def join(self, room):
            client = self.client

            # if client.room:
            #     await self.leave()

            client.room = room
            
            p_room = self.get_prefix(room)

            for uid in client.serv.onl:
                tmp = client.serv.onl[uid]

                if tmp.room == room:
                    await tmp.send({"data": {"plr": {"uid": client.uid, 
                                                     "locinfo": client.ci.location_info(),
                                                     "apprnc": await client.apprnc.get(),
                                                     "clths": await client.clths.get(type_=2),
                                                     "ci": await client.ci.get(),
                                            "usrinf": client.ci.user_info()}},
                                    "command": f"{p_room}.r.jn"}, 34)
                    
                    await tmp.send({"zoneId": room, "user": {"roomIds": [room],
                                                             "name": client.apprnc.n,
                                                             "zoneId": client.zone_id,
                                    "userId": client.uid}}, 16)

        async def leave(self):
            client = self.client
            
            if not client.room:
                return
            
            p_room = self.get_prefix(client.room)

            for uid in client.serv.onl:
                tmp = client.serv.onl[uid]
                if tmp.room == client.room:
                    await tmp.send({"data": {"uid": client.uid},
                                    "command": f"{p_room}.r.lv"}, 34)
                    
                    await tmp.send({"user": {"roomIds": [],
                                             "name": None,
                                             "zoneId": tmp.zone_id,
                                             "userId": client.uid},
                                    "roomId": client.room}, 17)
                    
            client.state = 0
            client.room = None
            client.action = None
            client.pos.default()

        async def get(self, uid: str = None):
            client = self.client
            redis = client.serv.redis

            if not uid:
                uid = client.uid

            is_client: bool = client.uid == uid

            rooms: dict = {"r": [], "lt": 0}

            if not self.rooms_ids or not is_client:
                rooms_ids = await redis.lrange(f"rooms:{uid}", 0, -1)

                for item in rooms_ids:
                    r_name, r_lev = await redis.lrange(f"rooms:{uid}:{item}", 0, -1)
                    items = await self.get_items(uid, item)

                    rooms["r"].append({"f": items, "w": 13, "id": item,
                                       "lev": int(r_lev), "l": 13,
                                       "nm": r_name})
                    
                if is_client:
                    self.rooms = rooms
                    self.rooms_ids = rooms_ids

            return rooms if not is_client else self.rooms
        
        async def get_items(self, uid, room):
            redis = self.client.serv.redis
            items: list = []

            for item in await redis.smembers(f"rooms:{uid}:{room}:items"):
                x, y, z, d = await redis.lrange(f"rooms:{uid}:{room}:items:{item}", 0, -1)
                options = await redis.smembers(f"rooms:{uid}:{room}:items:{item}:options")

                *item, lid = item.split("_")
                item = "_".join(item)

                tmp = {"tpid": item, "x": float(x),
                       "y": float(y), "z": float(z),
                       "d": float(d), "lid": int(lid)}
                
                for option in options:
                    val = await redis.get(f"rooms:{uid}:{room}:items:{item}_{lid}:{option}")

                    tmp[option] = val

                items.append(tmp)

            return items

        async def add(self, room, name, lev=2):
            client = self.client
            redis = client.serv.redis

            await redis.rpush(f"rooms:{client.uid}", room)
            await redis.rpush(f"rooms:{client.uid}:{room}", name, lev)

            if self.rooms:
                self.rooms_ids.append(room)
                self.rooms["r"].append({"f": [], "w": 13, "id": room,
                                        "lev": lev, "l": 13,
                                        "nm": name})

            for item in const.NEW_ROOM:
                await self.add_item(item, room)

        async def add_item(self, params, room):
            client = self.client
            redis = client.serv.redis

            if "oid" in params:
                params["lid"] = params["oid"]
                del params["oid"]

            item = params["tpid"], str(params["lid"])
            item = "_".join(item)

            await redis.sadd(f"rooms:{client.uid}:{room}:items", item)

            if "rid" in params:
                await redis.sadd(f"rooms:{client.uid}:{room}:items:{item}:options", "rid")

                if params["rid"]:
                    await redis.set(f"rooms:{client.uid}:{room}:items:{item}:rid", params["rid"])

            await redis.rpush(f"rooms:{client.uid}:{room}:items:{item}",
                              params["x"], params["y"], params["z"], params["d"])
            
            if self.rooms:
                items = await self.get_items(client.uid, room)

                old_room, = [r for r in self.rooms["r"] if r["id"] == room]
                lev, name = old_room["lev"], old_room["nm"]

                idx = self.rooms["r"].index(old_room)
                
                del self.rooms["r"][idx]

                self.rooms["r"].append({"f": items, "w": 13, "id": room,
                                        "lev": lev, "l": 13, "nm": name})
        
            await self.add_rating(params["tpid"])

        async def update_item(self, item):
            client = self.client
            redis = client.serv.redis

            room = client.room.split("_")

            item_id = item["tpid"], str(item["oid"])
            item_id = "_".join(item_id)

            items = await redis.smembers(f"rooms:{client.uid}:{room[2]}:items")

            if item_id not in items:
                await self.add_item(item, room[2])
                return

            await redis.delete(f"rooms:{client.uid}:{room[2]}:items:{item_id}")
            await redis.rpush(f"rooms:{client.uid}:{room[2]}:items:{item_id}",
                                       item["x"], item["y"], item["z"], item["d"])

            if self.rooms:
                items = await self.get_items(client.uid, room[2])
                
                old_room, = [r for r in self.rooms["r"] if r["id"] == room[2]]
                lev, name = old_room["lev"], old_room["nm"]

                idx = self.rooms["r"].index(old_room)
                
                del self.rooms["r"][idx]

                self.rooms["r"].append({"f": items, "w": 13, "id": room[2],
                                        "lev": lev, "l": 13, "nm": name})

        async def del_item(self, item, add=True):
            client = self.client
            redis = client.serv.redis

            room = client.room.split("_")

            if "lid" in item:
                item["oid"] = item["lid"]
                del item["lid"]

            params: dict = item

            item = params["tpid"], str(params["oid"])
            item = "_".join(item)

            items = await redis.smembers(f"rooms:{client.uid}:{room[2]}:items")
           
            if item not in items: return

            options = await redis.smembers(f"rooms:{client.uid}:{room[2]}:items:{item}:options")

            for op in options:
                await redis.delete(f"rooms:{client.uid}:{room[2]}:items:{item}:{op}")

            await redis.delete(f"rooms:{client.uid}:{room[2]}:items:{item}:options")
            await redis.srem(f"rooms:{client.uid}:{room[2]}:items", item)
            await redis.delete(f"rooms:{client.uid}:{room[2]}:items:{item}")

            if self.rooms:
                items = await self.get_items(client.uid, room[2])
                
                old_room, = [r for r in self.rooms["r"] if r["id"] == room[2]]
                lev, name = old_room["lev"], old_room["nm"]

                idx = self.rooms["r"].index(old_room)
                
                del self.rooms["r"][idx]

                self.rooms["r"].append({"f": items, "w": 13, "id": room[2],
                                        "lev": lev, "l": 13, "nm": name})

            await self.add_rating(params["tpid"], incr=False)
            
            if not add: return

            await client.inv.add(params["tpid"], "frn", 1)

        async def replace_door(self, item):
            client = self.client
            room = client.room.split("_")

            items, = [r for r in self.rooms["r"] if r["id"] == room[2]]
            items  = items["f"]

            found: dict = None

            for tmp in items:
                layout_id = tmp["lid"]

                if layout_id == item["oid"]:
                    found = tmp
                    break

            if found is None: return

            await self.del_item(found)

            found["tpid"] = item["tpid"]

            await client.inv.take(item["tpid"], 1)

            await self.add_item(found, room[2])

        async def update(self):
            client = self.client
            room = client.room.split("_")

            room, = [r for r in self.rooms["r"] if r["id"] == room[2]]

            for uid in client.serv.onl:
                tmp = client.serv.onl[uid]

                if tmp.room == client.room:
                    await tmp.send({"data": {"rm": room},
                                    "command": "h.r.rfr"}, 34)

        async def rename(self, room, name):
            uid: str = self.client.uid

            room, = [r for r in self.rooms["r"] if r["id"] == room]
            index: int = self.rooms["r"].index(room)
            
            del self.rooms["r"][index]

            room["nm"] = name

            self.rooms["r"].append(room)
            
            await redis.lset(f"rooms:{uid}:{room}", 0, name)

        def get_prefix(self, room):
            room = room.split("_")[0]

            match room:
                case "house": return "h"
                case  "work": return "w"
                case       _: return "o"

        async def add_rating(self, item, incr=True):
            client = self.client
            server = client.serv

            if item not in server.furniture: return

            rating: int = int(server.furniture[item]["rating"])
            
            rating = rating if incr else -rating

            await client.ci.set("hrt", rating, mode=True)
