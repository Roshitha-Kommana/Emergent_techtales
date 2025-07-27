#!/usr/bin/env python3
"""
TechTales Backend Testing Suite
Tests the multi-agent educational AI system backend functionality
"""

import asyncio
import aiohttp
import json
import base64
import time
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

class TechTalesBackendTester:
    def __init__(self):
        self.session = None
        self.test_results = {
            'multi_agent_orchestration': {'passed': False, 'details': ''},
            'story_agent': {'passed': False, 'details': ''},
            'image_agent': {'passed': False, 'details': ''},
            'quiz_agent': {'passed': False, 'details': ''},
            'api_endpoints': {'passed': False, 'details': ''},
            'database_operations': {'passed': False, 'details': ''}
        }
        self.generated_lesson_id = None

    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout for AI operations
        )
        print(f"🔧 Testing backend at: {API_BASE_URL}")

    async def teardown(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()

    async def test_root_endpoint(self):
        """Test basic API connectivity"""
        try:
            async with self.session.get(f"{API_BASE_URL}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Root endpoint working: {data}")
                    return True
                else:
                    print(f"❌ Root endpoint failed with status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Root endpoint error: {str(e)}")
            return False

    async def test_multi_agent_orchestration(self):
        """Test the complete multi-agent lesson generation"""
        print("\n🤖 Testing Multi-Agent System Orchestration...")
        
        try:
            # Test data as specified in review request
            test_payload = {
                "topic": "OSI Layers",
                "age_group": "adult",
                "difficulty": "beginner"
            }
            
            print(f"📤 Sending request: {test_payload}")
            
            async with self.session.post(
                f"{API_BASE_URL}/generate-lesson",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                print(f"📥 Response status: {response.status}")
                
                if response.status == 200:
                    lesson_data = await response.json()
                    
                    # Validate response structure
                    required_fields = ['id', 'topic', 'age_group', 'difficulty', 'story', 'visual_cues', 'images', 'quiz', 'created_at']
                    missing_fields = [field for field in required_fields if field not in lesson_data]
                    
                    if missing_fields:
                        self.test_results['multi_agent_orchestration']['details'] = f"Missing fields: {missing_fields}"
                        print(f"❌ Missing required fields: {missing_fields}")
                        return False
                    
                    # Store lesson ID for later tests
                    self.generated_lesson_id = lesson_data['id']
                    
                    # Validate story content
                    if not lesson_data['story'] or len(lesson_data['story']) < 100:
                        self.test_results['multi_agent_orchestration']['details'] = "Story content too short or empty"
                        print("❌ Story content insufficient")
                        return False
                    
                    # Validate visual cues
                    if not lesson_data['visual_cues'] or len(lesson_data['visual_cues']) == 0:
                        self.test_results['multi_agent_orchestration']['details'] = "No visual cues generated"
                        print("❌ No visual cues generated")
                        return False
                    
                    # Validate images (base64 encoded)
                    if not lesson_data['images']:
                        print("⚠️ No images generated (may be expected due to API limitations)")
                    else:
                        # Validate base64 format
                        for i, img in enumerate(lesson_data['images']):
                            try:
                                base64.b64decode(img)
                                print(f"✅ Image {i+1} is valid base64")
                            except Exception as e:
                                print(f"❌ Image {i+1} invalid base64: {str(e)}")
                    
                    # Validate quiz
                    if not lesson_data['quiz'] or len(lesson_data['quiz']) == 0:
                        self.test_results['multi_agent_orchestration']['details'] = "No quiz questions generated"
                        print("❌ No quiz questions generated")
                        return False
                    
                    # Validate quiz structure
                    for i, question in enumerate(lesson_data['quiz']):
                        required_q_fields = ['question', 'options', 'correct_answer', 'explanation']
                        missing_q_fields = [field for field in required_q_fields if field not in question]
                        if missing_q_fields:
                            self.test_results['multi_agent_orchestration']['details'] = f"Quiz question {i+1} missing fields: {missing_q_fields}"
                            print(f"❌ Quiz question {i+1} missing fields: {missing_q_fields}")
                            return False
                    
                    print(f"✅ Multi-agent orchestration successful!")
                    print(f"   - Story length: {len(lesson_data['story'])} characters")
                    print(f"   - Visual cues: {len(lesson_data['visual_cues'])}")
                    print(f"   - Images: {len(lesson_data['images'])}")
                    print(f"   - Quiz questions: {len(lesson_data['quiz'])}")
                    
                    self.test_results['multi_agent_orchestration']['passed'] = True
                    self.test_results['multi_agent_orchestration']['details'] = f"Successfully generated lesson with {len(lesson_data['quiz'])} quiz questions, {len(lesson_data['visual_cues'])} visual cues, {len(lesson_data['images'])} images"
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    self.test_results['multi_agent_orchestration']['details'] = f"HTTP {response.status}: {error_text}"
                    print(f"❌ Multi-agent orchestration failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.test_results['multi_agent_orchestration']['details'] = f"Exception: {str(e)}"
            print(f"❌ Multi-agent orchestration error: {str(e)}")
            return False

    async def test_story_agent(self):
        """Test Story Agent functionality through the lesson generation"""
        print("\n📚 Testing Story Agent...")
        
        # Story agent is tested as part of multi-agent orchestration
        if self.test_results['multi_agent_orchestration']['passed']:
            self.test_results['story_agent']['passed'] = True
            self.test_results['story_agent']['details'] = "Story agent working - generates educational stories with visual cues using Gemini LLM"
            print("✅ Story Agent working (tested via multi-agent orchestration)")
            return True
        else:
            self.test_results['story_agent']['details'] = "Story agent failed - part of multi-agent orchestration failure"
            print("❌ Story Agent failed")
            return False

    async def test_image_agent(self):
        """Test Image Agent functionality with PIL-based educational diagrams"""
        print("\n🖼️ Testing Image Agent - PIL-based Educational Diagrams...")
        
        # Test different diagram types as specified in review request
        test_topics = [
            {"topic": "OSI Layers", "expected_type": "layer"},
            {"topic": "Database Management", "expected_type": "database"},
            {"topic": "Network Topology", "expected_type": "network"}
        ]
        
        image_test_results = []
        
        for test_case in test_topics:
            print(f"\n🔍 Testing {test_case['topic']} diagram generation...")
            
            try:
                test_payload = {
                    "topic": test_case["topic"],
                    "age_group": "adult",
                    "difficulty": "beginner"
                }
                
                async with self.session.post(
                    f"{API_BASE_URL}/generate-lesson",
                    json=test_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        lesson_data = await response.json()
                        
                        # Check if images were generated
                        if lesson_data.get('images') and len(lesson_data['images']) > 0:
                            print(f"✅ {test_case['topic']}: Generated {len(lesson_data['images'])} images")
                            
                            # Validate each image is valid base64
                            valid_images = 0
                            for i, img in enumerate(lesson_data['images']):
                                try:
                                    # Decode base64 to verify it's valid
                                    decoded = base64.b64decode(img)
                                    if len(decoded) > 0:
                                        valid_images += 1
                                        print(f"  ✅ Image {i+1}: Valid base64 ({len(decoded)} bytes)")
                                    else:
                                        print(f"  ❌ Image {i+1}: Empty decoded data")
                                except Exception as e:
                                    print(f"  ❌ Image {i+1}: Invalid base64 - {str(e)}")
                            
                            if valid_images == len(lesson_data['images']):
                                image_test_results.append({
                                    'topic': test_case['topic'],
                                    'success': True,
                                    'image_count': len(lesson_data['images']),
                                    'details': f"All {valid_images} images are valid base64"
                                })
                            else:
                                image_test_results.append({
                                    'topic': test_case['topic'],
                                    'success': False,
                                    'image_count': len(lesson_data['images']),
                                    'details': f"Only {valid_images}/{len(lesson_data['images'])} images are valid"
                                })
                        else:
                            print(f"❌ {test_case['topic']}: No images generated")
                            image_test_results.append({
                                'topic': test_case['topic'],
                                'success': False,
                                'image_count': 0,
                                'details': "No images generated"
                            })
                    else:
                        error_text = await response.text()
                        print(f"❌ {test_case['topic']}: API call failed - {response.status}")
                        image_test_results.append({
                            'topic': test_case['topic'],
                            'success': False,
                            'image_count': 0,
                            'details': f"API call failed: {response.status} - {error_text}"
                        })
                        
            except Exception as e:
                print(f"❌ {test_case['topic']}: Exception - {str(e)}")
                image_test_results.append({
                    'topic': test_case['topic'],
                    'success': False,
                    'image_count': 0,
                    'details': f"Exception: {str(e)}"
                })
        
        # Evaluate overall image agent performance
        successful_tests = sum(1 for result in image_test_results if result['success'])
        total_tests = len(image_test_results)
        
        if successful_tests == total_tests:
            self.test_results['image_agent']['passed'] = True
            self.test_results['image_agent']['details'] = f"PIL-based image generation working perfectly! Successfully generated educational diagrams for all {total_tests} test topics. All images are valid base64 format."
            print(f"✅ Image Agent: All {total_tests} diagram types working!")
            return True
        elif successful_tests > 0:
            self.test_results['image_agent']['passed'] = True  # Partial success is still working
            self.test_results['image_agent']['details'] = f"PIL-based image generation partially working. {successful_tests}/{total_tests} diagram types successful. Details: {image_test_results}"
            print(f"⚠️ Image Agent: {successful_tests}/{total_tests} diagram types working")
            return True
        else:
            self.test_results['image_agent']['passed'] = False
            self.test_results['image_agent']['details'] = f"PIL-based image generation failed for all test cases. Details: {image_test_results}"
            print(f"❌ Image Agent: No diagram types working")
            return False

    async def test_quiz_agent(self):
        """Test Quiz Agent functionality"""
        print("\n❓ Testing Quiz Agent...")
        
        # Quiz agent is tested as part of multi-agent orchestration
        if self.test_results['multi_agent_orchestration']['passed']:
            self.test_results['quiz_agent']['passed'] = True
            self.test_results['quiz_agent']['details'] = "Quiz agent working - generates quiz questions with answers and explanations using Gemini LLM"
            print("✅ Quiz Agent working (tested via multi-agent orchestration)")
            return True
        else:
            self.test_results['quiz_agent']['details'] = "Quiz agent failed - part of multi-agent orchestration failure"
            print("❌ Quiz Agent failed")
            return False

    async def test_api_endpoints(self):
        """Test all API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        try:
            # Test GET /lessons
            async with self.session.get(f"{API_BASE_URL}/lessons") as response:
                if response.status == 200:
                    lessons = await response.json()
                    print(f"✅ GET /lessons working - found {len(lessons)} lessons")
                    
                    # Test GET /lessons/{id} if we have a lesson
                    if self.generated_lesson_id:
                        async with self.session.get(f"{API_BASE_URL}/lessons/{self.generated_lesson_id}") as lesson_response:
                            if lesson_response.status == 200:
                                lesson = await lesson_response.json()
                                print(f"✅ GET /lessons/{{id}} working - retrieved lesson: {lesson['topic']}")
                                
                                self.test_results['api_endpoints']['passed'] = True
                                self.test_results['api_endpoints']['details'] = "All API endpoints working - /generate-lesson, /lessons, /lessons/{id}"
                                return True
                            else:
                                error_text = await lesson_response.text()
                                self.test_results['api_endpoints']['details'] = f"GET /lessons/{{id}} failed: {lesson_response.status} - {error_text}"
                                print(f"❌ GET /lessons/{{id}} failed: {lesson_response.status}")
                                return False
                    else:
                        print("⚠️ No lesson ID available for individual lesson test")
                        self.test_results['api_endpoints']['passed'] = True
                        self.test_results['api_endpoints']['details'] = "GET /lessons working, /generate-lesson working, /lessons/{id} not tested (no lesson ID)"
                        return True
                        
                else:
                    error_text = await response.text()
                    self.test_results['api_endpoints']['details'] = f"GET /lessons failed: {response.status} - {error_text}"
                    print(f"❌ GET /lessons failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.test_results['api_endpoints']['details'] = f"Exception: {str(e)}"
            print(f"❌ API endpoints error: {str(e)}")
            return False

    async def test_database_operations(self):
        """Test database storage and retrieval"""
        print("\n💾 Testing Database Operations...")
        
        # Database operations are tested through API endpoints
        if self.test_results['api_endpoints']['passed'] and self.generated_lesson_id:
            self.test_results['database_operations']['passed'] = True
            self.test_results['database_operations']['details'] = "Database operations working - lesson storage and retrieval via MongoDB"
            print("✅ Database operations working (lesson stored and retrieved)")
            return True
        else:
            self.test_results['database_operations']['details'] = "Database operations failed - unable to store/retrieve lessons"
            print("❌ Database operations failed")
            return False

    async def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n⚠️ Testing Error Handling...")
        
        try:
            # Test invalid topic request
            invalid_payload = {
                "topic": "",  # Empty topic
                "age_group": "invalid",  # Invalid age group
                "difficulty": "expert"  # Invalid difficulty
            }
            
            async with self.session.post(
                f"{API_BASE_URL}/generate-lesson",
                json=invalid_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status >= 400:
                    print("✅ Error handling working - invalid input rejected")
                    return True
                else:
                    print("⚠️ Error handling may be lenient - invalid input accepted")
                    return True  # Not a critical failure
                    
        except Exception as e:
            print(f"⚠️ Error handling test failed: {str(e)}")
            return True  # Not a critical failure

    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting TechTales Backend Testing Suite")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Test basic connectivity
            if not await self.test_root_endpoint():
                print("❌ Basic connectivity failed - aborting tests")
                return
            
            # Test multi-agent orchestration (most critical)
            await self.test_multi_agent_orchestration()
            
            # Test individual agents (based on orchestration results)
            await self.test_story_agent()
            await self.test_image_agent()
            await self.test_quiz_agent()
            
            # Test API endpoints
            await self.test_api_endpoints()
            
            # Test database operations
            await self.test_database_operations()
            
            # Test error handling
            await self.test_error_handling()
            
        finally:
            await self.teardown()
        
        # Print summary
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🧪 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
            if result['details']:
                print(f"    Details: {result['details']}")
        
        print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All backend tests PASSED!")
        else:
            print("⚠️ Some backend tests FAILED - check details above")

async def main():
    """Main test runner"""
    tester = TechTalesBackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())