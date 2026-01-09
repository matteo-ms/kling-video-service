from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import requests
import time
import os
from pathlib import Path
import logging
from typing import Optional
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kling Video Generation Service",
    description="Generate long-form videos using Kling AI with automatic extension",
    version="1.0.0"
)

# Kling API configuration
KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY")
JWT_SERVICE_URL = os.getenv("JWT_SERVICE_URL", "https://kling-jwt-service-production.up.railway.app/generate-jwt")
KLING_API_BASE = "https://api-singapore.klingai.com/v1"

if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
    logger.error("KLING_ACCESS_KEY and KLING_SECRET_KEY environment variables must be set!")
    raise ValueError("KLING_ACCESS_KEY and KLING_SECRET_KEY are required")

# Video storage
VIDEOS_DIR = Path(os.getenv("VIDEOS_DIR", "/tmp/videos"))
VIDEOS_DIR.mkdir(exist_ok=True, parents=True)

class CameraControl(BaseModel):
    type: Optional[str] = Field(None, description="Camera movement type")
    horizontal: Optional[int] = Field(None, description="Horizontal movement (-10 to 10)")
    vertical: Optional[int] = Field(None, description="Vertical movement (-10 to 10)")
    pan: Optional[int] = Field(None, description="Pan movement (-10 to 10)")
    tilt: Optional[int] = Field(None, description="Tilt movement (-10 to 10)")
    roll: Optional[int] = Field(None, description="Roll movement (-10 to 10)")
    zoom: Optional[int] = Field(None, description="Zoom movement (-10 to 10)")

class VideoGenerationRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Single video generation prompt", min_length=10, max_length=2500)
    prompts: Optional[list[str]] = Field(None, description="Array of prompts for multi-segment videos. If provided, overrides 'prompt'.")
    negative_prompt: Optional[str] = Field(
        default="blurry, distorted, low quality, watermark, text, ugly, deformed",
        description="What to avoid in the video"
    )
    camera_control: Optional[CameraControl] = Field(None, description="Camera movement controls")
    motion_control: Optional[MotionControl] = Field(None, description="Advanced motion control")
    motion_brush: Optional[dict] = Field(None, description="Motion brush data")
    object_motion: Optional[List[dict]] = Field(None, description="Per-object motion")
    model_name: str = Field(
        default="kling-v2-6",
        description="Model to use. Extension support: v1✅, v1-5✅, v1-6✅, v2-6 PRO only",
        pattern="^(kling-v1|kling-v1-5|kling-v1-6|kling-v2-master|kling-v2-1-master|kling-v2-5-turbo|kling-v2-6)$"
    )
    duration: str = Field(
        default="10",
        description="Video duration in seconds (5 or 10)",
        pattern="^(5|10)$"
    )
    aspect_ratio: str = Field(
        default="16:9",
        description="Video aspect ratio",
        pattern="^(16:9|9:16|1:1)$"
    )
    mode: str = Field(
        default="pro",
        description="Generation mode (std or pro)",
        pattern="^(std|pro)$"
    )
    sound: str = Field(
        default="on",
        description="Enable sound generation (on or off)",
        pattern="^(on|off)$"
    )
    voice_narration: Optional[str] = Field(
        default=None,
        description="Narration text to synthesize and mix"
    )
    voice_control: Optional[VoiceControl] = Field(default=None, description="Voice control parameters")
    target_duration: Optional[int] = Field(
        None,
        description="Target duration for extended videos (in seconds). If set, will auto-extend.",
        ge=5,
        le=100
    )

class VideoGenerationResponse(BaseModel):
    job_id: str
    video_url: str
    video_id: str
    task_id: str
    duration: int
    iterations: int
    file_size: str
    generation_time: float
    raw_response: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

