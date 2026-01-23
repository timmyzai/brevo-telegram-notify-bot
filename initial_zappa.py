import json
import sys

TEMPLATE = "zappa_settings.template.json"
TARGET = "zappa_settings.json"


def inject_env(stage_name: str, env_file: str):
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

    # Load environment-specific variables
    env = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()

    # Override ENVIRONMENT with capitalized stage name (matches Brevo tags)
    env["ENVIRONMENT"] = stage_name.capitalize()

    zappa_config[stage_name]["environment_variables"] = dict(env)

    # Write to target zappa_settings.json
    with open(TARGET, "w") as f:
        json.dump(zappa_config, f, indent=2)

    print(f"✅ Created '{TARGET}' with stage '{stage_name}' and injected environment variables.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python initial_zappa.py <stage> <env_file>")
        sys.exit(1)

    inject_env(sys.argv[1], sys.argv[2])
