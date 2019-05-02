from core.config.config_loader import load_config


def get_bot_configuration():
    bot_config = load_config().get("bot", {})
    return {
        "bot_token": bot_config.get("token"),
    }
