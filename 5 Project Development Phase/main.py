import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from google import genai
from google.genai import types

from pydantic import BaseModel, Field


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR = BASE_DIR / "static"


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0"
)


# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


# ---------------------------------------------------------
# JINJA2 TEMPLATES
# ---------------------------------------------------------

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)


# ---------------------------------------------------------
# GEMINI CONFIGURATION
# ---------------------------------------------------------

API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()


MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
).strip()
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"



client = None


if API_KEY:

    client = genai.Client(
        api_key=API_KEY
    )


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------

class AskRequest(BaseModel):

    question: str = Field(
        ...,
        min_length=1,
        max_length=6000
    )


class TextRequest(BaseModel):

    text: str = Field(
        ...,
        min_length=1,
        max_length=12000
    )


class QuizRequest(BaseModel):

    topic: str = Field(
        ...,
        min_length=1,
        max_length=3000
    )

    number_of_questions: int = Field(
        default=5,
        ge=3,
        le=10
    )


class LearningPathRequest(BaseModel):

    topic: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )

    level: str = Field(
        default="Beginner",
        max_length=50
    )

    weeks: int = Field(
        default=6,
        ge=1,
        le=16
    )


# ---------------------------------------------------------
# QUIZ RESPONSE MODELS
# ---------------------------------------------------------

class QuizQuestion(BaseModel):

    question: str

    options: list[str] = Field(
        min_length=4,
        max_length=4
    )

    answer: str

    explanation: str


class QuizResponse(BaseModel):

    title: str

    questions: list[QuizQuestion]


# ---------------------------------------------------------
# LEARNING PATH MODELS
# ---------------------------------------------------------

class LearningWeek(BaseModel):

    week: int

    title: str

    topics: list[str]

    practice: list[str]

    goal: str


class LearningPathResponse(BaseModel):

    title: str

    overview: str

    weeks: list[LearningWeek]


# ---------------------------------------------------------
# CHECK GEMINI CONFIGURATION
# ---------------------------------------------------------

def require_ai():

    if client is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Gemini API key is not configured. "
                "Please add GEMINI_API_KEY to your .env file."
            )
        )

    return client

def demo_text_response(prompt: str) -> str:
    return """
Artificial Intelligence (AI) is a branch of computer science that enables
machines to perform tasks that normally require human intelligence.

Examples of AI include:
- Chatbots
- Image recognition
- Speech recognition
- Recommendation systems
- Self-driving technology

AI systems can learn from data, identify patterns, understand information,
and help solve problems.

In simple words, AI makes computers perform tasks in a smart way.
""".strip()
    if "python" in prompt_lower:
        return """
Python is a high-level, easy-to-learn programming language.

It is commonly used for:
- Web development
- Data science
- Artificial Intelligence
- Automation
- Machine learning

Python is popular because its syntax is simple and readable.
""".strip()

    if "object oriented programming" in prompt_lower:
        return """
Object-Oriented Programming (OOP) is a programming approach based on objects
and classes.

The main concepts are:
- Class
- Object
- Encapsulation
- Inheritance
- Polymorphism
- Abstraction

OOP helps organize programs and makes code easier to reuse and maintain.
""".strip()

    return """
EduGenie Demo Mode

This is a sample educational answer because the Gemini API quota is
currently unavailable.

Please try a topic such as Artificial Intelligence, Python, or
Object-Oriented Programming.
""".strip()
# ---------------------------------------------------------
# GENERATE NORMAL TEXT
# ----------------------------------------------------------
def generate_text(
    prompt: str,
    system_instruction: str,
    temperature: float = 0.4
):
    if DEMO_MODE:
        return demo_text_response(prompt)

    ai = require_ai()

    last_error = None

    for attempt in range(3):
        try:
            response = ai.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=1800
                )
            )

            text = getattr(
                response,
                "text",
                None
            )

            if not text:
                raise HTTPException(
                    status_code=502,
                    detail="Gemini returned an empty response."
                )

            return text.strip()

        except HTTPException:
            raise

        except Exception as exc:
            last_error = exc

            error_text = str(exc)

            if "503" in error_text or "UNAVAILABLE" in error_text:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue

            raise HTTPException(
                status_code=502,
                detail=f"Gemini request failed: {exc}"
            ) from exc

    raise HTTPException(
        status_code=502,
        detail=f"Gemini request failed: {last_error}"
    )

