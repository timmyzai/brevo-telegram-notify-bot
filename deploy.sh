#!/bin/bash

echo "Select deployment stage:"
select STAGE in "staging" "production"; do
    if [[ -n "$STAGE" ]]; then
        echo "Selected stage: $STAGE"
        break
    else
        echo "Invalid option. Please try again."
    fi
done

echo "Select deployment action:"
select ACTION in "deploy" "update" "quit"; do
    case $ACTION in
        deploy|update)
            echo "Selected action: $ACTION"
            break
            ;;
        quit)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
done

ENV_FILE=".env.${STAGE}"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ File '$ENV_FILE' not found. Exiting."
    exit 1
fi

TABLE_NAME=$(grep DYNAMODB_TABLE_NAME "$ENV_FILE" | cut -d '=' -f2)
REGION="ap-southeast-1"

echo "Checking DynamoDB table '$TABLE_NAME'..."
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
    echo "Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name "$TABLE_NAME" --region "$REGION"
    echo "✅ Table created."
else
    echo "✅ Table already exists."
fi

echo "Injecting environment variables from $ENV_FILE into $STAGE stage..."
python initial_zappa.py "$STAGE" "$ENV_FILE"
if [ $? -ne 0 ]; then
    echo "❌ Injection failed. Exiting."
    exit 1
fi

echo "Running: zappa $ACTION $STAGE"
zappa $ACTION $STAGE

rm zappa_settings.json
echo "✅ Deployment finished."
