# Legal Document Summarizer using finetuned FLAN-T5 Small

This project provides an end-to-end solution for summarizing lengthy legal documents using a fine-tuned FLAN-T5 Small model. The system is designed to help users extract concise summaries from complex legal texts, particularly cases from India and the UK.

---

## Tech Stack

- 🧠 Machine Learning: `google/flan-t5-small` fine-tuned on large dataset of Indian & UK court cases
- 🖥️ Backend: Python (FastAPI / Flask) with MongoDB for storing input files & generated summaries
- 🌐 Frontend: React / HTML-CSS-JS based user-friendly interface
- ☁️ Database: MongoDB for storing uploaded legal documents and corresponding summaries
- 🧰 Other Tools: Hugging Face PEFT library for efficient fine-tuning

---

## Features

- Upload legal documents (txt, pdf)
- Auto-generation of human-readable summaries
- Stores both original documents & summaries securely in MongoDB
- Clean, intuitive frontend for easy interaction
- API endpoints to interact with the model programmatically
- Fine-tuned on real-world datasets from Indian & UK court cases for domain-specific understanding

---
##Model Details

Base Model: google/flan-t5-small

Fine-tuned using: PEFT (Parameter Efficient Fine Tuning)

Domain: Legal Document Summarization

Trained On: Large dataset of Indian & UK legal case summaries

##Future Improvements

Support for more document formats (DOCX, HTML)

Better UI for summary visualization

Deploying model to HuggingFace Spaces / AWS / GCP

User Authentication for secure access

Feedback loop to improve summaries