@app.get("/")
async def root():
    return {
        "service": "Kling Video Generation Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "generate": "POST /generate-video",
            "extend": "POST /extend-video",
            "image2video": "POST /image2video",
            "lipsync": "POST /lipsync",
            "video2audio": "POST /video2audio",
            "multi_image2video": "POST /multi-image2video",
            "download": "GET /videos/{filename}",
            "list": "GET /videos",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Test JWT generation
        jwt_token = _generate_jwt()
        return {
            "status": "healthy",
            "jwt_service": "connected",
            "kling_api": "connected",
            "videos_dir": str(VIDEOS_DIR),
            "videos_count": len(list(VIDEOS_DIR.glob("*.mp4")))
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/generate-video", response_model=VideoGenerationResponse, responses={
    500: {"model": ErrorResponse}
})
async def generate_video(request: VideoGenerationRequest):
    """
    Generate a video with Kling AI, optionally extending it to target duration.
    
    - **prompt**: Detailed video description
    - **target_duration**: If set, will automatically extend video to reach this duration
    - **model_name**: kling-v1, kling-v1-5, or kling-v2-6
    - **duration**: Base duration (5 or 10 seconds)
    - **mode**: std (standard) or pro (professional quality)
    """
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"[{job_id}] Starting video generation")
    
    # Handle prompts array vs single prompt
    if request.prompts:
        prompts_list = request.prompts[:20]  # Max 20 segments
        initial_prompt = prompts_list[0]
        logger.info(f"[{job_id}] Using multi-prompt mode: {len(prompts_list)} prompts")
    elif request.prompt:
        prompts_list = [request.prompt]
        initial_prompt = request.prompt
    else:
        raise HTTPException(status_code=400, detail="Either 'prompt' or 'prompts' must be provided")
    
    logger.info(f"[{job_id}] Initial prompt: {initial_prompt[:100]}...")
    
    try:
        # Step 1: Generate JWT
        jwt_token = _generate_jwt()
        logger.info(f"[{job_id}] JWT generated successfully")
        
        # Step 2: Create initial video with first prompt
        task_id = _create_video(jwt_token, request, job_id, initial_prompt)
        logger.info(f"[{job_id}] Video creation started - Task ID: {task_id}")
        
        # Step 3: Poll for completion and get video_id
        video_url, video_id = _poll_video_status(jwt_token, task_id, job_id, iteration=0)
        logger.info(f"[{job_id}] Initial video ready - Video ID: {video_id}")
        
        # Step 4: Download initial video
        output_filename = f"kling_{job_id}_{int(time.time())}.mp4"
        output_path = VIDEOS_DIR / output_filename
        _download_video(video_url, output_path)
        
        current_duration = int(request.duration)
        iterations = 1
        
        # Step 5: Extend if target_duration is set OR if we have multiple prompts
        extensions_needed = 0
        if request.target_duration and request.target_duration > current_duration:
            extensions_needed = (request.target_duration - current_duration + int(request.duration) - 1) // int(request.duration)
        elif len(prompts_list) > 1:
            # Use remaining prompts for extensions
            extensions_needed = len(prompts_list) - 1
        
        if extensions_needed > 0:
            logger.info(f"[{job_id}] Extensions needed: {extensions_needed}")
            
            for i in range(extensions_needed):
                if request.target_duration and current_duration >= request.target_duration:
                    break
                    
                # Use next prompt in sequence, or reuse first if not enough prompts
                extension_prompt = prompts_list[i + 1] if (i + 1) < len(prompts_list) else prompts_list[0]
                logger.info(f"[{job_id}] Extension {i+1}/{extensions_needed} - Prompt: {extension_prompt[:80]}...")
                
                # Extend video
                task_id = _extend_video(jwt_token, video_id, extension_prompt, job_id)
                video_url, video_id = _poll_video_status(jwt_token, task_id, job_id, iteration=i+1)
                
                # Download extended video (overwrite)
                _download_video(video_url, output_path)
                
                current_duration += int(request.duration)
                iterations += 1
                
                logger.info(f"[{job_id}] Extension {i+1} complete - Duration: {current_duration}s")
        
        file_size = output_path.stat().st_size
        file_size_mb = f"{file_size / (1024 * 1024):.2f} MB"
        generation_time = time.time() - start_time
        
        logger.info(f"[{job_id}] ✅ Success! {output_filename} ({file_size_mb}) in {generation_time:.1f}s")
        
        return VideoGenerationResponse(
            job_id=job_id,
            video_url=f"/videos/{output_filename}",
            video_id=video_id,
            task_id=task_id,
            duration=current_duration,
            iterations=iterations,
            file_size=file_size_mb,
            generation_time=round(generation_time, 2),
            raw_response={"video_url": video_url}
        )
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

