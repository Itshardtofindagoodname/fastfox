import os
import re
import sys
import csv
import docx
import json
import base64
import winreg
import PyPDF2
import requests
import pythoncom
import subprocess
import pandas as pd
from groq import Groq
import win32com.client
from io import StringIO
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from contextlib import redirect_stderr, redirect_stdout

#setting up conversation history for the bot's memory
CONVERSATION_HISTORY = []
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".fastfox", "history.json")

# If you want to use the exe version of the application, this setup essentially copies the batch files to the user's scripts and system paths directly once it's executed.
#If you're running this code however, you can comment out this setup_batch_files() function and remove it from main too
#And just run python fastfox.py <command/codeit/organize/forget> <query> in the terminal.

#Setting up batch files and PATH so that everything works out of the box.
def setup_batch_files():
    batch_commands = {
        "organize": "fastfox.exe organize",
        "codeit": "fastfox.exe codeit",
        "command": "fastfox.exe command",
        "forget": "fastfox.exe forget"
    }
    scripts_dir = os.path.join(os.environ['APPDATA'], 'FastFoxScripts')
    os.makedirs(scripts_dir, exist_ok=True)

    try:
        result = subprocess.run(["where", "fastfox.exe"], capture_output=True, text=True, check=True)
        fastfox_path = result.stdout.strip().split('\n')[0]
        fastfox_dir = os.path.dirname(fastfox_path)
    except subprocess.CalledProcessError:
        print("Error: fastfox.exe not found in PATH. Please ensure it's installed and accessible.")
        return

    for cmd in batch_commands.items():
        with open(os.path.join(scripts_dir, f"{cmd}.bat"), 'w') as batch_file:
            batch_file.write(f'@echo off\n"{fastfox_path}" {cmd} %*')

    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_ALL_ACCESS)
    current_path = winreg.QueryValueEx(key, "Path")[0]

    paths_to_add = [scripts_dir, fastfox_dir]
    new_paths = [path for path in paths_to_add if path.lower() not in current_path.lower()]

    if new_paths:
        new_path = f"{current_path};{';'.join(new_paths)}"
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        print("Batch files created and System PATH updated. Restart your command prompt for changes to take effect.")
    else:
        print("The specified directories are already in the System PATH.")

    winreg.CloseKey(key)

#Loading conversation history
def load_conversation_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading conversation history: {str(e)}")
    return []

#Saving conversation history
def save_conversation_history():
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump(CONVERSATION_HISTORY, f)
    except Exception as e:
        print(f"Error saving conversation history: {str(e)}")

#Adding a new chat context to the conversation history.
def add_to_history(command_type, query, response):
    CONVERSATION_HISTORY.append({
        'command_type': command_type,
        'query': query,
        'response': response
    })
    save_conversation_history()

#Getting the last 5 chat contexts for a given command type.
def get_context(command_type, query):
    relevant_history = [
        item for item in CONVERSATION_HISTORY 
        if item['command_type'] == command_type
    ]
    return relevant_history[-5:] if relevant_history else []

# Add the forget function
def forget(query: str):
    global CONVERSATION_HISTORY
    
    if query.lower() == 'all':
        # Clear all history
        CONVERSATION_HISTORY = []
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        print("All conversation history has been cleared.")
    else:
        # Clear history for a specific command type
        valid_commands = ['command', 'code', 'organize']
        if query.lower() in valid_commands:
            CONVERSATION_HISTORY = [
                item for item in CONVERSATION_HISTORY 
                if item['command_type'] != query.lower()
            ]
            save_conversation_history()
            print(f"Conversation history for /{query} has been cleared.")
        else:
            print(f"Invalid option. Use 'all' or one of: {', '.join(valid_commands)}")
    
    return True

