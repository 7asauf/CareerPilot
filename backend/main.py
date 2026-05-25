import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
import io


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI()


@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    global cv_text
    content = await file.read()
    
    if file.filename.endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            cv_text = ""
            for page in pdf_reader.pages:
                cv_text += page.extract_text()
        except Exception as e:
            return {"error": str(e)}
    else:
        cv_text = content.decode("utf-8", errors="ignore")
    
    return {"message": "CV uploaded successfully", "length": len(cv_text)}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cv_text = ""

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    global cv_text
    content = await file.read()
    cv_text = content.decode("utf-8", errors="ignore")
    return {"message": "CV uploaded successfully", "length": len(cv_text)}


class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: ChatMessage):
    if not cv_text:
        return {"response": "Please upload your CV first."}
    
    prompt = f"""You are CareerPilot, an AI career assistant. 
You have access to the user's CV below. Answer their questions based on their actual experience.

CV:
{cv_text}

User question: {msg.message}

Give a helpful, specific answer based on their CV."""

    response = model.generate_content(prompt)
    return {"response": response.text}


class JobDescription(BaseModel):
    job_description: str

@app.post("/fit-score")
async def fit_score(job: JobDescription):
    if not cv_text:
        return {"error": "Please upload your CV first."}
    
    prompt = f"""You are CareerPilot, an AI career assistant.
Compare this user's CV against the job description and give a fit score.

CV:
{cv_text}

Job Description:
{job.job_description}

Respond in this exact format:
SCORE: [number between 0-100]
SUMMARY: [2-3 sentences explaining the match]
STRENGTHS: [bullet points of matching skills]
GAPS: [bullet points of missing skills]"""

    response = model.generate_content(prompt)
    return {"result": response.text}