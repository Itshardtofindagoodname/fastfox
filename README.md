# FastFox: AI-Powered File Ninja & Command Line Whiz 🦊💨

Unleash the power of AI to organize files at lightning speed, get smart command suggestions, and supercharge your coding! FastFox harnesses cutting-edge models from Groq and Hugging Face to bring order to chaos and boost your productivity.

![FastFox Logo](fox.ico)

## 🚀 Quick Start

1. Clone the repo: `git clone https://github.com/Itshardtofindagoodname/fastfox.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run initial setup: `python fastfox.py`
4. Start organizing: `python fastfox.py organize <folder_path>`

## 🌟 Key Features

- **Blazing-Fast File Organization**: Categorizes files 10x faster than manual sorting.
- **AI-Powered Command Suggestions**: Get context-aware CLI suggestions in milliseconds.
- **Intelligent Code Generation**: Create or modify code with pinpoint accuracy.
- **Smart History Management**: Remember or forget commands on demand.
- **Seamless Setup**: One-click environment setup with the `.exe` version.

## 🛠️ Installation

### Requirements

- Python 3.7+
- Windows OS
- Hugging Face and Groq API keys

### Detailed Setup

1. **Clone this repository**:
   ```bash
   git clone https://github.com/Itshardtofindagoodname/fastfox.git
   cd fastfox
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Initial Setup**:
   ```bash
   python fastfox.py
   ```
   You'll be prompted for your Hugging Face and Groq API keys on first run.

4. **EXE Version**:
   Simply run the `.exe`, enter your API keys, and FastFox handles the rest automatically.

## 🔑 API Key Information

- **Groq**: [Get your API key](https://console.groq.com/keys)
- **Hugging Face**: [Generate your token](https://huggingface.co/settings/tokens)

### Rate Limits

- **Hugging Face Free Tier**: 1,000 requests/day (max 50/hour)
- **Groq Free Tier**: 14,400 requests/day (max 30/minute)

For higher limits, check out their paid plans.

## 🧠 AI Models

- **Salesforce/blip-image-captioning-large**: Image captioning
- **llama3-8b-8192**: Command and code suggestions
- **mixtral-8x7b-32768**: Code generation

## Usage

### Commands

#### Organize Files
Organize files in a specified folder by analyzing their content and sorting them into categorized subfolders.

```bash
python fastfox.py organize <folder_path>
```

Example:
```bash
python fastfox.py organize C:\Users\Icarus\Pictures
```

#### Command Suggestions
Get AI-generated command-line suggestions.

```bash
python fastfox.py command "<query>"
```

Example:
```bash
python fastfox.py command "List all files in a directory"
```

#### Code Generation and Suggestions
Generate or suggest code for a given file.

```bash
python fastfox.py codeit <file_path>
```

Example:
```bash
python fastfox.py codeit C:\Users\Icarus\Projects\main.py
```

You will be prompted to choose between code generation or suggestion.
- Generation: Generates code based on the provided file.
- Suggestion: Suggests changes to the provided file.

#### Forget History
Forget previous command history or clear all stored information.

```bash
python fastfox.py forget <all|command|codeit|organize>
```

Example:
```bash
python fastfox.py forget all
```

## 🚄 Performance

FastFox outperforms traditional file explorers:
- Organizes 50+ files in under 30 seconds
- Generates command suggestions in <1s
- Provides code insights 5x faster than manual review

## 🙏 Acknowledgements
- [Hugging Face](https://huggingface.co) for their exceptional models
- [Groq](https://groq.com) for powering FastFox's lightning-fast AI suggestions

## 📄 License

This project is licensed under the MIT License.

---

Ready to revolutionize your file management and coding workflow? Get started with FastFox today! 🚀🦊