# ---------------------------------------------------------
# GENERATE STRUCTURED JSON
# ---------------------------------------------------------

def generate_json(
    prompt: str,
    system_instruction: str,
    schema,
    temperature: float = 0.3
):
    ai = require_ai()

    last_error = None

    for attempt in range(3):
        try:
            response = ai.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=temperature,
                    max_output_tokens=4000
                )
            )

            parsed = getattr(
                response,
                "parsed",
                None
            )

            if parsed is not None:
                return parsed

            raw = getattr(
                response,
                "text",
                ""
            )

            if not raw:
                raise HTTPException(
                    status_code=502,
                    detail="Gemini returned an empty JSON response."
                )

            return json.loads(raw)

        except HTTPException:
            raise

        except Exception as exc:
            last_error = exc

            error_text = str(exc)

            if "503" in error_text or "UNAVAILABLE" in error_text:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue

            raise HTTPException(
                status_code=502,
                detail=f"Gemini structured request failed: {exc}"
            ) from exc

    raise HTTPException(
        status_code=502,
        detail=f"Gemini structured request failed: {last_error}"
    )

    ai = require_ai()

    try:

        response = ai.models.generate_content(

            model=MODEL_NAME,

            contents=prompt,

            config=types.GenerateContentConfig(

                system_instruction=system_instruction,

                response_mime_type="application/json",

                response_schema=schema,

                temperature=temperature,

                max_output_tokens=4000
            )
        )

        parsed = getattr(
            response,
            "parsed",
            None
        )

        if parsed is not None:

            return parsed

        raw = getattr(
            response,
            "text",
            ""
        )

        return json.loads(raw)

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Gemini structured request failed: {exc}"
        ) from exc


# =========================================================
# HOME PAGE
# =========================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(

        request=request,

        name="index.html",

        context={
            "model_name": MODEL_NAME
        }
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():

    return {

        "status": "ok",

        "gemini_configured": bool(API_KEY),

        "model": MODEL_NAME
    }


# =========================================================
# ASK QUESTION
# =========================================================

@app.post("/api/ask")
async def ask(request: AskRequest):

    answer = generate_text(

        prompt=f"""
Student question:

{request.question}
""",

        system_instruction="""
You are EduGenie, a friendly educational AI assistant.

Answer the student's question accurately and clearly.

Rules:

1. Use simple language.
2. Explain difficult concepts step-by-step.
3. Use examples when useful.
4. Use headings or bullet points when helpful.
5. Avoid unnecessary technical jargon.
6. Do not invent facts.
7. If the question is ambiguous, clearly state your assumption.
""",

        temperature=0.35
    )

    return {
        "answer": answer
    }


# =========================================================
# EXPLAIN CONCEPT
# =========================================================

@app.post("/api/explain")
async def explain(request: TextRequest):

    if DEMO_MODE:
        return {
            "answer": f"""
Simple Meaning:

{request.text}

Easy Explanation:

This concept means understanding the basic idea clearly and
applying it with a simple example.

Example:

If you are learning this topic for the first time, first understand
the definition, then learn how it works, and finally practice it.

Important Points:

- Understand the basic meaning.
- Learn how it works.
- Practice with examples.
- Revise the important points.
""".strip()
        }

    answer = generate_text(
        prompt=f"""
Concept to explain:

{request.text}
""",
        system_instruction="""
You are EduGenie.

Explain the given educational concept to a beginner student.

Use this structure:

1. Simple meaning
2. Easy explanation
3. Small example
4. Important points

Use simple student-friendly English.
""",
        temperature=0.35
    )

    return {
        "answer": answer
    }
 


# =========================================================
# SUMMARIZE TEXT
# =========================================================

@app.post("/api/summarize")
async def summarize(request: TextRequest):

    if DEMO_MODE:
        text = request.text.strip()

        return {
            "answer": f"""
Summary:

{text}

Key Points:

- The text explains the main topic.
- It contains important information about the topic.
- The main idea should be understood clearly.
- Important details should be remembered.
- The topic can be revised using these points.

In Short:

The passage gives a simple explanation of the main topic and its important ideas.
""".strip()
        }

    answer = generate_text(
        prompt=f"""
Summarize the following text:

{request.text}
""",
        system_instruction="""
You are EduGenie.

Summarize the supplied educational text clearly and simply.

Give:
1. A short summary
2. Important key points
3. A short conclusion

Do not add information that is not present in the text.
""",
        temperature=0.25
    )

    return {
        "answer": answer
    }
