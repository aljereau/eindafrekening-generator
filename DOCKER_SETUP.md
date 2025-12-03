# 🏠 RyanRent Intelligence - Docker Setup

## Quick Start (Windows)

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Setup API Keys**
   - Create a file named `.env` in this folder
   - Add your API keys:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   OPENAI_API_KEY=sk-xxxxx
   ```

3. **Run the Application**
   - Double-click `start.bat`
   - Wait for the build to complete (first time takes ~2-3 minutes)
   - The chatbot will start automatically

## Quick Start (Mac/Linux)

1. **Install Docker**
   - Mac: Download Docker Desktop from https://www.docker.com/products/docker-desktop
   - Linux: `sudo apt-get install docker docker-compose`

2. **Setup API Keys**
   - Create a file named `.env` in this folder
   - Add your API keys:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   OPENAI_API_KEY=sk-xxxxx
   ```

3. **Run the Application**
   ```bash
   ./start.sh
   ```

## Manual Docker Commands

### Build the image
```bash
docker-compose build
```

### Start the bot
```bash
docker-compose up
```

### Stop the bot
Press `Ctrl+C` or run:
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up --build
```

## Troubleshooting

### "Docker is not running"
- **Windows**: Open Docker Desktop from the Start menu
- **Mac**: Open Docker Desktop from Applications
- **Linux**: Run `sudo systemctl start docker`

### "Permission denied" (Linux)
```bash
sudo usermod -aG docker $USER
# Log out and log back in
```

### "Port already in use"
```bash
docker-compose down
docker-compose up
```

### Database/Output not persisting
Check that these folders exist:
- `database/`
- `Eindafrekening/output/`

## Features

✅ **Cross-platform**: Works on Windows, Mac, and Linux  
✅ **No Python installation needed**: Everything runs in Docker  
✅ **Persistent data**: Database and reports are saved on your computer  
✅ **Latest AI models**: Claude 4.5, GPT-4o, and local Ollama support  
✅ **Interactive model selection**: Choose your AI model at startup  

## What's Included

- **RyanRent Intelligence Bot**: AI-powered chatbot for property management
- **Database**: SQLite database for houses, clients, and bookings
- **Report Generator**: Automated settlement report generation
- **Multi-model support**: Claude, GPT, and Ollama

## Getting Help

If you encounter issues:
1. Check that Docker Desktop is running
2. Verify your `.env` file has valid API keys
3. Try rebuilding: `docker-compose up --build`
4. Contact Aljereau for support
