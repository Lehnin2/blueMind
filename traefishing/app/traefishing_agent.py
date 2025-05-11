import requests
import json
import re
import time
from typing import Dict, List, Any, Optional
import folium
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
import math

# Assuming maritime_navigation.py contains the navigation functions


# Set up logging
logging.basicConfig(filename="agent.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Location dictionary for city names
KNOWN_LOCATIONS = {
    "sousse": {"lat": 35.8272, "lon": 10.6356},
    "kelibia": {"lat": 36.8444, "lon": 11.0889},
    "sfax": {"lat": 34.7272, "lon": 10.7603},
    "jendouba": {"lat": 36.9558, "lon": 8.7339},
    "tunis": {"lat": 36.8333, "lon": 10.3167}
}

# Session context to store memory
SESSION_CONTEXT = {
    "current_location": None,  # {"lat": float, "lon": float}
    "recent_locations": [],    # List of {"lat": float, "lon": float}
    "recent_ports": [],       # List of {"name": str, "governorate": str, "lat": float, "lon": float}
    "last_tool_results": {},  # Tool results
    "user_preferences": {"offshore_distance_km": 5.0}  # User settings
}

# Tool registry
TOOL_REGISTRY = {
    "get_current_location": {
        "function": get_current_location,
        "description": "Retrieves the vessel's current location and generates a map.",
        "parameters": {}
    },
    "get_depth_at_location": {
        "function": get_depth_at_location,
        "description": "Estimates water depth at a given latitude and longitude.",
        "parameters": {
            "lat": {"type": "float", "description": "Latitude (-90 to 90)"},
            "lon": {"type": "float", "description": "Longitude (-180 to 180)"}
        }
    },
    "create_route_map": {
        "function": create_route_map,
        "description": "Plans a maritime route between two points and generates a map.",
        "parameters": {
            "start_lat": {"type": "float", "description": "Starting latitude"},
            "start_lon": {"type": "float", "description": "Starting longitude"},
            "end_lat": {"type": "float", "description": "Destination latitude"},
            "end_lon": {"type": "float", "description": "Destination longitude"}
        }
    },
    "get_ports_map": {
        "function": get_ports_map,
        "description": "Creates a map of Tunisian ports, optionally filtered by governorate.",
        "parameters": {
            "governorate": {"type": "string", "description": "Governorate name (optional)", "optional": True}
        }
    },
    "get_ports_by_governorate": {
        "function": get_ports_by_governorate,
        "description": "Lists ports in a specific governorate.",
        "parameters": {
            "governorate": {"type": "string", "description": "Governorate name"}
        }
    },
    "find_nearest_port": {
        "function": find_nearest_port,
        "description": "Finds the nearest port to a given location, optionally filtered by governorate.",
        "parameters": {
            "lat": {"type": "float", "description": "Latitude"},
            "lon": {"type": "float", "description": "Longitude"},
            "governorate": {"type": "string", "description": "Governorate name (optional)", "optional": True}
        }
    },
    "estimate_coordinates": {
        "function": lambda **kwargs: estimate_coordinates(**kwargs),
        "description": "Estimates coordinates based on distance and bearing from a given point.",
        "parameters": {
            "lat": {"type": "float", "description": "Starting latitude"},
            "lon": {"type": "float", "description": "Starting longitude"},
            "distance_km": {"type": "float", "description": "Distance in kilometers"},
            "bearing_deg": {"type": "float", "description": "Bearing in degrees (0=north, 90=east)"}
        }
    }
}

# API configuration
API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "Bearer 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"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": API_KEY
}

