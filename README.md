# 🎬 Kling Video Generation Service

FastAPI service for generating long-form videos using **Kling AI** with automatic video extension.

## Features

- ✅ Generate videos from 5s to 100s with automatic extension
- ✅ JWT authentication with external service
- ✅ Support for Kling v1, v1.5, and v2.6 models
- ✅ Camera control (pan, tilt, zoom, roll)
- ✅ Multiple aspect ratios (16:9, 9:16, 1:1)
- ✅ Pro and Standard quality modes
- ✅ Optional sound generation
- ✅ RESTful API with OpenAPI docs
- ✅ Health check endpoint
- ✅ Video management (list, download, delete)
- ✅ Comprehensive logging
- ✅ Docker support
- ✅ Ready for Railway deployment

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export KLING_ACCESS_KEY="your_access_key"
export KLING_SECRET_KEY="your_secret_key"

# Run server
python app.py
```

Server will start at `http://localhost:8000`

### Docker

```bash
# Build image
docker build -t kling-video-service .

# Run container
docker run -p 8000:8000 \
  -e KLING_ACCESS_KEY="your_access_key" \
  -e KLING_SECRET_KEY="your_secret_key" \
  kling-video-service
```

### Railway Deploy

1. Push to GitHub
2. Create new project on Railway
3. Connect GitHub repository
4. Add environment variables:
   - `KLING_ACCESS_KEY`
   - `KLING_SECRET_KEY`
5. Deploy automatically

## API Documentation

### Interactive Docs

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### Generate Video

```bash
POST /generate-video
```

**Request (Single Prompt):**

```json
{
  "prompt": "Medium shot of open textbook and penciled notes on desk, amber lamp glow against charcoal shadows, rain tapping softly at window beyond, static with slight focus shift to paper, cinematic, 4k",
  "negative_prompt": "blurry, distorted, low quality, watermark",
  "model_name": "kling-v2-6",
  "duration": "10",
  "aspect_ratio": "16:9",
  "mode": "pro",
  "sound": "on",
  "target_duration": 30
}
```

**Request (Multi-Prompt Array):**

```json
{
  "prompts": [
    "Wide shot of misty forest at dawn, soft golden light filtering through trees",
    "Camera slowly moves forward through the forest path, revealing a clearing",
    "Close-up of morning dew on leaves, bokeh background, peaceful atmosphere"
  ],
  "model_name": "kling-v2-6",
  "duration": "10",
  "aspect_ratio": "16:9",
  "mode": "pro",
  "sound": "on"
}
```

**Response:**

```json
{
  "job_id": "a3f2c1b4",
  "video_url": "/videos/kling_a3f2c1b4_1704672000.mp4",
  "video_id": "838001376042680322",
  "task_id": "task_abc123",
  "duration": 30,
  "iterations": 3,
  "file_size": "18.43 MB",
  "generation_time": 245.67
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cinematic aerial view of misty mountains at sunrise, golden light breaking through clouds, smooth forward movement, epic landscape, 4k quality",
    "target_duration": 20,
    "aspect_ratio": "16:9",
    "mode": "pro"
  }'
```

#### Extend Video

```bash
POST /extend-video
```

**Parameters:**
- `video_id`: Video ID from previous generation
- `prompt`: Prompt for the extension

**Example:**

```bash
curl -X POST "http://localhost:8000/extend-video?video_id=838001376042680322&prompt=Continue the scene with camera slowly panning right"
```

#### Download Video

```bash
GET /videos/{filename}
```

**Example:**

```bash
curl http://localhost:8000/videos/kling_a3f2c1b4_1704672000.mp4 -o my_video.mp4
```

#### List Videos

```bash
GET /videos
```

**Response:**

```json
{
  "videos_dir": "/tmp/videos",
  "count": 3,
  "videos": [
    {
      "filename": "kling_a3f2c1b4_1704672000.mp4",
      "size": "18.43 MB",
      "created": 1704672000.123,
      "url": "/videos/kling_a3f2c1b4_1704672000.mp4"
    }
  ]
}
```