#Taking user input for huggingface and groq api keys and saving it to the .env file.
def setup_env():
    env_file = os.path.join(os.path.expanduser("~"), ".fastfox", ".env")
    os.makedirs(os.path.dirname(env_file), exist_ok=True)
    
    if not os.path.exists(env_file):
        print("Welcome to FastFox! First-time setup required.")
        groq_api_key = input("Please enter your Groq API key: ").strip()
        hf_token = input("Please enter your Hugging Face API token: ").strip()
        
        with open(env_file, 'w') as f:
            f.write(f"GROQ_API_KEY={groq_api_key}\n")
            f.write(f"HUGGINGFACE_API_TOKEN={hf_token}\n")
        
        print("API keys saved successfully!")
    
    with open(env_file, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            os.environ[key] = value

#downloading nltk(natural language toolkit) packages silently, this is to avoid the annoying nltk download prompts.
#the nltk module is what gives the folder names by picking the most common words in the text.
def silent_nltk_download(package):
    try:
        nltk_data_dir = os.path.join(os.path.expanduser("~"), ".fastfox", "nltk_data")
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        import nltk
        nltk.data.path.append(nltk_data_dir)
        
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            nltk.download(package, download_dir=nltk_data_dir, quiet=True)
    except Exception as e:
        print(f"Error downloading {package}: {e}")

#initializing the groq and huggingface api clients.
def initialize():
    setup_env()
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    hf_token = os.getenv('HUGGINGFACE_API_TOKEN')
    
    if not groq_api_key or not hf_token:
        print("API keys not found. Please run setup again.")
        sys.exit(1)
    
    return Groq(api_key=groq_api_key), {"Authorization": f"Bearer {hf_token}"}

HF_API_URL = "https://api-inference.huggingface.co/models/"

#suggesting command function, it suggests command based on user query. 
#it uses the llama3-8b model for it as it's lightweight and fast and near accurate too.
def suggest_command(query: str, groq_client: Groq):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that suggests command line instructions for various tasks. Provide the command in a code block."
                },
                {
                    "role": "user",
                    "content": f"Suggest a command line instruction for the following task: {query}"
                }
            ],
            model="llama3-8b-8192",
            max_tokens=100
        )
        
        full_response = chat_completion.choices[0].message.content.strip()
        
        command_pattern = re.compile(r"```(?:\w+)?\n(.*?)\n```", re.DOTALL)
        match = command_pattern.search(full_response)
        
        if match:
            command = match.group(1).strip()
            
            if command:
                print(f"Suggested command: {command}")
                
                user_input = input("Do you want to run this command? (y/n): ").lower()
                if user_input == 'y':
                    try:
                        subprocess.run(command, shell=True, check=True)
                        print("Command executed successfully.")
                    except subprocess.CalledProcessError as e:
                        print(f"Error executing command: {e}")
                else:
                    print("Command execution cancelled.")
            else:
                print("Error: No valid command found in the response.")
        else:
            print("Error: Unable to extract command from the response.")
    except Exception as e:
        print(f"Error generating command suggestion: {str(e)}")

#querying huggingface api and returning the response.
def query_huggingface_api(payload, model, hf_headers):
    response = requests.post(HF_API_URL + model, headers=hf_headers, json=payload)
    return response.json()

#simplifying the caption by removing common words.
def simplify_caption(caption: str) -> str:
    tokens = word_tokenize(caption)
    tagged_words = pos_tag(tokens)
    
    nouns = [word for word, pos in tagged_words if pos in ('NN', 'NNS', 'NNP', 'NNPS')]
    
    if not nouns:
        return sanitize_folder_name(tokens[0]) if tokens else "Untitled"
    
    ranked_nouns = sorted(nouns, key=lambda word: (len(word), tokens.index(word)), reverse=True)
    
    most_meaningful_word = ranked_nouns[0]
    
    simplified_word = re.sub(r'[^a-zA-Z0-9]', '', most_meaningful_word)
    if simplified_word.endswith('s') and len(simplified_word) > 3:
        simplified_word = simplified_word[:-1]
    
    return sanitize_folder_name(simplified_word)

#sanitizes the folder name by removing special characters and spaces.
def sanitize_folder_name(folder_name: str) -> str:
    sanitized_name = re.sub(r'[<>:"/\\|?*\n]', '', folder_name)
    return sanitized_name.strip()[:50]

