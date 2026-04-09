from fastapi import FastAPI, HTTPException, status
import uvicorn
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine, text
from typing import List, Optional

app = FastAPI()

# MySQL connection
DATABASE_URL = "mysql+pymysql://root:Nag%401234@127.0.0.1:3306/feedback_db"

engine = create_engine(DATABASE_URL)

# Request Model
class Feedback(BaseModel):
    session: str = Field(..., min_length=1, max_length=100, description="Session name")
    instructor: str = Field(..., min_length=1, max_length=100, description="Instructor name")
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    feedback: str = Field(..., min_length=1, max_length=1000, description="Feedback comments")

    @field_validator("session", "instructor")
    @classmethod
    def remove_extra_spaces(cls, value: str) -> str:
        return value.strip()
    #session: str
    #instructor: str
    #rating: int
    #feedback: str

class FeedbackListResponse(BaseModel):
    feedbacks: List[Feedback]

@app.get("/")
async def read_root():
    return {"Hello": "World new after changes"}

@app.get("/test_db")
def test_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"status": "Database connected"}

# POST API - Submit Feedback
@app.post("/submit_feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: Feedback):

    query = """
    INSERT INTO feedbacks (session, instructor, rating, feedback)
    VALUES (:session, :instructor, :rating, :feedback)
    """
    try:
        with engine.connect() as connection:
            connection.execute(text(query), payload.model_dump())
            connection.commit()

        return {"message": "Feedback submitted successfully"}
    
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        ) from exc
    

@app.get("/get_feedbacks")
def get_feedback(instructor: Optional[str] = None):

    query = "SELECT session, instructor, rating, feedback FROM feedbacks"

    params = {}

    # Dynamically add filter
    if instructor:
        query += " WHERE instructor = :instructor"
        params["instructor"] = instructor

    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params)
            feedback_list = []

            for row in result:
                feedback_list.append({
                    "session": row.session,
                    "instructor": row.instructor,
                    "rating": row.rating,
                    "feedback": row.feedback
                })
        return {"feedbacks": feedback_list}
    
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch feedback data"
        ) from exc

