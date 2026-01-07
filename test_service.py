"""
Test script for Kling Video Generation Service
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_generate_video():
    """Test video generation"""
    print("🎬 Testing video generation...")
    
    payload = {
        "prompt": "Medium shot of open textbook and penciled notes on desk, amber lamp glow against charcoal shadows, rain tapping softly at window beyond, static with slight focus shift to paper, cinematic, 4k",
        "negative_prompt": "blurry, distorted, low quality, watermark, text",
        "model_name": "kling-v2-6",
        "duration": "10",
        "aspect_ratio": "16:9",
        "mode": "pro",
        "sound": "on",
        "target_duration": 20
    }
    
    print(f"Request payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/generate-video", json=payload)
    elapsed = time.time() - start_time
    
    print(f"Status: {response.status_code}")
    print(f"Time: {elapsed:.1f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        print(f"\n✅ Video ready: {data['video_url']}")
        return data['video_url']
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_list_videos():
    """Test list videos endpoint"""
    print("📋 Testing list videos...")
    response = requests.get(f"{BASE_URL}/videos")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()

def test_download_video(video_url):
    """Test video download"""
    if not video_url:
        print("⏭️  Skipping download test (no video URL)")
        return
    
    print(f"⬇️  Testing video download: {video_url}")
    response = requests.get(f"{BASE_URL}{video_url}")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Size: {len(response.content) / (1024*1024):.2f} MB")
    
    if response.status_code == 200:
        filename = "test_output.mp4"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Video saved to {filename}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Kling Video Generation Service - Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: List videos
        test_list_videos()
        
        # Test 3: Generate video
        video_url = test_generate_video()
        
        # Test 4: Download video
        test_download_video(video_url)
        
        # Test 5: List videos again
        test_list_videos()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