#gets the topic of a pdf file.
def get_pdf_topic(pdf_path: str, groq_client: Groq) -> str:
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes documents and provides a single-word topic."
            },
            {
                "role": "user",
                "content": f"Summarize this text and provide a single-word topic: {text[:1000]}"
            }
        ],
        model="llama3-8b-8192",
        max_tokens=50
    )

    summary = chat_completion.choices[0].message.content.strip()
    folder_name = simplify_caption(summary)    
    return sanitize_folder_name(folder_name)

#gets the topic of an excel file.
def get_excel_topic(excel_path: str, groq_client: Groq) -> str:
    df = pd.read_excel(excel_path)
    column_names = ", ".join(df.columns)
    
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that analyzes Excel files and provides a single-word topic."
            },
            {
                "role": "user",
                "content": f"Analyze these Excel column names and provide a single-word topic: {column_names}"
            }
        ],
        model="llama3-8b-8192",
        max_tokens=50
    )
    
    topic = chat_completion.choices[0].message.content.strip()
    return sanitize_folder_name(topic)

#gets the topic of a csv file.
def get_csv_topic(csv_path: str, groq_client: Groq) -> str:
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252']
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', newline='', encoding=encoding) as file:
                csv_reader = csv.reader(file)
                headers = next(csv_reader, None)
            
            if headers:
                column_names = ", ".join(headers)
                break
        except UnicodeDecodeError:
            continue
    else:
        return "Untitled_CSV"
    
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that analyzes CSV files and provides a single-word topic."
            },
            {
                "role": "user",
                "content": f"Analyze these CSV column names and provide a single-word topic: {column_names}"
            }
        ],
        model="llama3-8b-8192",
        max_tokens=50
    )
    
    topic = chat_completion.choices[0].message.content.strip()
    simplified_topic = simplify_caption(topic)
    return sanitize_folder_name(simplified_topic)

#organizes a folder by moving files to appropriate folders based on their content.
def organize_folder(folder_path: str, groq_client: Groq, hf_headers):
    
    print("Initializing Natural Language Toolkit...")
    silent_nltk_download('punkt')
    silent_nltk_download('averaged_perceptron_tagger')
    print("Running organize...")

    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    categories = ['images', 'pdfs', 'excels', 'csvs', 'docs', 'other_files']
    for category in categories:
        os.makedirs(os.path.join(folder_path, category), exist_ok=True)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            file_extension = os.path.splitext(filename)[1].lower()

            if file_extension in ('.png', '.jpg', '.jpeg', '.gif'):
                process_image(file_path, folder_path, hf_headers)
            elif file_extension == '.pdf':
                process_pdf(file_path, folder_path, groq_client)
            elif file_extension in ('.xls', '.xlsx'):
                process_excel(file_path, folder_path, groq_client)
            elif file_extension == '.csv':
                process_csv(file_path, folder_path, groq_client)
            elif file_extension in ('.doc', '.docx'):
                process_doc_docx(file_path, folder_path, groq_client)
            else:
                move_to_other_files(file_path, folder_path)

#processes a doc/docx file.
def process_doc_docx(file_path: str, base_folder: str, groq_client: Groq):
    try:
        if file_path.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_path.lower().endswith('.doc'):
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            try:
                doc = word.Documents.Open(file_path)
                text = doc.Content.Text
            finally:
                doc.Close()
                word.Quit()
        else:
            raise ValueError("Unsupported file format")

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes documents and provides a single-word topic."
                },
                {
                    "role": "user",
                    "content": f"Summarize this text and provide a single-word topic: {text[:1000]}"
                }
            ],
            model="llama3-8b-8192",
            max_tokens=50
        )

        topic = chat_completion.choices[0].message.content.strip()
        simplified_topic = simplify_caption(topic)
        category_folder = os.path.join(base_folder, 'docs', simplified_topic)
        os.makedirs(category_folder, exist_ok=True)
        new_file_path = os.path.join(category_folder, os.path.basename(file_path))
        os.rename(file_path, new_file_path)
        print(f"Moved {os.path.basename(file_path)} to docs/{simplified_topic} folder")
    except Exception as e:
        print(f"Error processing document {os.path.basename(file_path)}: {str(e)}")
    finally:
        pythoncom.CoUninitialize()