@app.post("/extend-video")
async def extend_video(video_id: str, prompt: str):
    """
    Extend an existing video by its video_id.
    
    - **video_id**: The ID of the video to extend (from previous generation)
    - **prompt**: Prompt for the extension
    """
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    
    logger.info(f"[{job_id}] Extending video: {video_id}")
    
    try:
        jwt_token = _generate_jwt()
        task_id = _extend_video(jwt_token, video_id, prompt, job_id)
        video_url, new_video_id = _poll_video_status(jwt_token, task_id, job_id, iteration=0)
        
        output_filename = f"kling_{job_id}_{int(time.time())}.mp4"
        output_path = VIDEOS_DIR / output_filename
        _download_video(video_url, output_path)
        
        file_size = output_path.stat().st_size
        file_size_mb = f"{file_size / (1024 * 1024):.2f} MB"
        generation_time = time.time() - start_time
        
        logger.info(f"[{job_id}] ✅ Extension complete! {output_filename}")
        
        return {
            "job_id": job_id,
            "video_url": f"/videos/{output_filename}",
            "task_id": task_id,
            "file_size": file_size_mb,
            "generation_time": round(generation_time, 2)
        }
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Video extension failed: {str(e)}")

def _post_kling(jwt_token: str, path: str, payload: dict, job_id: str) -> dict:
    url = f"{KLING_API_BASE}/{path}"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if response.status_code != 200:
        try:
            data = response.json()
            req_id = data.get("request_id") or data.get("data", {}).get("request_id")
            msg = data.get("message") or response.text
            raise KlingAPIError(status_code=response.status_code, message=msg, request_id=req_id)
        except ValueError:
            raise KlingAPIError(status_code=response.status_code, message=response.text)
    return response.json()




@app.post("/image2video")
async def image2video(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    negative_prompt: str = Form("blurry, distorted"),
    model_name: str = Form("kling-v1-6"),
    duration: str = Form("10"),
    aspect_ratio: str = Form("16:9"),
    mode: str = Form("pro"),
    start_frame: UploadFile | None = File(None),
    end_frame: UploadFile | None = File(None),
    motion_control: str | None = Form(None),
):
    """Image to Video generation."""
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    jwt_token = _generate_jwt()

    image_uri = _save_and_data_uri(image, job_id, "image", IMAGE_EXTS, MAX_IMAGE_SIZE)
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "model_name": model_name,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "mode": mode,
        "image": {"url": image_uri},
    }
    if start_frame:
        payload["start_frame"] = {"url": _save_and_data_uri(start_frame, job_id, "start", IMAGE_EXTS, MAX_IMAGE_SIZE)}
    if end_frame:
        payload["end_frame"] = {"url": _save_and_data_uri(end_frame, job_id, "end", IMAGE_EXTS, MAX_IMAGE_SIZE)}
    if motion_control:
        try:
            payload["motion_control"] = json.loads(motion_control)
        except Exception:
            pass

    resp = _post_kling(jwt_token, "videos/image2video", payload, job_id)
    task_id = resp.get("data", {}).get("task_id") or resp.get("data", {}).get("id")
    video_url, video_id = poll_task_status(jwt_token, KLING_API_BASE, task_id, "videos/image2video", logger)

    output_filename = f"kling_img_{job_id}_{int(time.time())}.mp4"
    output_path = VIDEOS_DIR / output_filename
    _download_video(video_url, output_path)

    file_size = output_path.stat().st_size
    return JobResponse(
        job_id=job_id,
        task_id=task_id,
        status="succeed",
        result_url=f"/videos/{output_filename}",
        file_size=f"{file_size / (1024*1024):.2f} MB",
        generation_time=round(time.time() - start_time, 2),
        raw_response={"video_id": video_id}
    )


@app.post("/lipsync")
async def lipsync(
    video: UploadFile = File(...),
    audio: UploadFile = File(...),
    mode: str = Form("pro"),
):
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    jwt_token = _generate_jwt()

    video_uri = _save_and_data_uri(video, job_id, "video", VIDEO_EXTS, MAX_VIDEO_SIZE)
    audio_uri = _save_and_data_uri(audio, job_id, "audio", AUDIO_EXTS, MAX_AUDIO_SIZE)

    payload = {
        "video": {"url": video_uri},
        "audio": {"url": audio_uri},
        "mode": mode,
    }
    resp = _post_kling(jwt_token, "videos/lip-sync", payload, job_id)
    task_id = resp.get("data", {}).get("task_id") or resp.get("data", {}).get("id")
    video_url, video_id = poll_task_status(jwt_token, KLING_API_BASE, task_id, "videos/lip-sync", logger)

    output_filename = f"kling_lipsync_{job_id}_{int(time.time())}.mp4"
    output_path = VIDEOS_DIR / output_filename
    _download_video(video_url, output_path)
    file_size = output_path.stat().st_size
    return JobResponse(
        job_id=job_id,
        task_id=task_id,
        status="succeed",
        result_url=f"/videos/{output_filename}",
        file_size=f"{file_size / (1024*1024):.2f} MB",
        generation_time=round(time.time() - start_time, 2),
        raw_response={"video_id": video_id}
    )


