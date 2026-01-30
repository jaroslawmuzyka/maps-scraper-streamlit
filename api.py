from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import os
import json
import time

app = FastAPI()

# Configuration
jobs_file = "jobs.json"
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

# Ensure jobs file exists
if not os.path.exists(jobs_file):
    with open(jobs_file, "w") as f:
        json.dump([], f)

class JobRequest(BaseModel):
    worker_id: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Scraper API is running"}

@app.get("/get-job")
def get_job(worker_id: str = "unknown"):
    """
    Returns the next pending job.
    """
    try:
        with open(jobs_file, "r+") as f:
            try:
                jobs = json.load(f)
            except json.JSONDecodeError:
                jobs = []
            
            # Find first pending job
            for job in jobs:
                if job["status"] == "pending":
                    job["status"] = "processing"
                    job["worker"] = worker_id
                    job["start_time"] = time.time()
                    
                    # Save back
                    f.seek(0)
                    json.dump(jobs, f, indent=4)
                    f.truncate()
                    
                    return {"job_id": job["id"], "phrase": job["phrase"]}
                    
        return {"status": "wait"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/upload-results")
async def upload_results(file: UploadFile = File(...), job_id: str = None):
    """
    Receives the JSON result file from the scraper.
    """
    try:
        if not file.filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Only JSON files allowed")

        file_location = os.path.join(results_dir, file.filename)
        
        with open(file_location, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Mark job as done
        if job_id:
            with open(jobs_file, "r+") as f:
                jobs = json.load(f)
                for job in jobs:
                    if str(job["id"]) == job_id:
                        job["status"] = "done"
                        job["end_time"] = time.time()
                        job["result_file"] = file.filename
                        break
                f.seek(0)
                json.dump(jobs, f, indent=4)
                f.truncate()

        return {"status": "success", "filename": file.filename}

    except Exception as e:
        return {"status": "error", "message": str(e)}