#processes a csv file.
def process_csv(file_path: str, base_folder: str, groq_client: Groq):
    try:
        topic = get_csv_topic(file_path, groq_client)
        category_folder = os.path.join(base_folder, 'csvs', topic)
        os.makedirs(category_folder, exist_ok=True)
        new_file_path = os.path.join(category_folder, os.path.basename(file_path))
        os.rename(file_path, new_file_path)
        print(f"Moved {os.path.basename(file_path)} to csvs/{topic} folder")
    except Exception as e:
        print(f"Error processing CSV {os.path.basename(file_path)}: {str(e)}")

def process_image(file_path: str, base_folder: str, hf_headers):
    try:
        with open(file_path, "rb") as image_file:
            image_data = image_file.read()
        
        payload = {
            "inputs": {
                "image": base64.b64encode(image_data).decode('utf-8')
            }
        }
        
        response = query_huggingface_api(payload, "Salesforce/blip-image-captioning-large", hf_headers)
        
        if isinstance(response, list) and len(response) > 0 and 'generated_text' in response[0]:
            caption = response[0]['generated_text']
            folder_name = simplify_caption(caption)
            category_folder = os.path.join(base_folder, 'images', folder_name)
            os.makedirs(category_folder, exist_ok=True)
            new_file_path = os.path.join(category_folder, os.path.basename(file_path))
            os.rename(file_path, new_file_path)
            print(f"Moved {os.path.basename(file_path)} to images/{folder_name} folder")
        else:
            print(f"Error: Unable to generate caption for {os.path.basename(file_path)}. Response: {response}")
    except Exception as e:
        print(f"Error processing {os.path.basename(file_path)}: {str(e)}")

#processes a pdf file.
def process_pdf(file_path: str, base_folder: str, groq_client: Groq):
    try:
        topic = get_pdf_topic(file_path, groq_client)
        category_folder = os.path.join(base_folder, 'pdfs', topic)
        os.makedirs(category_folder, exist_ok=True)
        new_file_path = os.path.join(category_folder, os.path.basename(file_path))
        os.rename(file_path, new_file_path)
        print(f"Moved {os.path.basename(file_path)} to pdfs/{topic} folder")
    except Exception as e:
        print(f"Error processing PDF {os.path.basename(file_path)}: {str(e)}")

#processes an excel file
def process_excel(file_path: str, base_folder: str, groq_client: Groq):
    try:
        topic = get_excel_topic(file_path, groq_client)
        category_folder = os.path.join(base_folder, 'excels', topic)
        os.makedirs(category_folder, exist_ok=True)
        new_file_path = os.path.join(category_folder, os.path.basename(file_path))
        os.rename(file_path, new_file_path)
        print(f"Moved {os.path.basename(file_path)} to excels/{topic} folder")
    except Exception as e:
        print(f"Error processing Excel {os.path.basename(file_path)}: {str(e)}")

#moves any other file type to the other_files folder (like json, mp4, etc.)
def move_to_other_files(file_path: str, base_folder: str):
    other_files_folder = os.path.join(base_folder, 'other_files')
    new_file_path = os.path.join(other_files_folder, os.path.basename(file_path))
    os.rename(file_path, new_file_path)
    print(f"Moved {os.path.basename(file_path)} to other_files folder")

#extracts the code from the response generated by the mistral model
def extract_code_from_response(response: str) -> str:
    code_blocks = re.findall(r'```(?:python)?\n(.*?)```', response, re.DOTALL)
    if code_blocks:
        return code_blocks[0].strip()
    return response.strip()

