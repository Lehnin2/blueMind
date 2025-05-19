import asyncio
import json
import os
import re
from groq import Groq
from configz import settings
from maritime_watch import SerperSearch

async def get_fish_info(species_name: str, length_cm: float, weight_kg: float):
    """
    Get information about a fish species from Groq AI and estimated market price in Tunisia using Serper.
    
    Args:
        species_name: Name of the fish species
        length_cm: Measured length in centimeters
        weight_kg: Predicted weight in kilograms
        
    Returns:
        Dict containing average info, release recommendations, and estimated price in Tunisia
    """
    try:
        # Initialize SerperSearch for price only
        serper = SerperSearch(
            api_key=settings.SERPER_API_KEY,
            country="tn",
            locale="fr",
            location="Tunisia"
        )
        
        # Search only for fish price in Tunisia
        search_query = f"{species_name} fish price Tunisia"
        print(f"Searching for price: {search_query}")
        search_results = await serper.search(search_query)
        formatted_results = serper.format_results(search_results)
        print(f"Formatted price search results: {formatted_results}")
        
        # Initialize Groq client
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        # Prepare Groq prompt - now focusing on using existing knowledge plus price search
        prompt = f"""
        You are a fishing expert with knowledge about various fish species.

        Fish species: {species_name}
        Measured length: {length_cm} cm
        Measured weight: {weight_kg} kg
        
        Task 1: Use your existing knowledge to provide information about this fish species:
        1. Average length (cm) for adult {species_name}
        2. Average weight (kg) for adult {species_name}
        3. Minimum legal catch size (cm) if available
        4. Should this fish be released based on its length? (true/false)
        5. A brief comparison between the measured fish and the average for this species
        
        Task 2: Use ONLY the following search results to estimate the market price in Tunisia (TND):
        {formatted_results}
        
        Respond ONLY with valid JSON structure with these keys:
        - average_length_cm (float or null)
        - average_weight_kg (float or null)
        - minimum_legal_size_cm (float or null)
        - should_release (boolean)
        - comparison (string)
        - estimated_price_tnd_per_kg (float or null)
        """
        
        print(f"Sending Groq prompt for fish data and price estimation...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-70b-8192",
            stream=False,
        )
        
        response = chat_completion.choices[0].message.content
        print(f"Raw Groq response: {response}")
        
        # Extract JSON from response using regex patterns
        # Try multiple patterns to handle different response formats
        json_patterns = [
            r'```json\n([\s\S]*?)\n```',  # Standard markdown JSON code block
            r'```\n([\s\S]*?)\n```',      # Generic code block
            r'{[\s\S]*}',                 # Just find the JSON object
        ]
        
        json_str = None
        for pattern in json_patterns:
            match = re.search(pattern, response, re.MULTILINE)
            if match and '{' in match.group(0):
                # For the last pattern, we want the whole match
                json_str = match.group(1) if pattern != r'{[\s\S]*}' else match.group(0)
                # Clean up the string - remove any non-JSON content
                json_str = json_str.strip()
                try:
                    # Validate that this is actually parseable JSON
                    json.loads(json_str)
                    break  # We found valid JSON, stop trying patterns
                except json.JSONDecodeError:
                    json_str = None  # Reset and try next pattern
        
        # If we didn't find JSON with regex, try to extract it more aggressively
        if not json_str:
            # Look for anything that looks like JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx+1]
        
        # If we still don't have JSON, fall back to default values
        if not json_str:
            print("Failed to extract JSON from response")
            return {
                "error": "Failed to extract JSON from Groq response",
                "raw_response": response,
                "average_length_cm": None,
                "average_weight_kg": None,
                "minimum_legal_size_cm": None,
                "should_release": False,
                "comparison": "Could not retrieve comparison data.",
                "estimated_price_tnd_per_kg": None
            }
        
        try:
            fish_data = json.loads(json_str)
            # Validate required keys
            required_keys = [
                "average_length_cm",
                "average_weight_kg",
                "minimum_legal_size_cm",
                "should_release",
                "comparison",
                "estimated_price_tnd_per_kg"
            ]
            missing_keys = [key for key in required_keys if key not in fish_data]
            
            if missing_keys:
                print(f"Missing required keys in fish_data: {missing_keys}")
                # Add missing keys with default values
                for key in missing_keys:
                    if key == "should_release":
                        fish_data[key] = False
                    elif key == "comparison":
                        fish_data[key] = "Could not retrieve comparison data."
                    else:
                        fish_data[key] = None
            
            return fish_data
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return {
                "error": f"Failed to parse Groq response: {e}",
                "raw_response": response,
                "average_length_cm": None,
                "average_weight_kg": None,
                "minimum_legal_size_cm": None,
                "should_release": False,
                "comparison": "Could not retrieve comparison data.",
                "estimated_price_tnd_per_kg": None
            }
            
    except Exception as e:
        print(f"Error in get_fish_info: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to get fish information: {str(e)}",
            "average_length_cm": None,
            "average_weight_kg": None,
            "minimum_legal_size_cm": None,
            "should_release": False,
            "comparison": "Could not retrieve comparison data.",
            "estimated_price_tnd_per_kg": None
        }