#### Delete Video

```bash
DELETE /videos/{filename}
```

#### Health Check

```bash
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "jwt_service": "connected",
  "kling_api": "connected",
  "videos_dir": "/tmp/videos",
  "videos_count": 5
}
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `KLING_ACCESS_KEY` | Kling API Access Key | ✅ Yes | - |
| `KLING_SECRET_KEY` | Kling API Secret Key | ✅ Yes | - |
| `JWT_SERVICE_URL` | JWT generation service URL | No | `https://kling-jwt-service-production.up.railway.app/generate-jwt` |
| `PORT` | Server port | No | `8000` |
| `VIDEOS_DIR` | Video storage directory | No | `/tmp/videos` |

## How It Works

### Video Generation Process

```
1. Request (30s target duration)
   ↓
2. Generate JWT token
   ↓
3. Create initial 10s video (text2video)
   ↓ (poll every 10s)
4. Video ready → Extract video_id
   ↓
5. Extend video +10s (video-extend)
   ↓ (poll)
6. Extend video +10s (video-extend)
   ↓ (poll)
... repeat until target duration
   ↓
N. Download final 30s video
```

### Architecture

- **FastAPI**: Modern async web framework
- **JWT Service**: External service for Kling authentication
- **Kling API**: Singapore region endpoint
- **Polling Strategy**: 10s intervals with max 60 polls (10 minutes)
- **Video Storage**: Local filesystem (configurable)

## Parameters

### Multi-Prompt Support

The service supports **two modes** for video generation:

1. **Single Prompt Mode**: Use `prompt` field with optional `target_duration`
   - Service will extend the video using the same prompt
   - Good for consistent scenes

2. **Multi-Prompt Array Mode**: Use `prompts` array (overrides `prompt`)
   - Each prompt generates one segment (5s or 10s based on `duration`)
   - Perfect for storytelling with scene transitions
   - Max 20 prompts supported
   - Example: `["Scene 1 description", "Scene 2 description", "Scene 3 description"]`

### Prompt Guidelines

Good prompts include:
- **Shot type**: "Wide shot", "Close-up", "Medium shot"
- **Subject**: What's in the scene
- **Lighting**: "Golden hour", "Neon lights", "Soft morning light"
- **Atmosphere**: "Moody", "Peaceful", "Energetic"
- **Camera movement**: "Slow pan", "Zoom in", "Static"
- **Quality markers**: "Cinematic", "4k", "Professional"

**Example:**

```
Medium shot of open textbook and penciled notes on desk, 
amber lamp glow against charcoal shadows, 
rain tapping softly at window beyond, 
static with slight focus shift to paper, 
cinematic, 4k
```

### Camera Control

Optional camera movement controls:

```json
{
  "camera_control": {
    "type": "simple",
    "horizontal": 5,
    "vertical": 0,
    "pan": 3,
    "tilt": 0,
    "roll": 0,
    "zoom": 2
  }
}
```

Values range from -10 to 10.

### Model Selection

- `kling-v1` - Original model
- `kling-v1-5` - Improved quality
- `kling-v2-6` - Latest model (recommended)

### Duration

- `5` - 5 seconds per segment
- `10` - 10 seconds per segment (recommended)

### Aspect Ratio

- `16:9` - Landscape (YouTube, TV)
- `9:16` - Portrait (TikTok, Instagram Stories)
- `1:1` - Square (Instagram posts)

### Mode

- `std` - Standard quality (faster, cheaper)
- `pro` - Professional quality (slower, better)

### Sound

- `on` - Generate sound effects
- `off` - Silent video

## API Limits & Costs

- **Generation time**: 60-180s per 10s segment
- **Max wait per segment**: 600s (10 min)
- **Max polls**: 60 per segment
- **Recommended max duration**: 100s

## Integration Examples

### From n8n

