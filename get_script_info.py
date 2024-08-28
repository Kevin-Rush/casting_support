import io
import os
import shutil
from tkinter import Image
import fitz  # PyMuPDF
import re
import json
from screenplay_pdf_to_json import convert
import base64
from colorama import Fore
import requests
import openai
from dotenv import load_dotenv

load_dotenv()
gpt_api_key = os.getenv("CASTING_OPENAI_API_KEY")
gpt_model = os.getenv("GPT_MODEL")

# Conver a pdf to a text file
def pdf_to_text(pdf_path, txt_path):
    doc = fitz.open(pdf_path)
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = clean_text(text)
            txt_file.write(cleaned_text)
            txt_file.write('\n\n')  # Ensure there's a line break between pages

# Ensure there are spaces after each word in a body of text
def clean_text(text):
    text = re.sub(r'(\w)([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\w)([\.\,\;\:\!\?\)\(\[\]])', r'\1 \2', text)
    text = re.sub(r'([\.\,\;\:\!\?\)\(\[\]])(\w)', r'\1 \2', text)
    return text

# Convert a pdf into images saved in a specified directory
def pdf_to_images(pdf_path, img_dir):
    # Ensure the directory exists
    os.makedirs(img_dir, exist_ok=True)

    #read the pdf file and convert each page to an image and save in img_dir

    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc[page_num]
        image = page.get_pixmap()
        image_path = os.path.join(img_dir, f'page_{page_num}.png')
        image.save(image_path) 

# Delete an entire directory
def delete_image_dir(img_dir):
    try:
        if os.path.exists(img_dir):
            shutil.rmtree(img_dir)
            print(f"Directory {img_dir} deleted successfully.")
        else:
            print(f"Directory {img_dir} does not exist.")
    except PermissionError:
        print(f"Permission denied: Unable to delete {img_dir}.")
    except FileNotFoundError:
        print(f"File not found: {img_dir}.")
    except Exception as e:
        print(f"An error occurred while deleting {img_dir}: {e}")

# Delete a file at a given path
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"File {file_path} deleted successfully.")
    else:
        print(f"File {file_path} does not exist.")

# Function to encode an image
def encode_image(image_path):
    #This function encodes the image to base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# This function takes an image and returns the text for the image
def get_script_json_via_gpt(image_path):
    sys_prompt = """You are an expert script JSON converter. Your job is to take in an image of a single page of a script and convert the text on the page into JSON format. Note, you NEVER add text that was not originally in the script. All text must be traceable to the original script! If information is unknown because it is missing the value is left blank (Example: A page is only dialogue and does not list the act number or title.)
     
    The JSON file should contain the following keys: title, author, act[act_number, act_title], page_num, scenes [scene_number, location, extra_info, dialogues[character, dialogue, direction], intercut].

    For example:
    
    {
        "title": "Movie 1",
        "author": "John Doe",
        "act": {
            "name": "ACT ONE",
            "title": "Title 1"
        },
        "page_num": "1",
        "scenes": [
            {
            "scene_number": 1,
            "location": "EXT. LOCATION NAME - Lorem ipsum - FLASHBACK",
            "extra_information": "a description of the scene"
            },
            {
            "scene_number": 2,
            "location": "EXT. LOCATION NAME - Lorem ipsum - PRESENT DAY",
            "extra_information": "information about the scene and the background",
            "dialogues": [
                {
                "character": "CHARACTER 1",
                "dialogue": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "direction": ""
                },
                {
                "character": "CHARACTER 2",
                "dialogue": "Duis tristique nibh vel tellus fermentum dictum.",
                "direction": "CHARACTER 2 reacts to CHARACTER 1"
                }
                ]
            },
            {
            "intercut": "Information about what is happening at this point of the scene",
            "dialogue": [
                {
                "character": "CHARACTER 1",
                "dialogue": "Nullam vitae malesuada orci.",
                "direction": "CHARACTER 3 does something as they enter the scene"
                },
                {
                "character": "CHARACTER 3",
                "dialogue": "Pellentesque habitant morbi tristique senectus et",
                "direction": ""
                }
            ]
            }
        ]
    }
    """
    print(f"{Fore.YELLOW}\n-----------------Encoding Image-----------------{Fore.RESET}")
    base64_image = encode_image(image_path)

    print(f"{Fore.YELLOW}\n-----------------Calling OpenAI-----------------{Fore.RESET}")
    response = call_gpt_vision(base64_image, sys_prompt, user_prompt)

    print(f"{Fore.GREEN}\n-----------------Image Processed-----------------{Fore.RESET}")

    # return response['choices'][0]['message']['content']
    return response

# Make a call to gpt_vision
def call_gpt_vision(base64_image, sys_prompt, user_prompt, gpt_model=gpt_model):
    openai.api_key = gpt_api_key
    model = gpt_model

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {gpt_api_key}"
    }

    payload = {
    "model": model,
    "messages": [
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": sys_prompt
            },
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": user_prompt
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    # "max_tokens": 1251
    "temperature": 0
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response = response.json()

    return response

# Iterate over a directory
def iterate_dir(dir_path, file_type=".png"):
    for file in os.listdir(dir_path):
        if file.endswith(file_type):
            dir_path = os.path.join(img_path, file)
            script_json = get_script_json_via_gpt(dir_path)

            delete_file(dir_path)

# Usage
script_name = 'OGIAT Second Draft v4'
pdf_path = f'scripts/{script_name}.pdf'  
txt_path = f'scripts/{script_name}.txt'  
img_path = f'scripts/{script_name}_images'

# Testing

pdf_to_images(pdf_path, img_path)

