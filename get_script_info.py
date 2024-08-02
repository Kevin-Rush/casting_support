import shutil
import fitz  # PyMuPDF
import re
import json

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
    doc = fitz.open(pdf_path)
    for page_num in range(doc.page_count):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for image_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            image.save(f'{img_dir}/page_{page_num}_img_{image_index}.png')

def delete_image_dir(img_dir):
    shutil.rmtree(img_dir)



# Usage
script_name = 'OGIAT Second Draft v4'
pdf_path = f'scripts/{script_name}.pdf'  
txt_path = f'scripts/{script_name}.txt'  
img_path = f'scripts/{script_name}_images'

# pdf_to_text(pdf_path, txt_path)

pdf_to_images(pdf_path, img_path)
