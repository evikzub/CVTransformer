#!/bin/bash
set -e

# Activate virtual environment
source .venv/bin/activate

# Control flags
RUN_MODE=${RUN_MODE:-unit}  # Options: unit, integration, e2e
STREAMLIT_PORT=${STREAMLIT_PORT:-8501}

if [ "$RUN_MODE" = "unit" ]; then
    echo "Running unit tests..."
    pytest tests/unit

elif [ "$RUN_MODE" = "integration" ]; then
    echo "Running integration tests..."
    pytest tests/integration

elif [ "$RUN_MODE" = "e2e" ]; then
    echo "Running E2E tests..."

    # Start Streamlit in background
    echo "Starting Streamlit server..."
    streamlit run app.py --server.port $STREAMLIT_PORT &
    STREAMLIT_PID=$!

    # Wait a few seconds to let the app boot
    sleep 5

    # Run your E2E tool (e.g., Playwright, Selenium, etc.)
    pytest tests/e2e

    # Kill Streamlit after test run
    kill $STREAMLIT_PID

else
    echo "Unknown RUN_MODE: $RUN_MODE"
    exit 1
fi