def estimate_coordinates(lat: float, lon: float, distance_km: float, bearing_deg: float) -> Dict:
    """Calculate coordinates at a given distance and bearing from a point."""
    R = 6371  # Earth's radius in km
    bearing_rad = math.radians(bearing_deg)
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    distance_ratio = distance_km / R

    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_ratio) +
        math.cos(lat_rad) * math.sin(distance_ratio) * math.cos(bearing_rad)
    )
    new_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_ratio) * math.cos(lat_rad),
        math.cos(distance_ratio) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )

    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)
    SESSION_CONTEXT["recent_locations"].append({"lat": new_lat, "lon": new_lon})
    return {"lat": new_lat, "lon": new_lon}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, json.JSONDecodeError))
)
def call_language_model(prompt: str) -> Optional[Dict]:
    """Call the Grok API to process a prompt."""
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": prompt}]
    }
    start_time = time.time()
    try:
        response = requests.post(API_URL, headers=HEADERS, data=json.dumps(payload), timeout=10)
        elapsed_time = time.time() - start_time
        logging.info(f"API Response Time: {elapsed_time:.2f} seconds")
        logging.info(f"Raw API Response: {response.text}")
        print(f"API Response Time: {elapsed_time:.2f} seconds")
        print(f"Raw API Response: {response.text}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            logging.info(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        elapsed_time = time.time() - start_time
        print(f"API Request Failed after {elapsed_time:.2f} seconds: {str(e)}")
        logging.info(f"API Request Failed after {elapsed_time:.2f} seconds: {str(e)}")
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"Unexpected Error after {elapsed_time:.2f} seconds: {str(e)}")
        logging.info(f"Unexpected Error after {elapsed_time:.2f} seconds: {str(e)}")
        raise

def parse_tool_and_parameters(prompt: str) -> List[Dict]:
    """Use Grok to identify tools and parameters."""
    system_prompt = f"""
You are an advanced assistant that analyzes a user prompt in any language to determine the appropriate tool(s) to call and their parameters. Your goal is to understand the intent, select tools, and extract or infer parameters, potentially chaining tools. Respond with a JSON array of objects wrapped in ```json\n...\n```, where each object contains:
- "tool": The name of the tool (or null if no tool matches).
- "parameters": A dictionary of parameter names and values (or empty). Numeric parameters (e.g., lat, lon) must be floats, not strings.
- "missing_parameters": A list of required but missing parameters.

Available tools:
{json.dumps({k: v["description"] for k, v in TOOL_REGISTRY.items()}, indent=2)}

Required parameters:
{json.dumps({k: {p: v["description"] for p, v in v["parameters"].items()} for k, v in TOOL_REGISTRY.items()}, indent=2)}

Known locations:
{json.dumps(KNOWN_LOCATIONS, indent=2)}

Recent context (use to infer parameters):
- Current location: {SESSION_CONTEXT["current_location"]}
- Recent locations: {SESSION_CONTEXT["recent_locations"][-3:]}
- Recent ports: {SESSION_CONTEXT["recent_ports"][-3:]}
- User preferences: {SESSION_CONTEXT["user_preferences"]}

Context:
- If the prompt refers to "my location," use get_current_location unless coordinates are provided.
- If a city name (e.g., Sfax) is mentioned, use its coordinates as floats.
- For prompts like "X km in the sea of [city]," use estimate_coordinates with inferred bearing (e.g., 90° east for "in the sea").
- If multiple steps are needed (e.g., depth at my location), chain tools in order.
- If parameters depend on prior tools, mark them as missing (e.g., "missing_parameters": ["lat", "lon"]).
- The prompt may be in any language. Analyze naturally.
- Use geospatial knowledge (e.g., Tunisia’s coast) to infer directions or distances.
- Suggest offshore coordinates (e.g., 5 km east) for land-based locations.

Prompt: {prompt}
"""
    response = call_language_model(system_prompt)
    if response and "choices" in response and response["choices"]:
        try:
            content = response["choices"][0]["message"]["content"]
            json_match = re.search(r"```json\n([\s\S]*?)\n```", content)
            if json_match:
                tool_sequence = json.loads(json_match.group(1))
                if isinstance(tool_sequence, dict):
                    tool_sequence = [tool_sequence]
                return tool_sequence
            else:
                print(f"Error: No JSON block found in response: {content}")
                logging.info(f"Error: No JSON block found in response: {content}")
                return []
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing API response: {str(e)}")
            logging.info(f"Error parsing API response: {str(e)}")
            return []
    print("No valid API response received.")
    logging.info("No valid API response received.")
    return []

def ask_for_missing_parameters(missing_parameters: List[str], tool_name: str) -> Dict:
    """Prompt user for missing parameters with validation."""
    params = {}
    for param in missing_parameters:
        param_info = TOOL_REGISTRY[tool_name]["parameters"][param]
        while True:
            value = input(f"Please provide {param} ({param_info['description']}): ")
            try:
                if param_info["type"] == "float":
                    val = float(value)
                    if param == "lat" and not (-90 <= val <= 90):
                        print("Latitude must be between -90 and 90.")
                        continue
                    if param == "lon" and not (-180 <= val <= 180):
                        print("Longitude must be between -180 and 180.")
                        continue
                    params[param] = val
                elif param_info["type"] == "string":
                    params[param] = value
                break
            except ValueError:
                print(f"Invalid input for {param}. Please try again.")
    return params

