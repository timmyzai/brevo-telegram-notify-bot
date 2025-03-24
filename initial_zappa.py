import os
import json
import sys
from shutil import copyfile
from dotenv import dotenv_values

TEMPLATE = "zappa_settings.template.json"
TARGET = "zappa_settings.json"


def inject_env(stage_name: str):
    # Load the template with the key "env"
    with open(TEMPLATE, "r") as f:
        template_config = json.load(f)

    if "env" not in template_config:
        print("❌ Error: 'env' key not found in template.")
        sys.exit(1)

    # Rename "env" to the actual stage
    zappa_config = {
        stage_name: template_config["env"]
    }

    # Load .env variables
    env = dotenv_values(".env")
    zappa_config[stage_name]["environment_variables"] = env

    # Write to target zappa_settings.json
    with open(TARGET, "w") as f:
        json.dump(zappa_config, f, indent=2)

    print(f"✅ Created '{TARGET}' with stage '{stage_name}' and injected environment variables.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inject_env_to_zappa.py <stage>")
        sys.exit(1)

    inject_env(sys.argv[1])
