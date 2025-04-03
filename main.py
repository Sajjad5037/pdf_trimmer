from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import shutil
import os
import uuid

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sajjadalinoor.vercel.app"],  # Updated frontend URL
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create directory if not exists

@app.post("/extractPdfPages")
async def extract_pdf_pages(file: UploadFile = File(...), pages: str = Form(...)):
    try:
        # Save uploaded file
        file_path = f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Open the PDF
        doc = fitz.open(file_path)
        selected_pages = [int(p) - 1 for p in pages.split(",") if p.strip().isdigit()]
        
        if not selected_pages or min(selected_pages) < 0 or max(selected_pages) >= len(doc):
            return JSONResponse(status_code=400, content={"error": "Invalid page numbers."})

        # Create new PDF with selected pages
        new_pdf = fitz.open()
        for page_num in selected_pages:
            new_pdf.insert_pdf(doc, from_page=page_num, to_page=page_num)

        # Save extracted PDF
        new_pdf_path = f"{UPLOAD_DIR}/extracted_{uuid.uuid4()}.pdf"
        new_pdf.save(new_pdf_path)
        new_pdf.close()

        # Generate a public URL (Change this to match your server's domain)
        download_url = f"https://pdf-trimmer-b296287835d4.herokuapp.com/{new_pdf_path}"
         
        return {"pdfUrl": download_url}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    print("Starting FastAPI app...")
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
