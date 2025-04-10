from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import pymongo
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import PyPDF2
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure MongoDB
mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client["document_summarizer"]
summaries_collection = db["summaries"]

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

ALLOWED_EXTENSIONS = {'pdf'}

# Model configuration
MODEL_NAME = "google/flan-t5-small"
MODEL_DIR = os.getenv("MODEL_DIR", "./model")
MAX_SOURCE_LENGTH = 512
MAX_TARGET_LENGTH = 128
CHUNK_OVERLAP = 50

# Load model and tokenizer
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
base_model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# Load the fine-tuned model
try:
    model = PeftModel.from_pretrained(base_model, os.path.join(MODEL_DIR, "final_model"))
    print("Fine-tuned model loaded successfully")
except Exception as e:
    print(f"Error loading fine-tuned model: {e}")
    print("Using base model instead")
    model = base_model

# Move model to appropriate device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if not torch.cuda.is_available():
    model = model.to(device)
print(f"Using device: {device}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

def chunk_document(text, max_length=MAX_SOURCE_LENGTH, overlap=CHUNK_OVERLAP):
    """Split a document into overlapping chunks that fit within the model's context window"""
    # Make sure text is a string
    text = str(text)

    tokens = tokenizer.encode(text, add_special_tokens=False)

    # If the document fits within the context window, return it as is
    if len(tokens) <= max_length:
        return [text]

    # Split into chunks
    chunks = []
    chunk_size = max_length - overlap  # Effective chunk size considering overlap

    for i in range(0, len(tokens), chunk_size):
        # Get chunk tokens
        chunk_tokens = tokens[i:i + max_length]
        # Decode back to text
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

    return chunks

def combine_chunk_summaries(summaries):
    """Combine summaries from multiple chunks into a coherent summary"""
    # Simple concatenation approach - could be improved with more sophisticated methods
    combined = " ".join(summaries)
    # Remove redundant sentences
    # (This is a simple implementation; a more sophisticated approach might use embeddings)
    return combined

def summarize_text(text):
    try:
        # Check if input needs chunking
        chunks = chunk_document(text)
        
        summaries = []
        for chunk in chunks:
            chunk_input = f"summarize: {chunk}"
            inputs = tokenizer(chunk_input, return_tensors="pt").to(device)
            
            with torch.no_grad():
                outputs = model.generate(
                    input_ids=inputs["input_ids"],
                    max_length=MAX_TARGET_LENGTH,
                    num_beams=4,
                )
            
            summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
            summaries.append(summary)
        
        # If we had to chunk the input, combine the summaries
        if len(summaries) > 1:
            return combine_chunk_summaries(summaries)
        else:
            return summaries[0]
    except Exception as e:
        print(f"Error in summarization: {e}")
        return "Error generating summary. Please try again."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        
        # Generate summary using custom model
        summary = summarize_text(text)
        
        # Store in MongoDB
        document = {
            "original_filename": filename,
            "stored_filename": unique_filename,
            "upload_date": datetime.now(),
            "text_length": len(text),
            "summary": summary
        }
        
        result = summaries_collection.insert_one(document)
        
        # Return the summary and document ID
        return jsonify({
            "success": True,
            "document_id": str(result.inserted_id),
            "summary": summary,
            "filename": filename
        })
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/summaries', methods=['GET'])
def get_summaries():
    summaries = list(summaries_collection.find({}, {
        "_id": 1, 
        "original_filename": 1, 
        "upload_date": 1, 
        "summary": 1
    }))
    
    # Convert ObjectId to string for JSON serialization
    for summary in summaries:
        summary["_id"] = str(summary["_id"])
        summary["upload_date"] = summary["upload_date"].isoformat()
    
    return jsonify(summaries)

@app.route('/summary/<document_id>', methods=['GET'])
def get_summary(document_id):
    from bson.objectid import ObjectId
    
    summary = summaries_collection.find_one({"_id": ObjectId(document_id)})
    
    if not summary:
        return jsonify({"error": "Summary not found"}), 404
    
    # Convert ObjectId to string for JSON serialization
    summary["_id"] = str(summary["_id"])
    summary["upload_date"] = summary["upload_date"].isoformat()
    
    return jsonify(summary)

@app.route('/model-info', methods=['GET'])
def model_info():
    """Return information about the loaded model"""
    return jsonify({
        "model_name": MODEL_NAME,
        "fine_tuned": isinstance(model, PeftModel),
        "device": str(device),
        "max_source_length": MAX_SOURCE_LENGTH,
        "max_target_length": MAX_TARGET_LENGTH
    })

if __name__ == '__main__':
    app.run(debug=True)
