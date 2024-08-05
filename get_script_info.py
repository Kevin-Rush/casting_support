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
gpt_api_key = os.getenv("OPENAI_API_KEY")

def pdf_to_text(pdf_path, txt_path):
    doc = fitz.open(pdf_path)
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = clean_text(text)
            txt_file.write(cleaned_text)
            txt_file.write('\n\n')  # Ensure there's a line break between pages

def clean_text(text):
    # This function ensures there are spaces after each word
    text = re.sub(r'(\w)([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'(\w)([\.\,\;\:\!\?\)\(\[\]])', r'\1 \2', text)
    text = re.sub(r'([\.\,\;\:\!\?\)\(\[\]])(\w)', r'\1 \2', text)
    return text

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

def delete_image(img_path):
    # Delete the image at the given path
    if os.path.exists(img_path):
        os.remove(img_path)
        print(f"Image file {img_path} deleted successfully.")
    else:
        print(f"Image file {img_path} does not exist.")


# Function to encode the image
def encode_image(image_path):
    #This function encodes the image to base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_script_json_via_gpt(image_path):
    # This function takes an image and returns the alt text for the image
    prompt = """You are an expert script JSON converter. Your job is to take in an image of a single page of a script and convert the text on the page into JSON format. Note, you NEVER add text that was not originally in the script. All text must be traceable to the original script! If information is unknown because it is missing the value is left blank (Example: A page is only dialogue and does not list the act number or title.)
     
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
            "dialogue": "Duis tristique nibh vel tellus fermentum dictum."
            "direction": "CHARACTER 2 reacts to CHARACTER 1"
            }
            ]
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
            },
        ]
        }
    ]
    }
    """

    base64_image = encode_image(image_path)
    print(f"{Fore.YELLOW}\n-----------------Calling OpenAI-----------------{Fore.RESET}")

    response = call_gpt_vision(base64_image, prompt)
    print(f"{Fore.GREEN}\n-----------------Image Processed-----------------{Fore.RESET}")

    # return response['choices'][0]['message']['content']
    return response


def call_gpt_vision(base64_image, prompt, gpt_model_version):
    # This function takes a folder of images and an API key and returns a list of responses from the GPT-4 Vision model
    openai.api_key = gpt_api_key
    model = gpt_model_version

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {gpt_api_key}"
    }

    payload = {
    "model": model,
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": prompt
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
    "max_tokens": 1251
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response = response.json()

    return response

# Usage
script_name = 'OGIAT Second Draft v4'
pdf_path = f'scripts/{script_name}.pdf'  
txt_path = f'scripts/{script_name}.txt'  
img_path = f'scripts/{script_name}_images'



# Testing

exit()

fp =  open(pdf_path, 'rb')
scriptJSON = convert(fp, 0)

# save the json to a file
json_file = f'scripts/{script_name}.json'
with open(json_file, 'w') as f:
    json.dump(scriptJSON, f)

# pdf_to_text(pdf_path, txt_path)

pdf_to_images(pdf_path, img_path)

delete_image_dir(img_path)