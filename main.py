from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
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
        print(f"File saved successfully at {file_path}")
        
        # Open the PDF
        doc = fitz.open(file_path)
        print(f"PDF opened successfully: {file_path}")

        # Parse the pages input
        print(f"Raw pages input: {pages}")
        raw_pages = pages.split(",")
        page_ranges = []
        selected_pages = []
        
        # Process page ranges and individual pages
        for page in raw_pages:
            if "-" in page:  # Handle page ranges like '1-3'
                start, end = page.split("-")
                try:
                    page_ranges.append(range(int(start) - 1, int(end)))  # 0-based index
                except ValueError:
                    continue
            else:  # Handle individual pages
                try:
                    selected_pages.append(int(page) - 1)  # 0-based index
                except ValueError:
                    continue

        # Combine selected pages from ranges and individual pages
        for page_range in page_ranges:
            selected_pages.extend(page_range)

        # Ensure no out-of-bound pages are requested
        if not selected_pages or min(selected_pages) < 0 or max(selected_pages) >= len(doc):
            print("Invalid page numbers detected.")
            return JSONResponse(status_code=400, content={"error": "Invalid page numbers."})

        # Create a new PDF with the selected pages
        new_pdf = fitz.open()
        for page_num in selected_pages:
            new_pdf.insert_pdf(doc, from_page=page_num, to_page=page_num)
            print(f"Inserting page {page_num + 1}")

        # Save the extracted PDF to a new file
        new_pdf_path = f"{UPLOAD_DIR}/extracted_{uuid.uuid4()}.pdf"
        new_pdf.save(new_pdf_path)
        new_pdf.close()
        print(f"Extracted PDF saved at {new_pdf_path}")

        # Send the file as a response for the front-end to download
        return FileResponse(new_pdf_path, filename=os.path.basename(new_pdf_path), media_type='application/pdf')
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
