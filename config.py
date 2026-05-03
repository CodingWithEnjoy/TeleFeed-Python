import json
import os

class Config:
    @staticmethod
    def load_channels():
        config_path = "config.json"
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"{config_path} not found")
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        if "channels" not in config or not isinstance(config["channels"], list):
            raise ValueError("Invalid config.json: 'channels' list is required")
            
        return config["channels"]