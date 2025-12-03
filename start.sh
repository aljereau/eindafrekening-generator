#!/bin/bash

echo "========================================"
echo "  RyanRent Intelligence Bot - Docker"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file with your API keys:"
    echo "  ANTHROPIC_API_KEY=your_key_here"
    echo "  OPENAI_API_KEY=your_key_here"
    echo ""
    exit 1
fi

echo "Starting RyanRent Intelligence Bot..."
echo ""

docker-compose up --build
