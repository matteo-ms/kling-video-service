# 🔗 n8n Integration Guide

Complete guide for integrating Kling Video Generation Service with n8n workflows.

## Quick Setup

### 1. Deploy Service

Deploy to Railway or run locally:

```bash
# Local
export KLING_ACCESS_KEY="your_key"
export KLING_SECRET_KEY="your_secret"
python app.py

# Railway
# Set environment variables in Railway dashboard
```

### 2. Add HTTP Request Node in n8n

```json
{
  "parameters": {
    "url": "https://your-kling-service.railway.app/generate-video",
    "method": "POST",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={\n  \"prompt\": \"{{ $json.prompt }}\",\n  \"target_duration\": {{ $json.duration || 20 }},\n  \"aspect_ratio\": \"16:9\",\n  \"model_name\": \"kling-v2-6\",\n  \"mode\": \"pro\",\n  \"sound\": \"on\"\n}",
    "options": {
      "timeout": 3600000
    }
  },
  "type": "n8n-nodes-base.httpRequest",
  "name": "Generate Kling Video"
}
```

## Complete Workflow Examples

### Example 1: Simple Video Generation

```json
{
  "nodes": [
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "prompt",
              "value": "Medium shot of open textbook and penciled notes on desk, amber lamp glow against charcoal shadows, rain tapping softly at window beyond, static with slight focus shift to paper, cinematic, 4k",
              "type": "string"
            },
            {
              "name": "duration",
              "value": 30,
              "type": "number"
            }
          ]
        }
      },
      "name": "Set Parameters",
      "type": "n8n-nodes-base.set",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://your-service.railway.app/generate-video",
        "method": "POST",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\n  \"prompt\": \"{{ $json.prompt }}\",\n  \"target_duration\": {{ $json.duration }},\n  \"aspect_ratio\": \"16:9\",\n  \"model_name\": \"kling-v2-6\",\n  \"mode\": \"pro\"\n}",
        "options": {
          "timeout": 3600000
        }
      },
      "name": "Generate Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "url": "=https://your-service.railway.app{{ $json.video_url }}",
        "options": {
          "response": {
            "response": {
              "responseFormat": "file"
            }
          }
        }
      },
      "name": "Download Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [680, 300]
    }
  ],
  "connections": {
    "Set Parameters": {
      "main": [[{"node": "Generate Video", "type": "main", "index": 0}]]
    },
    "Generate Video": {
      "main": [[{"node": "Download Video", "type": "main", "index": 0}]]
    }
  }
}
```

### Example 2: Multi-Prompt Video with Extensions

```json
{
  "nodes": [
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "prompt",
              "value": "Cinematic aerial view of misty mountains at sunrise",
              "type": "string"
            },
            {
              "name": "target_duration",
              "value": 40,
              "type": "number"
            },
            {
              "name": "aspect_ratio",
              "value": "16:9",
              "type": "string"
            }
          ]
        }
      },
      "name": "Config",
      "type": "n8n-nodes-base.set",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://your-service.railway.app/generate-video",
        "method": "POST",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={\n  \"prompt\": \"{{ $json.prompt }}\",\n  \"target_duration\": {{ $json.target_duration }},\n  \"aspect_ratio\": \"{{ $json.aspect_ratio }}\",\n  \"model_name\": \"kling-v2-6\",\n  \"mode\": \"pro\",\n  \"sound\": \"on\"\n}",
        "options": {
          "timeout": 3600000
        }
      },
      "name": "Generate Extended Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    },
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "video_id",
              "value": "={{ $json.video_id }}",
              "type": "string"
            },
            {
              "name": "video_url",
              "value": "={{ $json.video_url }}",
              "type": "string"
            },
            {
              "name": "duration",
              "value": "={{ $json.duration }}",
              "type": "number"
            },
            {
              "name": "iterations",
              "value": "={{ $json.iterations }}",
              "type": "number"
            }
          ]
        }
      },
      "name": "Extract Results",
      "type": "n8n-nodes-base.set",
      "position": [680, 300]
    }
  ],
  "connections": {
    "Config": {
      "main": [[{"node": "Generate Extended Video", "type": "main", "index": 0}]]
    },
    "Generate Extended Video": {
      "main": [[{"node": "Extract Results", "type": "main", "index": 0}]]
    }
  }
}
```

