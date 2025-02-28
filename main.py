from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# OpenRouter API key
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Roast Levels
ROAST_LEVELS = {
    "mild": "Give a playful, funny roast in Nigerian Pidgin. Make it teasing but not too harsh.",
    "medium": "Roast the user HARD in Nigerian Pidgin. Be brutal, no pity, but still funny.",
    "savage": "Forget jokes. Drag this person mercilessly in Nigerian Pidgin. Be heartless, ruthless, and disrespectful. No mercy, no limits. Make them feel completely worthless."
}

# Request Model
class RoastRequest(BaseModel):
    user_input: str
    level: str = "medium"  # Default to medium

@app.post("/roast")
async def roast_user(request: RoastRequest):
    if request.level not in ROAST_LEVELS:
        return {"error": "Invalid roast level. Choose 'mild', 'medium', or 'savage'."}

    try:
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://yourwebsite.com",  # Change to your website
                "X-Title": "AI Pidgin Roaster",
            },
            model="google/gemini-2.0-pro-exp-02-05:free",
            messages=[
                {"role": "system", "content": ROAST_LEVELS[request.level]},
                {"role": "user", "content": request.user_input}
            ],
        )

        roast = response.choices[0].message.content
        return {"roast": roast}

    except Exception as e:
        return {"error": str(e)}