```json
{
  "parameters": {
    "url": "https://your-service.railway.app/generate-video",
    "method": "POST",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={\n  \"prompt\": \"{{ $json.prompt }}\",\n  \"target_duration\": 30,\n  \"aspect_ratio\": \"16:9\",\n  \"model_name\": \"kling-v2-6\",\n  \"mode\": \"pro\"\n}",
    "options": {
      "timeout": 3600000
    }
  },
  "type": "n8n-nodes-base.httpRequest",
  "name": "Generate Video"
}
```

### From Python

```python
import requests

response = requests.post(
    "http://localhost:8000/generate-video",
    json={
        "prompt": "Cinematic shot of...",
        "target_duration": 30,
        "aspect_ratio": "16:9",
        "model_name": "kling-v2-6",
        "mode": "pro"
    }
)

video_data = response.json()
video_url = video_data["video_url"]

# Download video
video_file = requests.get(f"http://localhost:8000{video_url}")
with open("output.mp4", "wb") as f:
    f.write(video_file.content)
```

### From JavaScript

```javascript
const response = await fetch('http://localhost:8000/generate-video', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prompt: "Cinematic shot of...",
    target_duration: 30,
    aspect_ratio: "16:9",
    model_name: "kling-v2-6",
    mode: "pro"
  })
});

const data = await response.json();
console.log(`Video ready: ${data.video_url}`);
```

## Logging

The service provides detailed logging:

```
2025-01-07 14:30:15 - INFO - [a3f2c1b4] Starting video generation
2025-01-07 14:30:15 - INFO - [a3f2c1b4] Prompt: Medium shot of open textbook...
2025-01-07 14:30:15 - INFO - [a3f2c1b4] JWT generated successfully
2025-01-07 14:30:16 - INFO - [a3f2c1b4] Video creation started - Task ID: task_abc123
2025-01-07 14:30:26 - INFO - [a3f2c1b4] Iteration 0 - Poll #1 (elapsed: 10s)
2025-01-07 14:31:35 - INFO - [a3f2c1b4] Status: succeed
2025-01-07 14:31:35 - INFO - [a3f2c1b4] ✅ Video ready after 79s
2025-01-07 14:31:35 - INFO - [a3f2c1b4] Extensions needed: 2 to reach 30s
2025-01-07 14:31:35 - INFO - [a3f2c1b4] Extension 1/2 - Current: 10s
...
2025-01-07 14:34:45 - INFO - [a3f2c1b4] ✅ Success! kling_a3f2c1b4_1704672000.mp4 (18.43 MB) in 270.5s
```

## Troubleshooting

### "KLING_ACCESS_KEY and KLING_SECRET_KEY are required"

Set the environment variables:

```bash
export KLING_ACCESS_KEY="your_access_key"
export KLING_SECRET_KEY="your_secret_key"
```

### "JWT generation failed"

- Check if JWT service is accessible
- Verify access_key and secret_key are correct
- Check network connectivity

### "Video generation timed out"

- Increase `max_polls` in `_poll_video_status()` (default: 60)
- Check Kling API status
- Try reducing video complexity in prompt

### Videos not persisting on Railway

Railway uses ephemeral storage. For permanent storage:
1. Add S3/GCS integration
2. Upload videos after generation
3. Return cloud storage URLs

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Format code
black app.py

# Lint
pylint app.py
```

## Limitations

- **Max duration**: ~100 seconds (recommended)
- **Storage**: Videos on Railway are ephemeral (restart = lost)
- **Rate limits**: Subject to Kling API quotas
- **JWT expiration**: Tokens expire after some time

## Roadmap

- [ ] Webhook callbacks when video ready
- [ ] S3/GCS integration for permanent storage
- [ ] Queue system for multiple concurrent jobs
- [ ] Progress tracking with SSE
- [ ] Video thumbnails generation
- [ ] Retry logic for failed generations
- [ ] Cost estimation endpoint
- [ ] Batch video generation
- [ ] Image-to-video support

## License

MIT

## Support

For issues or questions:
- Open an issue on GitHub
- Check [Kling AI documentation](https://klingai.com/docs)