@app.post("/video2audio")
async def video2audio(
    prompt: str = Form(...),
    video_id: str | None = Form(None),
    video_url: str | None = Form(None),
    video_file: UploadFile | None = File(None),
    voice_control: str | None = Form(None),
):
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    jwt_token = _generate_jwt()

    payload = {
        "prompt": prompt,
    }
    if video_id:
        payload["video_id"] = video_id
    elif video_url:
        payload["video"] = {"url": video_url}
    elif video_file:
        payload["video"] = {"url": _save_and_data_uri(video_file, job_id, "video", VIDEO_EXTS, MAX_VIDEO_SIZE)}
    if voice_control:
        try:
            payload["voice_control"] = json.loads(voice_control)
        except Exception:
            pass

    resp = _post_kling(jwt_token, "videos/video2audio", payload, job_id)
    task_id = resp.get("data", {}).get("task_id") or resp.get("data", {}).get("id")
    result_url, result_id = poll_task_status(jwt_token, KLING_API_BASE, task_id, "videos/video2audio", logger)

    output_filename = f"kling_audio_{job_id}_{int(time.time())}.mp4"
    output_path = VIDEOS_DIR / output_filename
    _download_video(result_url, output_path)
    file_size = output_path.stat().st_size
    return JobResponse(
        job_id=job_id,
        task_id=task_id,
        status="succeed",
        result_url=f"/videos/{output_filename}",
        file_size=f"{file_size / (1024*1024):.2f} MB",
        generation_time=round(time.time() - start_time, 2),
        raw_response={"audio_id": result_id}
    )


@app.post("/multi-image2video")
async def multi_image2video(
    images: List[UploadFile] = File(...),
    prompt: str = Form(...),
    negative_prompt: str = Form("blurry, distorted"),
    model_name: str = Form("kling-v1-6"),
    duration: str = Form("10"),
    aspect_ratio: str = Form("16:9"),
    mode: str = Form("pro"),
):
    if len(images) < 2:
        raise HTTPException(status_code=400, detail="At least 2 images are required")
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="Max 10 images allowed")

    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    jwt_token = _generate_jwt()

    image_items = []
    for idx, img in enumerate(images):
        image_items.append({"url": _save_and_data_uri(img, job_id, f"img{idx}", IMAGE_EXTS, MAX_IMAGE_SIZE)})

    payload = {
        "images": image_items,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "model_name": model_name,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "mode": mode,
    }

    resp = _post_kling(jwt_token, "videos/multi-image2video", payload, job_id)
    task_id = resp.get("data", {}).get("task_id") or resp.get("data", {}).get("id")
    video_url, video_id = poll_task_status(jwt_token, KLING_API_BASE, task_id, "videos/multi-image2video", logger)

    output_filename = f"kling_multi_{job_id}_{int(time.time())}.mp4"
    output_path = VIDEOS_DIR / output_filename
    _download_video(video_url, output_path)
    file_size = output_path.stat().st_size
    return JobResponse(
        job_id=job_id,
        task_id=task_id,
        status="succeed",
        result_url=f"/videos/{output_filename}",
        file_size=f"{file_size / (1024*1024):.2f} MB",
        generation_time=round(time.time() - start_time, 2),
        raw_response={"video_id": video_id}
    )

