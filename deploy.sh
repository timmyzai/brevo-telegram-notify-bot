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

echo "Injecting environment variables from .env into $STAGE stage..."
python initial_zappa.py "$STAGE"
if [ $? -ne 0 ]; then
    echo "❌ Injection failed. Exiting."
    exit 1
fi

echo "Running: zappa $ACTION $STAGE"
zappa $ACTION $STAGE

rm zappa_settings.json
echo "✅ Deployment finished."
