#!/bin/bash
# NQ Trading Bot launcher for local machine
# Run this on your Mac with Rithmic connection

cd "$(dirname "$0")"

# Load credentials
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check credentials
if [ -z "$RITHMIC_USER" ]; then
    echo "Error: RITHMIC_USER not set in .env"
    exit 1
fi

# Run the bot
echo "Starting NQ Trading Bot..."
echo "  Mode: $1"
echo "  Broker: $2"
echo ""

python3 main.py --mode "$1" --broker "$2" --interval 15