### Example 3: Video Extension Only

```json
{
  "nodes": [
    {
      "parameters": {
        "assignments": {
          "assignments": [
            {
              "name": "video_id",
              "value": "838001376042680322",
              "type": "string"
            },
            {
              "name": "prompt",
              "value": "Continue with camera slowly panning right",
              "type": "string"
            }
          ]
        }
      },
      "name": "Extension Config",
      "type": "n8n-nodes-base.set",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "=https://your-service.railway.app/extend-video?video_id={{ $json.video_id }}&prompt={{ encodeURIComponent($json.prompt) }}",
        "method": "POST",
        "options": {
          "timeout": 3600000
        }
      },
      "name": "Extend Video",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    }
  ],
  "connections": {
    "Extension Config": {
      "main": [[{"node": "Extend Video", "type": "main", "index": 0}]]
    }
  }
}
```

## Advanced Patterns

### Pattern 1: Conditional Quality Mode

```javascript
// In Set node
{
  "mode": "={{ $json.highQuality ? 'pro' : 'std' }}",
  "duration": "={{ $json.highQuality ? '10' : '5' }}"
}
```

### Pattern 2: Dynamic Aspect Ratio

```javascript
// Based on platform
{
  "aspect_ratio": "={{ $json.platform === 'youtube' ? '16:9' : ($json.platform === 'tiktok' ? '9:16' : '1:1') }}"
}
```

### Pattern 3: Camera Control

```json
{
  "prompt": "{{ $json.prompt }}",
  "camera_control": {
    "type": "simple",
    "horizontal": 5,
    "vertical": 0,
    "pan": 3,
    "zoom": 2
  }
}
```

## Error Handling

### Add Error Workflow Node

```json
{
  "parameters": {
    "conditions": {
      "conditions": [
        {
          "leftValue": "={{ $json.error }}",
          "rightValue": "",
          "operator": {
            "type": "string",
            "operation": "notEmpty"
          }
        }
      ]
    }
  },
  "name": "Check for Errors",
  "type": "n8n-nodes-base.if"
}
```

### Retry Logic

```json
{
  "parameters": {
    "amount": 5,
    "unit": "minutes"
  },
  "name": "Wait Before Retry",
  "type": "n8n-nodes-base.wait"
}
```

## Performance Tips

1. **Timeout Settings**: Set HTTP request timeout to at least 3600000ms (1 hour) for long videos
2. **Parallel Processing**: Use Split In Batches node for multiple videos
3. **Webhook Mode**: Use webhook for async processing of very long videos
4. **Storage**: Download and store videos immediately (they're ephemeral on Railway)

## Monitoring

### Add Logging Node

```json
{
  "parameters": {
    "assignments": {
      "assignments": [
        {
          "name": "timestamp",
          "value": "={{ new Date().toISOString() }}",
          "type": "string"
        },
        {
          "name": "job_id",
          "value": "={{ $json.job_id }}",
          "type": "string"
        },
        {
          "name": "duration",
          "value": "={{ $json.duration }}",
          "type": "number"
        },
        {
          "name": "generation_time",
          "value": "={{ $json.generation_time }}",
          "type": "number"
        }
      ]
    }
  },
  "name": "Log Results",
  "type": "n8n-nodes-base.set"
}
```

## Common Issues

### Issue 1: Timeout Errors

**Solution**: Increase timeout in HTTP Request node options:

```json
{
  "options": {
    "timeout": 3600000
  }
}
```

### Issue 2: Video Not Downloading

**Solution**: Use file response format:

```json
{
  "options": {
    "response": {
      "response": {
        "responseFormat": "file"
      }
    }
  }
}
```

### Issue 3: JWT Errors

**Solution**: Check service logs and verify credentials are set correctly in Railway.

## Full Production Workflow

See `n8n-kling-workflow.json` for a complete production-ready workflow with:
- Error handling
- Retry logic
- Logging
- File storage
- Notifications

## Support

For issues:
1. Check service logs: `railway logs`
2. Test endpoint directly: `curl https://your-service.railway.app/health`
3. Verify credentials in Railway dashboard
4. Check n8n execution logs

