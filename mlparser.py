import yaml


CONFIG_PATH:  str = "config_yaml"

BOY_CLOTHES_PATH:  str = f"{CONFIG_PATH}/clothes/boy.yaml"
GIRL_CLOTHES_PATH: str = f"{CONFIG_PATH}/clothes/girl.yaml"

CRAFT_PATH:     str = f"{CONFIG_PATH}/craft.yaml"
FURNITURE_PATH: str = f"{CONFIG_PATH}/furniture.yaml"
GAME_PATH:      str = f"{CONFIG_PATH}/game.yaml"
RELATIONS_PATH: str = f"{CONFIG_PATH}/relations.yaml"

RELATIONS_PROGRESS_PATH: str = f"{CONFIG_PATH}/relations_progress.yaml"


def parse_clothes():
    clothes: dict = {}
    clothes.update({"boy": yaml.unsafe_load(open(BOY_CLOTHES_PATH, "r"))})
    clothes.update({"girl": yaml.unsafe_load(open(GIRL_CLOTHES_PATH, "r"))})
    return clothes

def parse_craft():
    return yaml.unsafe_load(open(CRAFT_PATH, "r"))

def parse_furniture():
    return yaml.unsafe_load(open(FURNITURE_PATH, "r"))

def parse_game():
    return yaml.unsafe_load(open(GAME_PATH, "r"))

def parse_relations():
    return yaml.unsafe_load(open(RELATIONS_PATH, "r"))

def parse_relations_progress():
    return yaml.unsafe_load(open(RELATIONS_PROGRESS_PATH, "r"))
