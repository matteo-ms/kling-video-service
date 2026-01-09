# Kling AI Support Ticket - Video Extension API Issue

## Subject
Video Extension API Returns Error 1201 Despite Documentation Indicating Support

## Priority
High - API Feature Not Working As Documented

## Issue Description

I am experiencing consistent failures when attempting to use the video extension API endpoint (`/v1/videos/video-extend`) with videos generated through the text-to-video API. The API returns error code **1201** with the message "This video not supported extend-video" for all newly generated videos, despite the official documentation indicating that video extension is supported for the models I'm using.

## Environment Details

- **API Endpoint**: `https://api-singapore.klingai.com/v1/videos/video-extend`
- **Authentication**: JWT token generated via `/generate-jwt` endpoint
- **API Region**: Singapore
- **Integration**: Custom Python FastAPI service

## Models Tested

According to your official documentation, the following models should support video extension:

1. **kling-v2-6** (PRO mode, 10s duration)
   - Documentation: ✅ Extension supported
   - Actual Result: ❌ Error 1201

2. **kling-v2-5-turbo** (STD mode, 5s duration)
   - Documentation: ✅ Extension supported  
   - Actual Result: ❌ Error 1201

3. **kling-v1** (STD mode, 5s duration)
   - Documentation: ✅ Extension supported
   - Actual Result: ⏳ Request timeout (>15 minutes)

## Reproduction Steps

### Step 1: Generate Initial Video
```bash
POST https://api-singapore.klingai.com/v1/videos/text2video
Headers:
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

Body:
{
  "prompt": "Close-up of coffee cup on wooden table, steam rising, warm morning light",
  "model_name": "kling-v2-5-turbo",
  "duration": "5",
  "aspect_ratio": "16:9",
  "mode": "std",
  "sound": "on"
}
```

**Result**: ✅ Success
- Task ID: `838025501410852927`
- Video ID: `838025501490561068`
- Status: `succeed`
- Generation Time: ~34 seconds

### Step 2: Attempt Video Extension
```bash
POST https://api-singapore.klingai.com/v1/videos/video-extend
Headers:
  Authorization: Bearer {jwt_token}
  Content-Type: application/json

Body:
{
  "video_id": "838025501490561068",
  "prompt": "Continue with the same scene, steam still rising"
}
```

**Result**: ❌ Error
```json
{
  "code": 1201,
  "message": "This video not supported extend-video",
  "request_id": "8cfad4f6-1c36-4c95-b0d5-ee878ecc6fa1"
}
```

## Additional Test Cases

### Test Case 1: kling-v2-6 PRO Mode
- Initial video: ✅ Generated successfully (10s, PRO mode)
- Extension attempt: ❌ Error 1201
- Request ID: `09c8e65a-411c-43fa-9fe6-c02cb7862d5e`

### Test Case 2: kling-v1 STD Mode  
- Initial video: ⏳ Request timeout after 15+ minutes
- Extension attempt: Not reached due to timeout

### Test Case 3: kling-v2-5-turbo STD Mode
- Initial video: ✅ Generated successfully (5s, STD mode)
- Extension attempt: ❌ Error 1201
- Request ID: `8cfad4f6-1c36-4c95-b0d5-ee878ecc6fa1`

## Expected Behavior

Based on your official documentation (provided in my implementation):

| Model | Mode | Duration | Extension Support |
|-------|------|----------|-------------------|
| kling-v1 | std/pro | 5s/10s | ✅ YES |
| kling-v1-5 | std/pro | 5s/10s | ✅ YES |
| kling-v1-6 | std/pro | 5s/10s | ✅ YES |
| kling-v2-5-turbo | std/pro | 5s/10s | ✅ YES |

The documentation clearly states that video extension is supported for these models, but the API consistently rejects extension requests.

## Actual Behavior

All video extension requests fail with error code 1201, regardless of:
- Model used (v1, v2-5-turbo, v2-6)
- Mode (std or pro)
- Duration (5s or 10s)
- Prompt content
- Video generation success

## Questions

1. **Is there a specific requirement or parameter needed to make videos "extensible"?**
   - Are there undocumented parameters in the text2video request that enable extension support?
   - Do videos need specific settings (resolution, frame rate, etc.) to be extensible?

2. **Is video extension available for all API accounts?**
   - Does this feature require a specific subscription tier?
   - Are there quota limits or restrictions on video extension?

3. **Is there a delay required between video generation and extension?**
   - Should I wait for a specific amount of time before attempting extension?
   - Do videos need to be "processed" or "finalized" before extension is possible?

4. **Are there specific models or configurations that support extension?**
   - Which exact model versions currently support video extension?
   - What are the complete requirements for a video to be extensible?

## Impact

This issue is blocking the implementation of a critical feature in our video generation service. We have built a production system based on your API documentation that relies on video extension to create longer-form content (15-60 seconds). 

Currently, we can only generate single-segment videos (5-10 seconds), which significantly limits the usefulness of the service for our use case.

## Request

Please provide:

1. **Clarification** on why video extension is failing with error 1201
2. **Documentation** on the correct way to use video extension API
3. **Requirements** for videos to be eligible for extension
4. **Timeline** for when this feature will be available (if currently unavailable)
5. **Workarounds** or alternative approaches to create longer videos

## Service Implementation

For reference, our implementation is available at:
- GitHub: https://github.com/matteo-ms/kling-video-service
- Production: https://kling-video-service-production.up.railway.app

The service successfully:
- ✅ Generates JWT tokens
- ✅ Creates single-segment videos (5s, 10s)
- ✅ Polls for video completion
- ✅ Downloads and serves videos
- ❌ Cannot extend videos (error 1201)

## Contact Information

Please respond with:
- Explanation of the error
- Correct API usage for video extension
- Any account-specific limitations
- Timeline for resolution if this is a known issue

Thank you for your assistance in resolving this issue.

---

**Date**: January 8, 2025  
**API Version**: v1  
**Integration Type**: REST API with JWT authentication

