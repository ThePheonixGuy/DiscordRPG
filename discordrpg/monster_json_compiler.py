import json
from copy import deepcopy

new_monsters = {}

monster_list = []
json_data = open("5Emonster.json", mode="r")
monster_list = json.load(json_data)
counter = 0
for monster in monster_list:
    current_monster = monster_list[counter]
    level = current_monster["challenge_rating"]
    if level not in new_monsters.keys():
        new_monsters[level] = {}
    monster_name = current_monster["name"]
    img_url = ""
    size = current_monster["size"]
    monster_type = current_monster["type"]
    
    hp = current_monster["hit_points"]
    experience = hp
    atk_melee = current_monster["strength"]
    atk_magic = current_monster["wisdom"]
    if "actions" in current_monster.keys():
        attack_list = current_monster["actions"]
        for attack in attack_list:
            attack_name = attack['name']
            attacks = {attack_name : attack}
    else:
        attacks = ""
    speed = current_monster["speed"]
    atk_range = "" #no value. needs to be based off the attacks
    agility = current_monster["dexterity"]
    defense = current_monster["armor_class"]

    # grab the name of the current entry in the 5E list, to be used as the primary key in the json

    # add your attributes here with their values.

    #naming when adding it to the dict below:
    # new_monster[monster_name] = {"Attribute name here" : value, "name" : value}
    # creates new dict entry, with key as name and value as a dict. <- Empty dict btw
    new_monsters[level][monster_name] = {"Name": monster_name, "Img_Url" : img_url, "level" : level, "size" : size, "type" : monster_type, "hp" : hp, "exp" : experience, "atk_melee" : atk_melee, "atk_magic" : atk_magic, "atk_range" : atk_range, "attacks" : attacks, "speed" : speed, "agility" : agility, "defense" : defense}

    counter += 1

# save new_monsters to a new json
with open("output.json", encoding='utf-8', mode="w") as f:
    json.dump(new_monsters, f, indent=4,sort_keys=True, separators=(',',' : '))
