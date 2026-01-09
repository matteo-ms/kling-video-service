 # Failed Video Extension Task IDs - Complete Report for Kling Support

## Summary
All video extension attempts failed with **Error 1201**: "This video not supported extend-video"

**Important Note**: Extension requests failed immediately without generating a new Task ID. The API returns error 1201 before creating a task.

---

## Failed Extension Request #1

### Base Video That Was Attempted to Extend
- ✅ **Generation Status**: Success
- **Base Video Task ID**: `838014510966374444`
- **Base Video ID**: `838014511067037763`
- **Model**: `kling-v2-6`
- **Mode**: `pro`
- **Duration**: `10s`
- **Aspect Ratio**: `16:9`
- **Sound**: `on`
- **Prompt**: "Medium shot of open textbook and penciled notes on desk, amber lamp glow against charcoal shadows, rain tapping softly at window beyond, static with slight focus shift to paper, cinematic, 4k"
- **Generation Time**: 126.1 seconds
- **File Size**: 6.07 MB
- **Generated Date**: January 8, 2025

### Extension Request Details
- ❌ **Extension Status**: Failed immediately
- **Extension Request ID**: `09c8e65a-411c-43fa-9fe6-c02cb7862d5e`
- **Extension Task ID**: N/A (not generated due to immediate error)
- **Video ID Used**: `838014511067037763` (base video to extend)
- **Error Code**: `1201`
- **Error Message**: "This video not supported extend-video"
- **Extension Prompt**: "Cinematic aerial view of misty mountains at sunrise, golden light breaking through clouds, smooth forward movement, epic landscape, 4k quality"
- **Target Duration**: 30s (requiring 2 extensions)
- **API Endpoint**: `POST /v1/videos/video-extend`

---

## Failed Extension Request #2

### Base Video That Was Attempted to Extend
- ✅ **Generation Status**: Success
- **Base Video Task ID**: `838025501410852927`
- **Base Video ID**: `838025501490561068`
- **Model**: `kling-v2-5-turbo`
- **Mode**: `std`
- **Duration**: `5s`
- **Aspect Ratio**: `16:9`
- **Sound**: `on`
- **Prompt**: "Close-up of coffee cup on wooden table, steam rising, warm morning light"
- **Generation Time**: 33.76 seconds
- **File Size**: 4.77 MB
- **Generated Date**: January 8, 2025

### Extension Request Details
- ❌ **Extension Status**: Failed immediately
- **Extension Request ID**: `8cfad4f6-1c36-4c95-b0d5-ee878ecc6fa1`
- **Extension Task ID**: N/A (not generated due to immediate error)
- **Video ID Used**: `838025501490561068` (base video to extend)
- **Error Code**: `1201`
- **Error Message**: "This video not supported extend-video"
- **Extension Prompt**: "Close-up of coffee cup on wooden table, steam rising, warm morning light"
- **Target Duration**: 10s (requiring 1 extension)
- **API Endpoint**: `POST /v1/videos/video-extend`

---

## Summary Table for Support

| Test | Base Task ID | Base Video ID | Model | Mode | Duration | Extension Request ID | Extension Error |
|------|--------------|---------------|-------|------|----------|---------------------|-----------------|
| #1 | `838014510966374444` | `838014511067037763` | kling-v2-6 | pro | 10s | `09c8e65a-411c-43fa-9fe6-c02cb7862d5e` | Error 1201 |
| #2 | `838025501410852927` | `838025501490561068` | kling-v2-5-turbo | std | 5s | `8cfad4f6-1c36-4c95-b0d5-ee878ecc6fa1` | Error 1201 |

---

## Key Information for Support Team

### What Works
✅ JWT token generation  
✅ Base video generation (text2video endpoint)  
✅ Video polling and status checks  
✅ Video download from CDN URLs  

### What Fails
❌ Video extension (video-extend endpoint)  
❌ Error code 1201 on ALL extension attempts  
❌ Happens regardless of model, mode, or duration  
❌ Fails immediately (no task created)  

### Extension Request Payload Used
```json
{
  "video_id": "838014511067037763",
  "prompt": "Extension prompt text"
}
```

### Extension Request Headers
```
Authorization: Bearer {valid_jwt_token}
Content-Type: application/json
```

---

## Complete Extension Request Examples

### Extension Request #1 (Failed)
```bash
POST https://api-singapore.klingai.com/v1/videos/video-extend
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "video_id": "838014511067037763",
  "prompt": "Cinematic aerial view of misty mountains at sunrise, golden light breaking through clouds, smooth forward movement, epic landscape, 4k quality"
}

Response (Error):
{
  "code": 1201,
  "message": "This video not supported extend-video",
  "request_id": "09c8e65a-411c-43fa-9fe6-c02cb7862d5e"
}
```

### Extension Request #2 (Failed)
```bash
POST https://api-singapore.klingai.com/v1/videos/video-extend
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "video_id": "838025501490561068",
  "prompt": "Close-up of coffee cup on wooden table, steam rising, warm morning light"
}

Response (Error):
{
  "code": 1201,
  "message": "This video not supported extend-video",
  "request_id": "8cfad4f6-1c36-4c95-b0d5-ee878ecc6fa1"
}
```

---

## Test Environment

- **Service URL**: https://kling-video-service-production.up.railway.app
- **API Region**: Singapore (api-singapore.klingai.com)
- **Authentication Method**: JWT tokens (generated via /generate-jwt)
- **Test Date**: January 8, 2025
- **API Version**: v1
- **Client**: Custom Python FastAPI service

---

## Questions for Support

1. **Are there specific requirements for videos to be extensible?**
   - Do videos need special parameters during generation?
   - Is there a waiting period after generation before extension?
   - Are there account-level restrictions on extension?

2. **Which models actually support extension currently?**
   - Documentation says v1, v1-5, v1-6, v2-5-turbo support it
   - All our tests with these models fail with error 1201

3. **Is extension feature available for all API accounts?**
   - Do we need a specific subscription tier?
   - Are there quota limits we might have hit?

4. **What does error 1201 specifically mean?**
   - Is it a permanent restriction on these videos?
   - Is it a temporary API limitation?
   - Is it a configuration issue?

---

## Additional Context

### Both Base Videos Are:
- Successfully generated ✅
- Accessible via CDN URLs ✅
- Downloadable and playable ✅
- Generated with valid JWT tokens ✅
- Meeting all documented requirements ✅

### Extension Requests:
- Use same JWT tokens as generation ✅
- Use correct video_id from generation response ✅
- Include valid prompt text ✅
- Target correct API endpoint ✅
- Fail immediately with error 1201 ❌

**Conclusion**: The issue appears to be a restriction or missing requirement for videos to be eligible for extension, not a technical failure in our implementation or the API itself.

