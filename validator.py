import google.generativeai as genai
from PIL import Image
import io

class ImageValidator:
    def __init__(self):
        pass

    def validate_image(self, file_upload, yard_type, api_key):
        """
        Validates image using Google Gemini API for semantic understanding.
        Checks for:
        1. Realness (Not AI, Not Blurry)
        2. Content (Garden/Yard visible)
        3. Yard Type Mismatch (Front vs Back vs Side)
        4. Prohibited Objects (People, Cars, Pets, Interiors)
        """
        if not api_key:
            return {"valid": False, "error": "Google Gemini API Key is missing. Please enter it in the sidebar."}

        # Configure API
        genai.configure(api_key=api_key)

        def get_working_model():
            """
            Attempts to find a working model from preferred list or available list.
            """
            preferred_models = [
                "gemini-2.5-flash-lite",
                "gemini-2.0-flash", 
                "gemini-1.5-flash", 
                "gemini-flash-latest",
                "gemini-1.5-pro"
            ]
            
            # It's safer to list models once and pick the best match
            try:
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Check for preferred matches in available list
                for pref in preferred_models:
                    for avail in available_models:
                        if pref in avail: 
                            return avail
                
                # Fallback: any 'flash' model
                for avail in available_models:
                    if 'flash' in avail.lower():
                        return avail
                
                # Fallback: any 'pro' model
                for avail in available_models:
                    if 'pro' in avail.lower():
                        return avail
                        
                # Last resort: first available
                if available_models:
                    return available_models[0]
                    
            except Exception as e:
                return "gemini-1.5-flash"
            
            return "gemini-1.5-flash"

        # Load image
        image = Image.open(file_upload)
        
        # Construct Prompt
        prompt = f"""
        Analyze this image for a Home Garden validation system. 
        The user claims this is the: {yard_type}.

        Strictly evaluate the image against these rules:
        1. MUST be a real photo. REJECT if: AI-generated, screenshot, extremely blurry, too dark, or a document.
        2. MUST be an outdoor photo of a house/yard. REJECT if: Indoor (kitchen, bedroom), Public Park, Commercial Building.
        3. MUST match the claimed Yard Type ({yard_type}):
           - Front Yard: Must show front of house, main entrance, or driveway with lawn.
           - Back Yard: Must show rear of house, patio, or backyard lawn.
           - Side Yard: Must show narrow path between houses or side strip.
           - REJECT if the image clearly shows a different yard type (e.g. Back Yard uploaded as Front Yard).
        4. PROHIBITED content: REJECT if image contains prominent People, Cars, Pets (dogs/cats), or Text overlays.
        5. COMPOSITION: REJECT if it is just a close-up of a plant/flower with no context (must show land/area). REJECT if it is just a plain wall or fence with no garden/ground.

        Respond ONLY in valid JSON format:
        {{
            "valid": boolean,
            "reason": "Clear explanation of why it failed (max 1 sentence).",
            "suggestion": "Actionable advice on what to upload instead (e.g. 'Please take a photo from the street showing the whole house').",
            "score": integer (0-100 quality score)
        }}
        Output JSON only.
        """

        try:
            import time
            from google.api_core import exceptions
            
            # Smart Model Selection
            model_name = get_working_model()
            model = genai.GenerativeModel(model_name)
            
            # Retry logic for Rate Limits (429)
            max_retries = 3
            retry_delay = 2 # start with 2 seconds
            
            response = None
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    response = model.generate_content([prompt, image])
                    break # Success
                except exceptions.ResourceExhausted as e:
                    # 429 Error
                    last_error = e
                    if attempt < max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= 2 # Exponential backoff
                    else:
                        raise e # Re-raise after max retries
                except Exception as e:
                    # Other errors (e.g. 400, 500) - do not retry blindly
                     raise e
            
        except Exception as e:
             return {"valid": False, "error": f"AI Validation failed (Model: {model_name if 'model_name' in locals() else 'Unknown'}). Error: {str(e)}", "model_used": model_name if 'model_name' in locals() else 'Unknown'}

        
        try:
            # Simple parsing (Gemini usually returns markdown json)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            
            import json
            result = json.loads(text_response)

            
            if result.get("valid") is True:
                return {
                    "valid": True, 
                    "message": "OK", 
                    "score": result.get("score", 100), 
                    "model_used": model_name
                }
            else:
                return {
                    "valid": False, 
                    "error": result.get("reason", "Invalid image"), 
                    "suggestion": result.get("suggestion", "Please check the image requirements and try again."),
                    "score": result.get("score", 0), 
                    "model_used": model_name
                }

        except Exception as e:
            # Reset file pointer if needed, though Image.open usually handles it.
            file_upload.seek(0)
            return {"valid": False, "error": f"Validation failed: {str(e)}"}

