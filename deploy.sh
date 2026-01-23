#!/bin/bash
set -e
trap 'rm -f zappa_settings.json' EXIT

VENV_DIR="venv"
REGION="ap-southeast-1"

# Ensure venv exists and activate it
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "Virtual environment ready."
else
    source "$VENV_DIR/bin/activate"
fi

# Select stage
echo "Select deployment stage:"
select STAGE in "staging" "production"; do
    [ -n "$STAGE" ] && break
done

# Load env file
ENV_FILE=".env.${STAGE}"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found."
    exit 1
fi

# Ensure DynamoDB table exists
TABLE_NAME=$(grep DYNAMODB_TABLE_NAME "$ENV_FILE" | cut -d '=' -f2)
if ! aws dynamodb describe-table --table-name "$TABLE_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "Creating DynamoDB table '$TABLE_NAME'..."
    aws dynamodb create-table \
        --table-name "$TABLE_NAME" \
        --attribute-definitions \
            AttributeName=email,AttributeType=S \
            AttributeName=event_type,AttributeType=S \
        --key-schema \
            AttributeName=email,KeyType=HASH \
            AttributeName=event_type,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
fi

# Generate zappa_settings.json from env
python initial_zappa.py "$STAGE" "$ENV_FILE"

# Deploy or update
if zappa status "$STAGE" > /dev/null 2>&1; then
    zappa update "$STAGE"
else
    zappa deploy "$STAGE"
fi

echo "Done."