# =========================================================
# GENERATE QUIZ
# =========================================================

@app.post(
    "/api/quiz",
    response_model=QuizResponse
)
async def quiz(request: QuizRequest):

    if DEMO_MODE:
        questions = []

        for i in range(request.number_of_questions):
            questions.append(
                {
                    "question": f"What is an important idea about {request.topic}?",
                    "options": [
                        f"Basic concept of {request.topic}",
                        "Cooking food",
                        "Playing games",
                        "Watching movies"
                    ],
                    "answer": f"Basic concept of {request.topic}",
                    "explanation": f"This answer is related to {request.topic}."
                }
            )

        return {
            "title": f"{request.topic} Quiz",
            "questions": questions
        }

    schema = QuizResponse.model_json_schema()

    result = generate_json(
        prompt=f"""
Create a multiple-choice quiz.

Topic:
{request.topic}

Number of questions:
{request.number_of_questions}

Create exactly {request.number_of_questions} questions.
Every question must have exactly four options.
Only one option should be correct.

JSON schema:
{schema}
""",
        system_instruction="""
You are EduGenie's quiz generator.

Create accurate and student-friendly questions.
""",
        schema=QuizResponse,
        temperature=0.45
    )

    return result
# =========================================================
# GENERATE LEARNING PATH
# =========================================================

@app.post(
    "/api/learning-path",
    response_model=LearningPathResponse
)
async def learning_path(request: LearningPathRequest):

    if DEMO_MODE:
        weeks = [
            {
                "week": 1,
                "title": f"{request.topic} Fundamentals",
                "topics": [
                    f"Introduction to {request.topic}",
                    f"Basic concepts of {request.topic}",
                    "Important terminology"
                ],
                "practice": [
                    f"Learn the basic concepts of {request.topic}",
                    "Write short notes on important terms",
                    "Practice simple beginner exercises"
                ],
                "goal": f"Understand the fundamentals of {request.topic}"
            },
            {
                "week": 2,
                "title": f"Core Concepts of {request.topic}",
                "topics": [
                    f"Core concepts of {request.topic}",
                    "Basic problem solving",
                    "Common examples"
                ],
                "practice": [
                    "Solve simple practice problems",
                    "Work through examples step by step",
                    "Revise the concepts learned in Week 1"
                ],
                "goal": f"Build a strong understanding of {request.topic}"
            },
            {
                "week": 3,
                "title": f"Practical {request.topic}",
                "topics": [
                    f"Practical use of {request.topic}",
                    "Hands-on exercises",
                    "Common mistakes and solutions"
                ],
                "practice": [
                    "Complete hands-on exercises",
                    "Create a small practice task",
                    "Identify and correct common mistakes"
                ],
                "goal": f"Apply {request.topic} through practical activities"
            },
            {
                "week": 4,
                "title": f"{request.topic} Mini Project",
                "topics": [
                    f"Applying {request.topic}",
                    "Mini project planning",
                    "Revision and improvement"
                ],
                "practice": [
                    f"Build a small project using {request.topic}",
                    "Test and improve the project",
                    "Review all important concepts"
                ],
                "goal": f"Complete a small project using {request.topic}"
            }
        ]

        weeks = weeks[:request.weeks]

        return {
            "title": f"{request.topic} Learning Path",
            "overview": (
                f"A {request.weeks}-week learning plan for "
                f"{request.topic} at {request.level} level."
            ),
            "weeks": weeks
        }

    schema = LearningPathResponse.model_json_schema()

    result = generate_json(
        prompt=f"""
Create a structured learning plan.

Topic:
{request.topic}

Student level:
{request.level}

Duration:
{request.weeks} weeks

Requirements:

- Create exactly {request.weeks} weeks.
- Start from the fundamentals.
- Progress gradually.
- Include topics.
- Include practical activities.
- Include a goal for every week.
- Make the plan realistic for a student.

JSON schema:
{schema}
""",
        system_instruction="""
You are EduGenie, an expert learning-plan designer.

Create realistic and practical study plans.

The plan should progress logically from basic concepts
to more advanced concepts.
""",
        schema=LearningPathResponse,
        temperature=0.5
    )

    return result