# WraithWatch 🦹‍♂️

A Discord bot for real-time privacy & security threat detection, powered by AI. WraithWatch monitors, analyzes, and summarizes privacy and security incidents from Reddit, delivering actionable insights directly to your Discord server.

## 🌟 Features

- **Real-time Monitoring**: Tracks posts from key security & privacy subreddits
  - r/privacy
  - r/hacking
  - r/netsec
  - r/scams
  - r/socialengineering

- **AI-Powered Analysis**: Leverages Groq's LLaMA3 model for:
  - 📝 Concise summaries of complex incidents
  - 🏷️ Threat classification and tagging
  - 💡 Actionable security tips and insights
  - 🔄 Pattern detection across incidents

- **Discord Integration**: Seamless interaction through slash commands
  - `/latest` - View recent incidents from a subreddit
  - `/ask` - ask a sepefic question to be answered by our AI assistant
  - `/ping` - Check bot latency

## 🛠️ Tech Stack

- **Core**: Python
- **Web Scraping**: BeautifulSoup4
- **AI/ML**: Groq API (LLaMA3)
- **Bot Framework**: discord.py
- **Environment**: dotenv

## ⚙️ Prerequisites

- Python 3.8+
- Discord Bot Token
- Groq API Key

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wraithwatch.git
cd wraithwatch
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
GROQ_API_KEY=your_groq_api_key
```

## 🚀 Usage

1. Start the bot:
```bash
python main.py
```

2. In Discord, use the following commands:
- `/latest [subreddit]` - Get the 5 latest posts from a specific subreddit
- `/ping` - Check bot latency

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational and informational purposes only. Always verify security information from trusted sources and consult with security professionals for critical decisions.

## 🙏 Acknowledgments

- Reddit communities for sharing security knowledge
- Discord.py developers
- Groq team for AI capabilities 