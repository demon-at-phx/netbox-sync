import configparser
import os

def load_config(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Basic validation
    required_sections = ['General', 'Netbox', 'PDQ']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section in config: {section}")
            
    return config
