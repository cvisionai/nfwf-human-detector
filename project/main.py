from celery.result import AsyncResult
from fastapi import Body, FastAPI, Form, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os
#import uuid

from worker import create_task, slice_video, run_yolo

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class VideoRequest(BaseModel):
    url: str
    start_frame: int
    end_frame: int

class DetectRequest(BaseModel):
    url: str
    confidence: float

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", context={"request": request})

@app.get("/video_files")
async def list_video_files(request: Request):
    files = os.listdir('/inputs')
    return JSONResponse(files)

@app.get("/result_files")
async def list_video_files(request: Request, subdir: Optional[str] = None):
    directory = '/outputs/results'
    if subdir:
        directory = os.path.join(directory, subdir)
    files = os.listdir(directory)
    return JSONResponse(files)

@app.get("/result_contents")
async def get_result_contents(request: Request, subdir: Optional[str] = None):
    directory = '/outputs'
    if subdir:
        directory = os.path.join(directory, subdir)
    filenames = os.listdir(directory)
    files = []
    for filename in filenames:
        with open(os.path.join(directory, filename), 'r') as f:
            contents = f.read()
            files.append({'name': filename, 'content': contents})
    return JSONResponse(files)

@app.post('/slice_video')
async def post_slice_video(video_request: VideoRequest):
    #job_id = str(uuid.uuid4())

    # Add the job to Redis
    job_data = {'url': video_request.url,
                'start_frame': video_request.start_frame,
                'end_frame': video_request.end_frame,
                'output_filename': video_request.url.split(".mp4")[0] + "_sliced.mp4"}
    #redis.set(job_id, json.dumps({'status': 'PENDING', 'data': job_data}))

    # Queue the video slicing task with Celery
    task = slice_video.delay(video_request.url,
                                         video_request.start_frame,
                                         video_request.end_frame,
                                         job_data['output_filename'])

    # Return the job ID so the client can check the status later
    return JSONResponse({'task_id': task.id})

@app.post('/run_yolo')
async def post_run_yolo(video_request: DetectRequest):
    job_data = {'url': video_request.url,
                'confidence': 0.25}
    task = run_yolo.delay(job_data['url'], job_data['confidence'])

    return JSONResponse({'task_id': task.id})

@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    task_type = payload["type"]
    task = create_task.delay(int(task_type))
    return JSONResponse({"task_id": task.id})


@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)
