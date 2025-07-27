from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime
import asyncio
import base64
import json

# Import emergent integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class TopicRequest(BaseModel):
    topic: str
    age_group: str = Field(..., description="child, teen, adult")
    difficulty: str = Field(..., description="beginner, intermediate, advanced")

class StoryResponse(BaseModel):
    story: str
    visual_cues: List[str]

class ImageResponse(BaseModel):
    images: List[str]  # Base64 encoded images

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]

class LessonResponse(BaseModel):
    id: str
    topic: str
    age_group: str
    difficulty: str
    story: str
    visual_cues: List[str]
    images: List[str]
    quiz: List[QuizQuestion]
    created_at: datetime

class LessonCreate(BaseModel):
    topic: str
    age_group: str
    difficulty: str
    story: str
    visual_cues: List[str]
    images: List[str]
    quiz: List[QuizQuestion]

# Multi-Agent System
class StoryAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate_story(self, topic: str, age_group: str, difficulty: str) -> StoryResponse:
        """Generate an educational story with visual cues"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"story_{uuid.uuid4()}",
                system_message=f"""You are an expert educational storyteller. Create engaging, analogy-rich stories that explain technical computer science concepts.

Your task is to create a story that:
1. Explains {topic} in a way suitable for {age_group} audience at {difficulty} level
2. Uses real-world analogies and metaphors
3. Includes specific visual cues for illustration
4. Is educational but entertaining
5. Breaks down complex concepts into digestible parts

Format your response as JSON with:
{{
  "story": "The complete story text with clear sections",
  "visual_cues": ["List of 3-5 specific visual elements to illustrate", "Each cue should be detailed enough for image generation"]
}}

Focus on making the story engaging and the visual cues very specific."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            user_message = UserMessage(
                text=f"Create an educational story about {topic} for {age_group} at {difficulty} level. Include specific visual cues for illustrations."
            )
            
            response = await chat.send_message(user_message)
            logger.info(f"Story response: {response}")
            
            # Parse the JSON response (handle markdown code blocks)
            try:
                # Clean the response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                clean_response = clean_response.strip()
                
                parsed_response = json.loads(clean_response)
                return StoryResponse(
                    story=parsed_response["story"],
                    visual_cues=parsed_response["visual_cues"]
                )
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return StoryResponse(
                    story=response,
                    visual_cues=[f"Illustration of {topic} concept", f"Diagram showing {topic} components", f"Visual metaphor for {topic}"]
                )
                
        except Exception as e:
            logger.error(f"Story generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

class ImageAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # Using a simpler, free image generation service
        self.hf_api_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    
    async def generate_images(self, visual_cues: List[str]) -> ImageResponse:
        """Generate images based on visual cues using alternative free method"""
        try:
            images = []
            
            # Alternative approach: Generate placeholder images with text
            # This ensures the UI works while we find a better free solution
            for i, cue in enumerate(visual_cues[:3]):
                try:
                    # Create a simple placeholder image using a web service
                    placeholder_image = await self.generate_placeholder_image(cue, i)
                    if placeholder_image:
                        images.append(placeholder_image)
                        logger.info(f"Generated placeholder image for cue: {cue}")
                        
                except Exception as e:
                    logger.error(f"Image generation error for cue '{cue}': {str(e)}")
                    continue
                    
            return ImageResponse(images=images)
            
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
    
    async def generate_placeholder_image(self, cue: str, index: int) -> str:
        """Generate a placeholder image using a free service"""
        try:
            import aiohttp
            
            # Using a free placeholder service that generates images with text
            # This is a working free alternative until we get proper image generation
            width, height = 512, 512
            
            # Create a URL for placeholder image with the cue text
            placeholder_url = f"https://via.placeholder.com/{width}x{height}/4A90E2/FFFFFF?text={cue.replace(' ', '+')}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(placeholder_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        # Convert to base64
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        return image_base64
                    else:
                        logger.error(f"Placeholder generation failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Placeholder generation error: {str(e)}")
            return None

class QuizAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate_quiz(self, topic: str, story: str, age_group: str, difficulty: str) -> QuizResponse:
        """Generate quiz questions based on the story and topic"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"quiz_{uuid.uuid4()}",
                system_message=f"""You are an expert educational quiz creator. Create engaging quiz questions that test understanding of the story and concept.

Your task is to create 3-5 quiz questions that:
1. Test comprehension of {topic} from the story
2. Are appropriate for {age_group} at {difficulty} level
3. Include multiple choice options
4. Have clear explanations for the correct answers
5. Cover different aspects of the concept

Format your response as JSON with:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Detailed explanation of why this is correct"
    }}
  ]
}}

