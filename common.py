import hashlib

async def check_account(jwt_token, redis):
    auth_token = hashlib.sha256(jwt_token.encode()).hexdigest()
    user_id: str = await redis.get(f"auth:{auth_token}")
    if not user_id:
        user_id = await create_account(auth_token, redis)
    return user_id, auth_token

async def create_account(auth_token, redis):
    user_id: int = await redis.incr("uids")

    await redis.set(f"auth:{auth_token}", str(user_id))
    await redis.set(f"uid:{user_id}:gld", "6")
    await redis.set(f"uid:{user_id}:slvr", "1000")
    await redis.set(f"uid:{user_id}:enrg", "100")
    await redis.set(f"uid:{user_id}:wearing", "casual")
    await redis.set(f"uid:{user_id}:role", "1")

    await redis.set(f"uid:{user_id}:dr", "1")
    await redis.set(f"uid:{user_id}:vexp", "0")
    await redis.set(f"uid:{user_id}:ceid", "0")
    await redis.set(f"uid:{user_id}:cmid", "0")
    await redis.set(f"uid:{user_id}:exp", "670")
    await redis.set(f"uid:{user_id}:vip", "0")
    await redis.set(f"uid:{user_id}:crt", "0")
    await redis.set(f"uid:{user_id}:hrt", "0")

    return str(user_id)