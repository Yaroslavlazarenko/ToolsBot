# AI-Powered Telegram Bot

A sophisticated Telegram bot that combines Google Gemini AI capabilities with intelligent request routing and YouTube video analysis. The bot automatically determines the complexity of user requests and routes them to appropriate AI models for optimal response quality and speed.

## 🚀 Features

### 🤖 Intelligent Request Routing
- **Smart Dispatcher**: Automatically analyzes user requests and routes them to the most suitable AI model
- **Dynamic Model Selection**: Uses different Gemini models based on request complexity:
  - **Gemini 2.5 Pro**: For complex, detailed analysis requiring deep reasoning
  - **Gemini 2.5 Flash**: For standard responses with good balance of speed and quality
  - **Gemini 2.5 Flash Lite**: For quick, lightweight responses

### 📹 YouTube Video Analysis
- **Automatic Video Processing**: Detects YouTube URLs and performs comprehensive video analysis
- **Intelligent Segmentation**: Splits long videos into manageable segments for thorough analysis
- **Detailed Reports**: Generates comprehensive text reports with segment-by-segment analysis
- **Multi-format Support**: Handles various YouTube URL formats (youtube.com, youtu.be, etc.)

### ⚡ Performance Optimization
- **Rate Limiting**: Built-in sliding window rate limiting for API calls
- **Concurrent Processing**: Asynchronous processing for multiple video segments
- **Resource Management**: Automatic cleanup of temporary files and segments
- **Error Handling**: Robust error handling with graceful degradation

### 🛡️ Reliability Features
- **Automatic Retry Logic**: Handles temporary API failures
- **File Management**: Automatic cleanup of downloaded videos and generated reports
- **Memory Efficient**: Streams large files and processes them in chunks
- **Telegram Integration**: Full integration with Telegram's message handling

## 🏗️ Architecture

The bot follows a modular architecture with clear separation of concerns:

```
├── agents/
│   ├── orchestrator_agent.py    # Main orchestration logic
│   └── router_agent.py          # Request routing and classification
├── services/
│   └── gemini_service.py        # Google Gemini API integration
├── use_cases/
│   └── function_handler.py      # Business logic handlers
├── telegram/
│   ├── handlers/                # Telegram message handlers
│   ├── responder.py            # Response formatting and sending
│   └── utils/                  # Telegram utilities
├── utils/
│   ├── download_yt_video.py    # YouTube video downloading
│   └── video_cutter.py         # Video segmentation
└── core/
    ├── enums.py                # Model definitions and constants
    ├── limiter.py              # Rate limiting implementation
    └── schemas.py              # Data validation schemas
```

## 📋 Requirements

### System Dependencies
- **Python 3.8+**

### Python Dependencies
```
google-genai
aiogram>=3.0.0
pydantic-settings
yt-dlp
ffmpeg-python
```

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Yaroslavlazarenko/ToolsBot.git
cd telegram-ai-bot
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration

Create a `.env` file in the project root:
```env
BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_google_gemini_api_key_here
```

#### Getting Your API Keys:

**Telegram Bot Token:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` command to create a new bot
3. Follow the instructions and copy the provided token

**Google Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

### 5. Run the Bot
```bash
# Make sure virtual environment is activated
python main.py
```

> **Note**: Always activate your virtual environment before running the bot:
> - Windows: `venv\Scripts\activate`
> - macOS/Linux: `source venv/bin/activate`

## 🎯 Usage

### Basic Text Queries
Simply send any text message to the bot. The bot will automatically:
- Analyze the complexity of your request
- Route it to the appropriate AI model
- Return a tailored response

**Examples:**
- `"What's the weather like?"` → Quick response using Flash Lite
- `"Explain quantum computing in detail"` → Comprehensive response using Pro model

### YouTube Video Analysis
Send a message containing a YouTube URL along with your analysis request:

**Examples:**
- `"Analyze this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ"`
- `"What are the main topics discussed in this video? https://youtu.be/dQw4w9WgXcQ"`
- `"Summarize the key points: https://youtube.com/watch?v=dQw4w9WgXcQ"`

The bot will:
1. Download the video
2. Split it into segments (10-minute chunks)
3. Analyze each segment using AI
4. Generate a comprehensive report
5. Send the report as a document file

### Language Support
The bot automatically detects and responds in the same language as your request, unless you specifically ask for a response in another language.

## ⚙️ Configuration

### Model Selection
The bot uses three routing categories:
- **Light Response**: For simple, quick queries
- **Hard Response**: For complex, detailed analysis
- **Video Analysis**: For YouTube video processing

### Rate Limiting
Built-in rate limits per model (per minute) for **free tier**:
- **Gemini 2.5 Pro**: 6 requests
- **Gemini 2.5 Flash**: 11 requests
- **Gemini 2.5 Flash Lite**: 16 requests

> **Note**: These limits are configured for Google Gemini free tier usage. If you have a paid plan, you can adjust the limits in `core/enums.py`

### Video Processing
- **Segment Length**: 10 minutes (600 seconds)
- **Supported Formats**: MP4, with automatic conversion
- **Maximum Processing**: No hard limit, but longer videos take more time

## 🔍 Troubleshooting

### Common Issues

**Bot not responding:**
- Check if your bot token is correct
- Ensure the bot is not blocked by Telegram
- Verify your internet connection

**Video analysis failing:**
- Ensure Python dependencies are installed: `pip install -r requirements.txt`
- Check if yt-dlp is up to date: `pip install -U yt-dlp`
- Verify the YouTube URL is accessible
- Make sure your virtual environment is activated

**API errors:**
- Check your Gemini API key
- Ensure you haven't exceeded free tier rate limits
- Verify your Google Cloud project has the necessary permissions
- Consider upgrading to a paid plan for higher limits if needed

**Memory issues:**
- Long videos require significant processing power
- Consider running on a server with adequate RAM
- Monitor disk space for temporary files

### Logs
The bot provides detailed logging. Check the console output for specific error messages and debugging information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for powerful language models
- aiogram for excellent Telegram Bot API wrapper
- yt-dlp Python library for reliable YouTube video downloading
- ffmpeg-python for video processing capabilities

---

**Note**: This bot processes videos and makes API calls using Google Gemini's free tier by default. The rate limits are configured accordingly. Monitor your usage and consider upgrading to a paid plan if you need higher limits or want to avoid potential costs from exceeding free tier quotas.
