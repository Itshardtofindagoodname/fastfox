
# FastFox: Blazing-Fast AI File Organizer & Command Line Assistant 🦊

FastFox is a powerful, AI-driven tool designed to streamline file organization, suggest commands, and even generate or modify code. Powered by Groq and Hugging Face models, FastFox performs all tasks quickly and efficiently on your local machine.

![FastFox Logo](fox.ico)

## Key Features

- **File Organization**: Automatically categorizes images, PDFs, CSVs, Excel files, and Word documents into folders based on their content.
- **Command Suggestions**: Provides intelligent, context-aware command-line suggestions powered by the Groq API.
- **Code Generation and Suggestions**: Uses advanced AI to generate code or suggest changes with precision.
- **History Management**: Remembers or forgets specific commands based on your instructions.
- **Batch Setup**: The `.exe` version sets up your system’s environment variables and PATH automatically.

## Installation

### Requirements

- Python 3.7 or above
- Windows OS
- Hugging Face and Groq API keys

### Setup

1. **Clone this repository**:
   ```bash
   git clone https://github.com/yourusername/fastfox.git
   cd fastfox
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Initial Setup**:
   On your first run, FastFox will ask for your API keys for Hugging Face and Groq. These keys are saved locally for future use.
   
   ```bash
   python fastfox.py
   ```

4. **EXE Version**:
   No command input is needed. Simply run the `.exe`, enter your API keys, and FastFox will automatically set up everything.

## API Key Information

- **Groq**: [Get your API key](https://console.groq.com/keys)
- **Hugging Face**: [Generate your token](https://huggingface.co/settings/tokens)

### Rate Limits

- **Hugging Face Free Tier**: 1,000 requests per day.(Maximum 50 requests per hour.) [Click here to know more](https://huggingface.co/docs/api-inference/rate-limits).
- **Groq Free Tier**: 14,400 requests per day.(Maximum 30 requests per minute.) [Click here to know more](https://groq.com/pricing).

They have a generous free tier, but for higher limits, upgrade to a paid plan on their respective websites.

## Models Used

- **Salesforce/blip-image-captioning-large**: Image captioning model used to generate captions for images.
- **llama3-8b-8192**: Text generation model used to generate command suggestions and code suggestions.
- **mixtral-8x7b-32768**: Text generation model used to generate code.

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

### Performance
FastFox is designed to work faster than traditional file explorers, organizing files in the blink of an eye with asynchronous processing. Command suggestions and code generation also leverage cutting-edge AI to minimize latency.

## Documentation

Detailed documentation is available [here](https://your-docs-url.com) (Coming Soon).

## Acknowledgements
- Huge thanks to [Hugging Face](https://huggingface.co) for their top-notch models.
- Special thanks to [Groq](https://groq.com) for powering the AI behind FastFox's command and code suggestions.

## License

This project is licensed under the MIT License.

---