def _generate_jwt() -> str:
    """Generate JWT token from access_key and secret_key"""
    try:
        response = requests.post(
            JWT_SERVICE_URL,
            json={
                "access_key": KLING_ACCESS_KEY,
                "secret_key": KLING_SECRET_KEY
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["jwt_token"]
    except Exception as e:
        logger.error(f"JWT generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"JWT generation failed: {str(e)}")

def _create_video(jwt_token: str, request: VideoGenerationRequest, job_id: str, prompt: str) -> str:
    """Create video and return task_id"""
    url = f"{KLING_API_BASE}/videos/text2video"
    
    payload = {
        "prompt": prompt,
        "negative_prompt": request.negative_prompt,
        "model_name": request.model_name,
        "duration": request.duration,
        "aspect_ratio": request.aspect_ratio,
        "mode": request.mode,
        "sound": request.sound
    }
    
    if request.camera_control:
        payload["camera_control"] = request.camera_control.model_dump(exclude_none=True)
    if getattr(request, "motion_control", None):
        payload["motion_control"] = request.motion_control.model_dump(exclude_none=True)
    if getattr(request, "motion_brush", None):
        payload["motion_brush"] = request.motion_brush
    if getattr(request, "object_motion", None):
        payload["object_motion"] = request.object_motion
    if getattr(request, "voice_narration", None):
        payload["voice_narration"] = request.voice_narration
    if getattr(request, "voice_control", None):
        payload["voice_control"] = request.voice_control.model_dump(exclude_none=True)
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code != 200:
        logger.error(f"[{job_id}] Kling API error: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    data = response.json()
    return data["data"]["task_id"]

def _extend_video(jwt_token: str, video_id: str, prompt: str, job_id: str) -> str:
    """Extend video and return task_id"""
    url = f"{KLING_API_BASE}/videos/video-extend"
    
    payload = {
        "video_id": video_id,
        "prompt": prompt
    }
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code != 200:
        logger.error(f"[{job_id}] Kling extend API error: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    data = response.json()
    return data["data"]["task_id"]

def _poll_video_status(jwt_token: str, task_id: str, job_id: str, iteration: int, max_polls: int = 60) -> tuple[str, str]:
    """Poll video status until ready and return (video_url, video_id)"""
    url = f"{KLING_API_BASE}/videos/text2video/{task_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    
    poll_count = 0
    start_time = time.time()
    
    while poll_count < max_polls:
        poll_count += 1
        elapsed = time.time() - start_time
        
        logger.info(f"[{job_id}] Iteration {iteration} - Poll #{poll_count} (elapsed: {elapsed:.0f}s)")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        task_status = data["data"]["task_status"]
        
        logger.info(f"[{job_id}] Status: {task_status}")
        
        if task_status == "succeed":
            task_result = data["data"]["task_result"]
            video_url = task_result["videos"][0]["url"]
            video_id = task_result["videos"][0].get("id", "")
            logger.info(f"[{job_id}] ✅ Video ready after {elapsed:.0f}s")
            return video_url, video_id
        elif task_status in ["submitted", "processing"]:
            time.sleep(10)  # Wait 10 seconds before next poll
        else:
            # failed or unknown status
            raise HTTPException(
                status_code=500,
                detail=f"Video generation failed with status: {task_status}"
            )
    
    # Timeout
    raise TimeoutError(f"Video generation timed out after {poll_count} polls ({poll_count * 10 / 60:.1f} minutes)")

def _download_video(video_url: str, output_path: Path):


def _save_and_data_uri(upload: UploadFile, job_id: str, prefix: str, allowed, max_size: int) -> str:
    saved = save_upload_file(upload, job_id, prefix, allowed, max_size)
    return file_to_data_uri(saved)

    """Download video from URL to local path"""
    response = requests.get(video_url, timeout=300)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    logger.info(f"Video downloaded: {output_path.name}")

@app.get("/videos/{filename}")
async def get_video(filename: str):
    """Download a generated video by filename"""
    # Security: validate filename
    if not filename.endswith('.mp4') or '/' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    video_path = VIDEOS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    logger.info(f"Serving video: {filename}")
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )

@app.get("/videos")
async def list_videos():
    """List all generated videos in storage"""
    videos = []
    for video_path in VIDEOS_DIR.glob("*.mp4"):
        stat = video_path.stat()
        videos.append({
            "filename": video_path.name,
            "size": f"{stat.st_size / (1024 * 1024):.2f} MB",
            "created": stat.st_ctime,
            "url": f"/videos/{video_path.name}"
        })
    
    return {
        "videos_dir": str(VIDEOS_DIR),
        "count": len(videos),
        "videos": sorted(videos, key=lambda x: x['created'], reverse=True)
    }

@app.delete("/videos/{filename}")
async def delete_video(filename: str):
    """Delete a generated video"""
    # Security: validate filename
    if not filename.endswith('.mp4') or '/' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    video_path = VIDEOS_DIR / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_path.unlink()
    logger.info(f"Deleted video: {filename}")
    
    return {"status": "deleted", "filename": filename}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

