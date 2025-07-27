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
    
    async def generate_images(self, visual_cues: List[str]) -> ImageResponse:
        """Generate images based on visual cues using free image generation"""
        try:
            images = []
            
            # Generate educational diagram images
            for i, cue in enumerate(visual_cues[:3]):
                try:
                    # Create educational diagram image
                    image_base64 = await self.create_educational_diagram(cue, i)
                    if image_base64:
                        images.append(image_base64)
                        logger.info(f"Generated educational diagram for cue: {cue}")
                        
                except Exception as e:
                    logger.error(f"Image generation error for cue '{cue}': {str(e)}")
                    continue
                    
            return ImageResponse(images=images)
            
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
    
    async def create_educational_diagram(self, cue: str, index: int) -> str:
        """Create educational diagram using PIL"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create image
            width, height = 512, 384
            colors = [
                ('#4A90E2', '#FFFFFF'),  # Blue
                ('#5CB85C', '#FFFFFF'),  # Green  
                ('#F0AD4E', '#FFFFFF'),  # Orange
            ]
            
            bg_color, text_color = colors[index % len(colors)]
            
            # Create image
            img = Image.new('RGB', (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to default
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw title
            title = f"Educational Diagram {index + 1}"
            title_bbox = draw.textbbox((0, 0), title, font=font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, 30), title, fill=text_color, font=font)
            
            # Draw cue text (wrapped)
            words = cue.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_bbox = draw.textbbox((0, 0), test_line, font=font)
                test_width = test_bbox[2] - test_bbox[0]
                
                if test_width <= width - 40:  # 20px margin on each side
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw wrapped text
            y_offset = 80
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                draw.text((line_x, y_offset), line, fill=text_color, font=font)
                y_offset += 25
            
            # Draw simple diagram elements
            center_x, center_y = width // 2, height // 2 + 20
            
            # Draw some basic shapes for educational purposes
            if 'layer' in cue.lower() or 'osi' in cue.lower():
                # Draw layers
                for i in range(4):
                    y = center_y + (i * 30) - 60
                    draw.rectangle([center_x - 100, y, center_x + 100, y + 25], 
                                 outline=text_color, width=2)
                    draw.text((center_x - 90, y + 5), f"Layer {i+1}", fill=text_color, font=font)
                                 
            elif 'network' in cue.lower():
                # Draw network nodes
                for i in range(3):
                    x = center_x + (i - 1) * 80
                    draw.ellipse([x - 25, center_y - 25, x + 25, center_y + 25], 
                               outline=text_color, width=2)
                    draw.text((x - 10, center_y - 5), f"N{i+1}", fill=text_color, font=font)
                    
            elif 'data' in cue.lower() or 'database' in cue.lower():
                # Draw database cylinder
                draw.ellipse([center_x - 40, center_y - 60, center_x + 40, center_y - 40], 
                           outline=text_color, width=2)
                draw.rectangle([center_x - 40, center_y - 50, center_x + 40, center_y + 10], 
                             outline=text_color, width=2)
                draw.ellipse([center_x - 40, center_y, center_x + 40, center_y + 20], 
                           outline=text_color, width=2)
                           
            else:
                # Draw generic diagram
                draw.rectangle([center_x - 60, center_y - 40, center_x + 60, center_y + 40], 
                             outline=text_color, width=2)
                draw.text((center_x - 20, center_y - 5), "Concept", fill=text_color, font=font)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            logger.error(f"Educational diagram creation error: {str(e)}")
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