def execute_tool(tool_name: str, parameters: Dict) -> Any:
    """Execute tool, converting strings to floats."""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    parameters = parameters or {}
    processed_params = {}
    for param, value in parameters.items():
        param_info = tool["parameters"].get(param, {})
        if param_info.get("type") == "float" and isinstance(value, str):
            try:
                processed_params[param] = float(value)
            except ValueError:
                raise ValueError(f"Invalid numeric value for {param}: {value}")
        else:
            processed_params[param] = value
    
    required_params = [k for k, v in tool["parameters"].items() if not v.get("optional", False)]
    missing_params = [p for p in required_params if p not in processed_params]
    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
    
    try:
        result = tool["function"](**processed_params)
        if tool_name == "get_current_location":
            SESSION_CONTEXT["current_location"] = {"lat": result["lat"], "lon": result["lon"]}
            SESSION_CONTEXT["recent_locations"].append({"lat": result["lat"], "lon": result["lon"]})
        elif tool_name == "find_nearest_port":
            SESSION_CONTEXT["recent_ports"].append(result)
        SESSION_CONTEXT["last_tool_results"][tool_name] = result
        return result
    except Exception as e:
        raise RuntimeError(f"Error executing {tool_name}: {str(e)}")

def format_output(tool_name: str, result: Any, parameters: Dict = None) -> str:
    """Format tool output."""
    parameters = parameters or {}
    if tool_name == "get_current_location":
        return format_location_response(result)
    elif tool_name == "get_depth_at_location":
        output = format_depth_response(result)
        if result.get("depth") == 0.0 and "likely on land" in result.get("message", ""):
            default_distance = SESSION_CONTEXT["user_preferences"]["offshore_distance_km"]
            retry = input(f"Would you like to try different coordinates (e.g., {default_distance} km offshore)? (y/n): ")
            if retry.lower() == "y":
                print("Recent locations:", SESSION_CONTEXT["recent_locations"][-3:])
                use_default = input(f"Use default {default_distance} km east from current location? (y/n): ")
                if use_default.lower() == "y":
                    current = SESSION_CONTEXT["current_location"] or {"lat": 36.8333, "lon": 10.3167}
                    new_coords = estimate_coordinates(current["lat"], current["lon"], default_distance, 90)
                    new_params = {"lat": new_coords["lat"], "lon": new_coords["lon"]}
                else:
                    new_params = ask_for_missing_parameters(["lat", "lon"], tool_name)
                new_result = execute_tool(tool_name, new_params)
                return format_output(tool_name, new_result, new_params)
        return output
    elif tool_name == "create_route_map":
        map_obj, distance, waypoints = result
        map_obj.save("route_map.html")
        return f"{format_route_response(map_obj, distance, waypoints)}\nMap saved as route_map.html"
    elif tool_name == "get_ports_map":
        result.save("ports_map.html")
        return "Ports map generated and saved as ports_map.html"
    elif tool_name == "get_ports_by_governorate":
        return format_ports_response(result, parameters.get("governorate"))
    elif tool_name == "find_nearest_port":
        return f"Nearest port: {result['name']} ({result['governorate']}, {result['lat']:.4f}, {result['lon']:.4f})"
    elif tool_name == "estimate_coordinates":
        return f"Estimated coordinates: ({result['lat']:.4f}, {result['lon']:.4f})"
    return str(result)

