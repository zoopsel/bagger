import tomllib

from pathlib import Path


CONFIG_PATH = Path("config.toml")

SMTP_SERVER_ADDRESS: str = ""
EMAIL_SENDER: str = ""
EMAIL_TO: str = ""
EMAIL_CC: str = ""
PASSWORD: str = ""


def load_config():
    global SMTP_SERVER_ADDRESS, EMAIL_SENDER, EMAIL_TO, EMAIL_CC, PASSWORD

    with open(CONFIG_PATH, "rb") as fp:
        config_raw = tomllib.load(fp)

    SMTP_SERVER_ADDRESS = str(config_raw["smtp_server_address"])
    EMAIL_SENDER = str(config_raw["email_sender"])
    EMAIL_TO = str(config_raw["email_to"])
    EMAIL_CC = str(config_raw["email_cc"])
    PASSWORD = str(config_raw["password"])

    if "" in [SMTP_SERVER_ADDRESS, EMAIL_SENDER, EMAIL_TO, PASSWORD]:
        raise Exception("Config is not filled in correctly.")


def reload_config():
    load_config()


load_config()
