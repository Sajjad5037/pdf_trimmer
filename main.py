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
os.makedirs(UPLOAD_DIR, exist_ok=True)
            
@app.post("/extractPdfPages")
async def extract_pdf_pages(file: UploadFile = File(...), pages: str = Form(...)):
    try:
        print("Received file:", file.filename)  # Debug print to check file name
        print("Received pages:", pages)  # Debug print to check pages parameter

        # Save uploaded file
        file_path = f"{UPLOAD_DIR}/{uuid.uuid4()}_{file.filename}"
        print(f"Saving file to {file_path}")  # Debug print to show where file is saved

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File saved successfully at {file_path}")  # Debug print to confirm file save

        # Open the PDF
        try:
            doc = fitz.open(file_path)
            print(f"PDF opened successfully: {file_path}")
        except Exception as e:
            print(f"Failed to open PDF: {e}")
            return JSONResponse(status_code=500, content={"error": "Failed to open PDF."})

        # Debugging: Print raw pages input
        print(f"Raw pages input: {pages}")

        # Strip any unwanted characters from `pages` and split by commas
        pages = pages.strip()
        page_list = pages.split(",")
        print(f"Split pages list: {page_list}")  # Debug print after splitting by commas

        # Parse the page numbers correctly
        selected_pages = [int(p.strip()) - 1 for p in page_list if p.strip().isdigit()]
        print(f"Parsed page numbers: {selected_pages}")  # Debug print to check parsed pages

        if not selected_pages or min(selected_pages) < 0 or max(selected_pages) >= len(doc):
            print("Invalid page numbers detected.")  # Debug print when page numbers are invalid
            return JSONResponse(status_code=400, content={"error": "Invalid page numbers."})

        # Create new PDF with selected pages
        new_pdf = fitz.open()
        for page_num in selected_pages:
            print(f"Inserting page {page_num + 1}")  # Debug print for each page inserted
            new_pdf.insert_pdf(doc, from_page=page_num, to_page=page_num)

        # Save extracted PDF
        new_pdf_path = f"{UPLOAD_DIR}/extracted_{uuid.uuid4()}.pdf"
        new_pdf.save(new_pdf_path)
        print(f"Extracted PDF saved at {new_pdf_path}")  # Debug print to show where new PDF is saved
        new_pdf.close()

        # Send the file as a response to download
        return FileResponse(new_pdf_path, media_type='application/pdf', filename=os.path.basename(new_pdf_path))

    except Exception as e:
        print(f"An error occurred: {e}")  # Debug print to capture any other errors
        return JSONResponse(status_code=500, content={"error": str(e)})
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
