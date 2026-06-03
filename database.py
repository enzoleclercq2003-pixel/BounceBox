# -*- coding: utf-8 -*-
import os
import json


def get_all_profiles():
    if not os.path.exists("data_game.json"):
        return {}
    with open("data_game.json", "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def charger_profil(pseudo):
    data = get_all_profiles()
    return data.get(pseudo, {"victoires": 0})


def enregistrer_victoire(pseudo):
    data = get_all_profiles()
    if pseudo not in data:
        data[pseudo] = {"victoires": 0}
    data[pseudo]["victoires"] += 1
    with open("data_game.json", "w") as f:
        json.dump(data, f, indent=4)
