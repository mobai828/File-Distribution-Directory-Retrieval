from docx import Document
import sys

try:
    doc = Document("著录流程.docx")
    for para in doc.paragraphs:
        if para.text.strip():
            print(para.text)
except Exception as e:
    print(f"Error: {e}")
