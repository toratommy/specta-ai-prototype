# Simple authentication for login

import yaml

def load_config():
    with open("config.yml", "r") as file:
        return yaml.safe_load(file)

def authenticate(username, password):
    config = load_config()
    credentials = config["credentials"]
    return username == credentials["username"] and password == credentials["password"]
