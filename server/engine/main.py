from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
import os

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = whisper.load_model("base")

@app.get("/")
async def root():
    return {"message": "API is up and running!"}

@app.post("/speech-to-text") # post due to creation 
# async allows await, fastAPI uploadfile for large uploads 
# file in req.body
async def speech_to_text(file: UploadFile = File(...)): 
    with tempfile.NamedTemporaryFile(delete=False) as tmp: # temp file w name in local disk, delete=False NO AUTO DEL!
        tmp.write(await file.read()) # write the fully read file
        tmp_path = tmp.name # file path / name to pass to whisper

    result = model.transcribe(tmp_path) # transcribe is whisper method
    os.remove(tmp_path) # done w file, delete it
    return {"text": result["text"]} # dict to json