Make questions engaging and educational."""
            ).with_model("gemini", "gemini-2.0-flash")
            
            user_message = UserMessage(
                text=f"Create quiz questions about {topic} based on this story: {story}. Target audience: {age_group} at {difficulty} level."
            )
            
            response = await chat.send_message(user_message)
            logger.info(f"Quiz response: {response}")
            
            # Parse the JSON response (handle markdown code blocks)
            try:
                # Clean the response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove ```
                clean_response = clean_response.strip()
                
                parsed_response = json.loads(clean_response)
                questions = []
                for q in parsed_response["questions"]:
                    questions.append(QuizQuestion(
                        question=q["question"],
                        options=q["options"],
                        correct_answer=q["correct_answer"],
                        explanation=q["explanation"]
                    ))
                return QuizResponse(questions=questions)
            except json.JSONDecodeError as e:
                # Fallback questions if JSON parsing fails
                return QuizResponse(questions=[
                    QuizQuestion(
                        question=f"What is the main concept explained in the story about {topic}?",
                        options=[f"{topic} basics", "Something else", "Not sure", "All of the above"],
                        correct_answer=f"{topic} basics",
                        explanation=f"The story explains the fundamental concepts of {topic}."
                    )
                ])
                
        except Exception as e:
            logger.error(f"Quiz generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

# Initialize agents
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

story_agent = StoryAgent(GEMINI_API_KEY)
image_agent = ImageAgent()  # Using free Hugging Face API (no auth required for public models)
quiz_agent = QuizAgent(GEMINI_API_KEY)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "TechTales AI Educational App"}

@api_router.post("/generate-lesson", response_model=LessonResponse)
async def generate_lesson(request: TopicRequest):
    """Generate a complete lesson with story, images, and quiz"""
    try:
        logger.info(f"Generating lesson for topic: {request.topic}")
        
        # Step 1: Generate story
        story_response = await story_agent.generate_story(
            request.topic, request.age_group, request.difficulty
        )
        
        # Step 2: Generate images
        image_response = await image_agent.generate_images(story_response.visual_cues)
        
        # Step 3: Generate quiz
        quiz_response = await quiz_agent.generate_quiz(
            request.topic, story_response.story, request.age_group, request.difficulty
        )
        
        # Create lesson object
        lesson_id = str(uuid.uuid4())
        lesson = LessonCreate(
            topic=request.topic,
            age_group=request.age_group,
            difficulty=request.difficulty,
            story=story_response.story,
            visual_cues=story_response.visual_cues,
            images=image_response.images,
            quiz=quiz_response.questions
        )
        
        # Save to database
        lesson_dict = lesson.dict()
        lesson_dict["id"] = lesson_id
        lesson_dict["created_at"] = datetime.utcnow()
        
        await db.lessons.insert_one(lesson_dict)
        
        return LessonResponse(
            id=lesson_id,
            topic=request.topic,
            age_group=request.age_group,
            difficulty=request.difficulty,
            story=story_response.story,
            visual_cues=story_response.visual_cues,
            images=image_response.images,
            quiz=quiz_response.questions,
            created_at=lesson_dict["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Lesson generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lesson generation failed: {str(e)}")

@api_router.get("/lessons", response_model=List[LessonResponse])
async def get_lessons():
    """Get all lessons"""
    try:
        lessons = await db.lessons.find().to_list(100)
        return [
            LessonResponse(
                id=lesson["id"],
                topic=lesson["topic"],
                age_group=lesson["age_group"],
                difficulty=lesson["difficulty"],
                story=lesson["story"],
                visual_cues=lesson["visual_cues"],
                images=lesson["images"],
                quiz=lesson["quiz"],
                created_at=lesson["created_at"]
            )
            for lesson in lessons
        ]
    except Exception as e:
        logger.error(f"Error fetching lessons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch lessons: {str(e)}")

@api_router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: str):
    """Get a specific lesson"""
    try:
        lesson = await db.lessons.find_one({"id": lesson_id})
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        return LessonResponse(
            id=lesson["id"],
            topic=lesson["topic"],
            age_group=lesson["age_group"],
            difficulty=lesson["difficulty"],
            story=lesson["story"],
            visual_cues=lesson["visual_cues"],
            images=lesson["images"],
            quiz=lesson["quiz"],
            created_at=lesson["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lesson: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch lesson: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()