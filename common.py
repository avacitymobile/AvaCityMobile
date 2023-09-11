import hashlib

async def check_account(jwt_token, redis):
    auth_token = hashlib.sha256(jwt_token.encode()).hexdigest()
    user_id: str = await redis.get(f"auth:{auth_token}")
    if not user_id:
        user_id = await create_account(auth_token, redis)
    return user_id, auth_token

async def create_account(auth_token, redis):
    user_id = await redis.incr("uids")
    user_key = f"uid:{user_id}"

    batch = {
        f"auth:{auth_token}": str(user_id),
        f"{user_key}:gld": "6",
        f"{user_key}:slvr": "1000",
        f"{user_key}:enrg": "100",
        f"{user_key}:wearing": "casual",
        f"{user_key}:role": "1",
        f"{user_key}:dr": "1",
        f"{user_key}:vexp": "0",
        f"{user_key}:ceid": "0",
        f"{user_key}:cmid": "0",
        f"{user_key}:exp": "670",
        f"{user_key}:vip": "0",
        f"{user_key}:crt": "0",
        f"{user_key}:hrt": "0",
    }

    await redis.mset(batch)

    return str(user_id)