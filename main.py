from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq
import json

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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InludmNrbWRvamJja2hjbmJ3YmRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU4MDkzNjMsImV4cCI6MjA5MTM4NTM2M30.JHTlg-B8o9PsIeXFM3jHB0SP-pRlsld31xu2NOFgLLQ"
GROQ_API_KEY = "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"  # <-- Paste your new Groq key here!

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
@app.post("/generate-workout/")
async def generate_workout(profile: UserProfile):
    
    prompt = f"""
    You are an expert personal trainer. Create a 4-week workout plan for a user with the following profile:
    - Fitness Level: {profile.fitness_level}
    - Available Equipment: {profile.equipment_available}
    - Injuries/Limitations: {profile.injuries}
    
    Return ONLY a valid JSON object. Do not use markdown formatting or explain anything. The JSON must have exactly four keys: 'week_1', 'week_2', 'week_3', and 'week_4', each containing a list of daily workouts.
    """

    try:
        # 2. Call the AI (Now using Groq and Meta's Llama 3 model!)
        response = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant", 
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