from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv
import random
import json

# Initialize FastAPI app
app = FastAPI()

# Serve static files (CSS, JS, images)
#app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2 for HTML templates
templates = Jinja2Templates(directory="templates")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# Configure logging
logging.basicConfig(filename="roast_logs.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# Serve Frontend
@app.get("/")
async def serve_frontend(request: Request):
    """Render the frontend index.html."""
    return templates.TemplateResponse("index.html", {"request": request})

# **Savage Roast Levels**
ROAST_LEVELS = {
    "mild": "Give a playful, funny roast in Nigerian Pidgin. Make it teasing but not too harsh.",
    "medium": "Roast the user HARD in Nigerian Pidgin. Be brutal, no pity, but still funny.",
    "savage": "Forget jokes. Drag this person mercilessly in Nigerian Pidgin. Be heartless, ruthless, and disrespectful. No mercy, no limits. Make them feel completely worthless."
}

# **Dynamic Gender-Based Roast Variations**
MALE_ROASTS = [
    "Make him feel like his haircut was done by a blind barber.",
    "Roast him for acting rich but still borrowing money for data.",
    "Expose his fake deep quotes on WhatsApp that don't match his life.",
    "Destroy his 'gym bro' energy when his chest still looks like a whiteboard.",
    "Drag him for chasing women like a stray dog but getting ignored like a missed call."
]

FEMALE_ROASTS = [
    "Make her realize her Snapchat filters are the only reason she gets compliments.",
    "Drag her fashion sense for looking like a lost TikTok influencer.",
    "Roast her for posting 'men are trash' but still crying over one broke guy.",
    "Destroy her 'boss babe' attitude when she still begs for transport fare.",
    "Make her question why her toxic energy has scared away all her real friends."
]

# WebSocket connection manager
class ConnectionManager:
    """Handles multiple WebSocket connections for real-time roasting."""
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket connection."""
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket client."""
        await websocket.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/roast")
async def roast_websocket(websocket: WebSocket):
    """Handles WebSocket connections for live roasting."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive JSON message from client
            data = await websocket.receive_text()
            data = json.loads(data)

            # Extract message details
            message = data.get("message", "").strip()
            level = data.get("level", "medium")
            gender = data.get("gender", "male")

            if not message:
                await manager.send_personal_message("Error: Empty message received.", websocket)
                continue
            
            if level not in ROAST_LEVELS:
                await manager.send_personal_message("Error: Invalid roast level.", websocket)
                continue

            if gender not in ["male", "female"]:
                await manager.send_personal_message("Error: Invalid gender.", websocket)
                continue
            
            # Select roast style
            roast_instruction = ROAST_LEVELS[level]

            # Pick a **randomized** gender-specific roast instruction
            gender_instruction = random.choice(MALE_ROASTS if gender == "male" else FEMALE_ROASTS)

            # Generate roast using OpenAI
            try:
                response = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "https://yourwebsite.com",  # Replace with actual site
                        "X-Title": "HeartlessRoastBot",
                    },
                    model="google/gemini-2.0-flash-lite-preview-02-05:free",
                    messages=[
                        {"role": "system", "content": roast_instruction + " " + gender_instruction},
                        {"role": "user", "content": message},
                    ]
                )
                roast_response = response.choices[0].message.content.strip()

                # Log roast
                logging.info(f"User: {message} | Level: {level} | Gender: {gender} | Roast: {roast_response}")

                # Send the roast back to the user via WebSocket
                await manager.send_personal_message(json.dumps({"roast": roast_response}), websocket)

            except Exception as e:
                logging.error(f"Error: {str(e)}")
                await manager.send_personal_message(json.dumps({"error": "Wahala dey! Try again later."}), websocket)
    
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
