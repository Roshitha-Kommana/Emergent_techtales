#!/usr/bin/env python3
"""
Specific PIL-based Image Generation Test
Tests the new educational diagram generator with various visual cues
"""

import asyncio
import aiohttp
import json
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

async def test_specific_visual_cues():
    """Test PIL-based image generation with specific visual cues"""
    
    # Test cases as specified in the review request
    test_cases = [
        {
            "topic": "OSI Model Layers",
            "expected_diagrams": "layer diagrams",
            "age_group": "adult",
            "difficulty": "intermediate"
        },
        {
            "topic": "Database Schema Design", 
            "expected_diagrams": "database diagrams",
            "age_group": "adult",
            "difficulty": "advanced"
        },
        {
            "topic": "Computer Network Architecture",
            "expected_diagrams": "network diagrams", 
            "age_group": "teen",
            "difficulty": "beginner"
        }
    ]
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
        print("🎨 Testing PIL-based Educational Diagram Generation")
        print("=" * 60)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 Test {i}: {test_case['topic']}")
            print(f"Expected: {test_case['expected_diagrams']}")
            
            try:
                async with session.post(
                    f"{API_BASE_URL}/generate-lesson",
                    json=test_case,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        lesson_data = await response.json()
                        
                        print(f"✅ API Response: Success")
                        print(f"📖 Story length: {len(lesson_data.get('story', ''))} characters")
                        print(f"👁️ Visual cues: {len(lesson_data.get('visual_cues', []))}")
                        
                        # Focus on image generation
                        images = lesson_data.get('images', [])
                        print(f"🖼️ Generated images: {len(images)}")
                        
                        if images:
                            total_size = 0
                            for j, img in enumerate(images):
                                try:
                                    decoded = base64.b64decode(img)
                                    size = len(decoded)
                                    total_size += size
                                    print(f"  ✅ Image {j+1}: {size:,} bytes (valid base64)")
                                except Exception as e:
                                    print(f"  ❌ Image {j+1}: Invalid - {str(e)}")
                            
                            print(f"📊 Total image data: {total_size:,} bytes")
                            
                            # Show visual cues that generated the images
                            visual_cues = lesson_data.get('visual_cues', [])
                            print(f"🎯 Visual cues used:")
                            for k, cue in enumerate(visual_cues[:3]):  # Only first 3 are used for images
                                print(f"  {k+1}. {cue}")
                        else:
                            print("❌ No images generated!")
                            
                    else:
                        error_text = await response.text()
                        print(f"❌ API Error: {response.status} - {error_text}")
                        
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🏁 PIL-based Image Generation Test Complete")

if __name__ == "__main__":
    asyncio.run(test_specific_visual_cues())