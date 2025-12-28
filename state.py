import operator
from typing import Annotated, TypedDict, Optional, Literal
from pydantic import BaseModel, Field

# --- Pydantic Schemas (For LLM Output Enforcement) ---


class QuestionGeneratorSchema(BaseModel):
    question_text: str = Field(description="The text of the trivia question")
    option_a: str = Field(description="Option A text")
    option_b: str = Field(description="Option B text")
    option_c: str = Field(description="Option C text")
    correct_answer: Literal["A", "B", "C"] = Field(description="The correct option key (A, B, or C)")

class DomainGeneratorSchema(BaseModel):
    A: str = Field(description="A distinct, interesting knowledge domain (e.g., 'Space Science')")
    B: str = Field(description="A second distinct domain")
    C: str = Field(description="A third distinct domain")
# --- Updated GameState (For LangGraph) ---

class GameState(TypedDict):
    domain: dict        # The 3 available topics {A: "Space", B: "...", ...}
    current_topic: str          # The SPECIFIC topic user chose (e.g., "Space") <--- NEW
    question: str               
    options: dict               # {"A": "...", "B": "...", "C": "..."}
    correct_answer: str         
    user_answer: Optional[str]  
    feedback: str               
    status: str
    asked_questions: Annotated[list[str], operator.add]