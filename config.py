import os
from dotenv import load_dotenv
from typing import Optional


def load_env_variable(variable_name: str, default: Optional[str] = None) -> str:
    value = os.getenv(variable_name, default)
    if value is None:
        raise EnvironmentError(f"Environment variable '{variable_name}' is not set.")
    return value


def load_environment_variables() -> dict:
    if os.getenv("AWS_EXECUTION_ENV") is None:
        load_dotenv()

    env_vars = {
        "TELEGRAM_BOT_TOKEN": load_env_variable("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": load_env_variable("TELEGRAM_CHAT_ID"),
        "PORT": load_env_variable("PORT", "6666"),
        "ENVIRONMENT": load_env_variable("ENVIRONMENT"),
    }

    return env_vars


environment_variables = load_environment_variables()

TELEGRAM_BOT_TOKEN = environment_variables["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = environment_variables["TELEGRAM_CHAT_ID"]
PORT = int(environment_variables["PORT"])
ENVIRONMENT = environment_variables["ENVIRONMENT"]