def agent_process_prompt(prompt: str) -> str:
    """Process prompt and chain tools."""
    logging.info(f"Processing prompt: {prompt}")
    tool_sequence = parse_tool_and_parameters(prompt)
    
    if not tool_sequence or all(t["tool"] is None for t in tool_sequence):
        logging.info(f"Failed to determine tools for prompt: {prompt}")
        return "Sorry, I couldn't determine which tools to use."

    results = []
    for tool_info in tool_sequence:
        tool_name = tool_info["tool"]
        parameters = tool_info.get("parameters", {})
        missing_parameters = tool_info.get("missing_parameters", [])

        if missing_parameters:
            if tool_name == "get_depth_at_location" and "lat" in missing_parameters and "lon" in missing_parameters:
                if SESSION_CONTEXT["current_location"]:
                    parameters["lat"] = SESSION_CONTEXT["current_location"]["lat"]
                    parameters["lon"] = SESSION_CONTEXT["current_location"]["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["lat", "lon"]]
                elif "get_current_location" in SESSION_CONTEXT["last_tool_results"]:
                    location = SESSION_CONTEXT["last_tool_results"]["get_current_location"]
                    parameters["lat"] = location["lat"]
                    parameters["lon"] = location["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["lat", "lon"]]
            elif tool_name == "find_nearest_port" and "lat" in missing_parameters and "lon" in missing_parameters:
                if SESSION_CONTEXT["current_location"]:
                    parameters["lat"] = SESSION_CONTEXT["current_location"]["lat"]
                    parameters["lon"] = SESSION_CONTEXT["current_location"]["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["lat", "lon"]]
                elif "get_current_location" in SESSION_CONTEXT["last_tool_results"]:
                    location = SESSION_CONTEXT["last_tool_results"]["get_current_location"]
                    parameters["lat"] = location["lat"]
                    parameters["lon"] = location["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["lat", "lon"]]
            elif tool_name == "create_route_map" and any(p in missing_parameters for p in ["start_lat", "start_lon"]):
                if SESSION_CONTEXT["current_location"]:
                    parameters["start_lat"] = SESSION_CONTEXT["current_location"]["lat"]
                    parameters["start_lon"] = SESSION_CONTEXT["current_location"]["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["start_lat", "start_lon"]]
                elif "get_current_location" in SESSION_CONTEXT["last_tool_results"]:
                    location = SESSION_CONTEXT["last_tool_results"]["get_current_location"]
                    parameters["start_lat"] = location["lat"]
                    parameters["start_lon"] = location["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["start_lat", "start_lon"]]
            elif tool_name == "create_route_map" and any(p in missing_parameters for p in ["end_lat", "end_lon"]):
                if "find_nearest_port" in SESSION_CONTEXT["last_tool_results"]:
                    port = SESSION_CONTEXT["last_tool_results"]["find_nearest_port"]
                    parameters["end_lat"] = port["lat"]
                    parameters["end_lon"] = port["lon"]
                    missing_parameters = [p for p in missing_parameters if p not in ["end_lat", "end_lon"]]
            elif tool_name == "get_depth_at_location" and "find_nearest_port" in SESSION_CONTEXT["last_tool_results"]:
                port = SESSION_CONTEXT["last_tool_results"]["find_nearest_port"]
                parameters["lat"] = port["lat"]
                parameters["lon"] = port["lon"]
                missing_parameters = [p for p in missing_parameters if p not in ["lat", "lon"]]

        if missing_parameters:
            print(f"Missing parameters for {tool_name}: {', '.join(missing_parameters)}")
            additional_params = ask_for_missing_parameters(missing_parameters, tool_name)
            parameters.update(additional_params)

        try:
            result = execute_tool(tool_name, parameters)
            output = format_output(tool_name, result, parameters)
            results.append(output)
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logging.error(error_msg)
            return error_msg

    return "\n".join(results)

def main():
    """Interactive loop for continuous user input."""
    print("Welcome to the Maritime Navigation Agent! Type 'quit' to exit.")
    print("Available commands: get location, depth, route, ports, or estimate coordinates (e.g., '45 km in the sea of Sfax').")
    while True:
        if SESSION_CONTEXT["current_location"]:
            print(f"Current location: ({SESSION_CONTEXT['current_location']['lat']:.4f}, {SESSION_CONTEXT['current_location']['lon']:.4f})")
        if SESSION_CONTEXT["recent_ports"]:
            print(f"Recent port: {SESSION_CONTEXT['recent_ports'][-1]['name']} ({SESSION_CONTEXT['recent_ports'][-1]['lat']:.4f}, {SESSION_CONTEXT['recent_ports'][-1]['lon']:.4f})")
        prompt = input("\nEnter your prompt: ")
        if prompt.lower() == "quit":
            break
        print(f"\nPrompt: {prompt}")
        print(agent_process_prompt(prompt))

if __name__ == "__main__":
    main()
