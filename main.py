from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq
import json
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This means "Allow any website to talk to me"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STEP 2: CONFIGURATION ---
SUPABASE_URL = "https://ynvckmdojbckhcnbwbdc.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Turn on the connections
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


# --- STEP 3: THE SECURITY GUARD ---
class UserProfile(BaseModel):
    user_name: str
    fitness_level: str
    equipment_available: str
    injuries: str


# --- STEP 4 & 5: THE DRIVE-THRU WINDOW ---
# --- STEP 4 & 5: THE DRIVE-THRU WINDOW ---
@app.post("/generate-workout/")
async def generate_workout(profile: UserProfile):
    
    prompt = f"""
    You are an expert personal trainer. Create a 4-week workout plan for a user with the following profile:
    - Fitness Level: {profile.fitness_level}
    - Available Equipment: {profile.equipment_available}
    - Injuries/Limitations: {profile.injuries}
    
    Return ONLY a valid JSON object. Keep the exercise descriptions very brief and concise. Do not use markdown formatting or explain anything. The JSON must have exactly four keys: 'week_1', 'week_2', 'week_3', and 'week_4', each containing a list of daily workouts.
    """

    try:
        # 2. Call the AI (Added max_tokens to prevent the "Unterminated String" error)
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", 
            max_tokens=3000, 
            temperature=0.5
        )
        
        # Clean up the AI text so it's perfect JSON
        ai_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        workout_json = json.loads(ai_text)
        
        # 3. Save it to the Filing Cabinet (Supabase)
        db_data = {
            "user_name": profile.user_name,
            "fitness_level": profile.fitness_level,
            "equipment_available": profile.equipment_available,
            "injuries": profile.injuries,
            "generated_plan": workout_json
        }
        
        db_response = supabase.table("workout_plans").insert(db_data).execute()
        
        # 4. Hand the order to the customer
        return {"message": "Workout generated successfully!", "data": db_response.data[0]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))