#code function that takes a file path and a groq client and generates code based on the user's request
#I'm using the mistral model for this, but you can use any other model of your choice.
#For me, mistral is the best model for this task because it can generate code that is both concise and readable manner and it's also very fast.
def code(file_path: str, groq_client: Groq):
    if not os.path.exists(file_path):
        user_input = input(f"File {file_path} does not exist. Do you want to create it? (y/n): ")
        if user_input.lower() != 'y':
            print("Operation cancelled.")
            return
        open(file_path, 'w').close()

    with open(file_path, 'r') as file:
        content = file.read()

    user_input = input("What would you like to do with the code? (suggest/generate): ")

    context = get_context('code', file_path)
    context_prompt = ""
    if context:
        context_prompt = "Based on previous conversations:\n" + "\n".join([
            f"- {item['query']}: {item['response']}"
            for item in context
        ])

    if user_input.lower() == 'suggest':
        user_request = input("What changes would you like to suggest? ")
        prompt = f"{context_prompt}\n\nGiven the following code:\n\n{content}\n\nSuggest changes to fix this code based on this request: {user_request}"
    elif user_input.lower() == 'generate':
        user_request = input("What code would you like to generate? ")
        prompt = f"{context_prompt}\n\nGenerate code for the following request: {user_request}"
    else:
        print("Invalid option. Please choose 'suggest' or 'generate'.")
        return

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that suggests code changes or generates new code. Consider the context from previous conversations when applicable."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="mixtral-8x7b-32768",
            max_tokens=4000
        )

        response = chat_completion.choices[0].message.content.strip()
        add_to_history('code', user_request, response)

        if user_input.lower() == 'suggest':
            suggestions = response.split('\n')
            lines = content.split('\n')
            new_content = []
            changes_made = set()

            for suggestion in suggestions:
                match = re.match(r'Line (\d+):', suggestion)
                if match:
                    line_num = int(match.group(1))
                    if 1 <= line_num <= len(lines):
                        new_content.append(f"# Suggestion: {suggestion}")
                        new_content.append(lines[line_num - 1])
                        changes_made.add(line_num)
                    else:
                        new_content.append(f"# {suggestion}")
                else:
                    new_content.append(f"# {suggestion}")

            for i, line in enumerate(lines, 1):
                if i not in changes_made:
                    new_content.append(line)

            with open(file_path, 'w') as file:
                file.write('\n'.join(new_content))

            if changes_made:
                print(f"Changes suggested in lines: {', '.join(map(str, sorted(changes_made)))}")
            else:
                print("Please check the file for general suggestions.")

        elif user_input.lower() == 'generate':
            generated_code = extract_code_from_response(response)
            with open(file_path, 'w') as file:
                file.write(generated_code)
            print(f"Generated code has been written to {file_path}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

#main function that handles the command line arguments and calls the appropriate function based on the command type
def main():
    #checking if the first run flag exists, if not, it means this is the first time the program is run
    #if it's the first time, it will set up the batch files and the system path
    #you can remove this if statement if you want to run the program instead of the exe
    first_run_flag = os.path.join(os.path.expanduser("~"), ".fastfox", ".first_run")
    if not os.path.exists(first_run_flag):
        setup_batch_files()
        os.makedirs(os.path.dirname(first_run_flag), exist_ok=True)
        with open(first_run_flag, 'w') as f:
            f.write('installed')

    groq_client, hf_headers = initialize()
    
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY = load_conversation_history()
    
    if len(sys.argv) < 2:
        print("Usage: command <query> or organize <path> or codeit <file> or forget <all|command|codeit|organize>")
        return

    command_type = sys.argv[1].lower()
    query = sys.argv[2] if len(sys.argv) > 2 else ""

    try:
        if command_type in ["command", "organize", "codeit", "forget"]:
            if command_type == "command":
                suggest_command(query, groq_client)
            elif command_type == "organize":
                organize_folder(query, groq_client, hf_headers)
            elif command_type == "codeit":
                code(query, groq_client)
            elif command_type == "forget":
                forget(query)
        else:
            print("Invalid command type. Use command, organize, code, or forget.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    print("Starting FastFox...")
    main()
