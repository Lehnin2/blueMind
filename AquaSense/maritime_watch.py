from dotenv import load_dotenv
from groq import Groq
import requests
import os
import json
import asyncio
import logging
from typing import Dict, Any, List
import re
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define search categories for user to choose from
SEARCH_CATEGORIES = {
    "1": "All maritime conditions",
    "2": "Fishing specific information",
    "3": "Diving specific information",
    "4": "Maritime safety information"
}

def get_categories():
    """Return the search categories"""
    return SEARCH_CATEGORIES

# Models configuration
DEFAULT_MODEL = "qwen-qwq-32b"  # Default model for most tasks
SUMMARY_MODEL = "qwen-qwq-32b"  # Model for summarization tasks

# System prompts for various specialized roles
WEATHER_PROMPT = """
You are a Tunisian marine weather specialist who analyzes sea conditions, temperatures, and forecasts.
Focus on recent data from the past 14 days. Be concise and factual when reporting conditions.

Create a markdown-formatted list of 3-5 bullet points covering key weather conditions:
- Current sea temperatures at major coastal areas
- Weather forecasts affecting maritime activities
- Waves, tides, and other relevant sea conditions
- Include source information

Research Task: {search_query}
"""

FISHING_PROMPT = """
You are a Tunisian fishing expert who tracks fish migrations and optimal fishing locations.
Focus on recent data from the past 14 days. Be concise and factual when reporting current fishing conditions.

Create a markdown-formatted list of 3-5 bullet points covering:
- Currently active fish species in Tunisian waters
- Prime fishing locations this week
- Recent catches reported
- Include source information

Research Task: {search_query}
"""

DIVING_PROMPT = """
You are a Tunisian diving specialist who monitors underwater visibility and diving conditions.
Focus on recent data from the past 14 days. Be concise and factual when reporting diving conditions.

Create a markdown-formatted list of 3-5 bullet points covering:
- Current underwater visibility at popular diving spots
- Special sightings or conditions underwater
- Recommended diving locations this week
- Include source information

Research Task: {search_query}
"""

SAFETY_PROMPT = """
You are a Tunisian maritime safety expert who monitors advisories and safety conditions.
Focus on recent data from the past 14 days. Be concise and factual when reporting safety warnings.

Create a markdown-formatted list of 3-5 bullet points covering:
- Current maritime safety advisories
- Areas to avoid or exercise caution
- Required safety protocols currently in effect
- Include source information

Research Task: {search_query}
"""

SYNTHESIS_PROMPT = """
You are a maritime activities specialist who synthesizes technical marine data into a single, actionable notification for fishers, divers, and maritime enthusiasts in Tunisia.
Based ONLY on the provided research findings below, create a concise, single-sentence notification (20-50 words) summarizing optimal fishing spots, diving visibility, safety considerations, or notable species.

--- BEGIN RESEARCH FINDINGS ---
{context}
--- END RESEARCH FINDINGS ---

Your final answer must be a single sentence suitable for a phone notification, with no additional content or formatting.
"""

# Search queries for each research task
SEARCH_QUERIES = {
    "weather": "Tunisia current sea temperature AND weather forecast AND marine conditions",
    "fishing": "Tunisia current fishing conditions AND fish migrations AND best fishing spots",
    "diving": "Tunisia diving visibility AND underwater conditions AND best diving spots",
    "safety": "Tunisia maritime safety alerts AND marine hazards AND current advisories"
}

class SerperSearch:
    """Simple search tool using Serper API without CrewAI dependencies"""
    
    def __init__(self, api_key, country="tn", locale="fr", location="Tunisia"):
        self.api_key = api_key
        self.country = country
        self.locale = locale
        self.location = location
        self.base_url = "https://serpapi.com/search"
        
    async def search(self, query):
        """Perform a search and return results"""
        # Fallback to public SerpAPI if Serper not available/configured
        try:
            return await self._search_with_serper(query)
        except Exception as e:
            print(f"Error with Serper API: {str(e)}")
            try:
                return await self._search_with_serp_api(query)
            except Exception as e2:
                print(f"Error with SerpAPI: {str(e2)}")
                return {"error": f"Search failed: {str(e2)}", "organic_results": []}
    
    async def _search_with_serper(self, query):
        """Search using Serper.dev API"""
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": query,
            "gl": self.country,
            "hl": self.locale,
            "location": self.location
        })
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Use aiohttp or similar for async requests in production
        # For simplicity, we'll use requests in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.request("POST", url, headers=headers, data=payload)
        )
        return response.json()
    
    async def _search_with_serp_api(self, query):
        """Fallback to SerpAPI if available"""
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "gl": self.country,
            "hl": self.locale,
            "location": self.location
        }
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(self.base_url, params=params)
        )
        return response.json()
        
    def format_results(self, results):
        """Format search results into a readable string"""
        if "error" in results:
            return f"Search Error: {results['error']}"
            
        formatted = "# Search Results\n\n"
        
        # Add organic results
        if "organic" in results:
            for i, result in enumerate(results["organic"][:5], 1):  # Limit to top 5
                title = result.get("title", "No Title")
                link = result.get("link", "#")
                snippet = result.get("snippet", "No description available.")
                formatted += f"## {i}. {title}\n"
                formatted += f"{snippet}\n"
                formatted += f"Source: {link}\n\n"
        
        # Add knowledge graph if available
        if "knowledgeGraph" in results:
            kg = results["knowledgeGraph"]
            if "title" in kg:
                formatted += f"## Knowledge Graph: {kg['title']}\n"
                if "description" in kg:
                    formatted += f"{kg['description']}\n\n"
                    
        # If no results found
        if "organic" not in results or len(results["organic"]) == 0:
            formatted += "No search results found.\n"
            
        return formatted

import re
import asyncio

async def call_groq(prompt, model=DEFAULT_MODEL):
    """Make an API call to Groq with the given prompt and filter out thinking process"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: groq_client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "system",
                        "content": prompt
                    }],
                    stream=False
                )
            )
            # Get the raw response content
            content = response.choices[0].message.content
            # Remove content between <think> and </think> tags
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            # If </think> exists, keep only content after the last </think>
            if '</think>' in content:
                content = content.split('</think>')[-1]
            return content.strip()  # Strip any extra whitespace
        except Exception as e:
            retry_count += 1
            print(f"Error calling Groq API (attempt {retry_count}/{max_retries}): {str(e)}")
            if "rate_limit" in str(e).lower():
                wait_time = 60 * retry_count
                print(f"Rate limit hit, waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                print(f"Retrying in 10 seconds...")
                await asyncio.sleep(10)
                
            if retry_count >= max_retries:
                return f"Error: Failed to get response from Groq after {max_retries} attempts due to: {str(e)}"
    
    return "Error: Function didn't complete successfully"

async def execute_research_task(task_type, search_tool):
    """Execute a specific research task using search and analysis"""
    print(f"\n🔍 Executing {task_type} research task...")
    
    # 1. Define search query based on task type
    search_query = SEARCH_QUERIES.get(task_type, "Tunisia maritime conditions")
    print(f"   Search query: {search_query}")
    
    # 2. Perform the search
    search_results = await search_tool.search(search_query)
    formatted_results = search_tool.format_results(search_results)
    print(f"   Found {len(search_results.get('organic', [])) if 'organic' in search_results else 0} search results")
    
    # 3. Analyze the results based on task type
    prompt_template = {
        "weather": WEATHER_PROMPT,
        "fishing": FISHING_PROMPT,
        "diving": DIVING_PROMPT,
        "safety": SAFETY_PROMPT
    }.get(task_type)
    
    if not prompt_template:
        return f"Error: Unknown task type '{task_type}'"
    
    # Complete the prompt with the search query and results
    full_prompt = prompt_template.format(search_query=search_query)
    full_prompt += "\n\n# Search Results\n" + formatted_results
    
    # 4. Call Groq API for analysis
    analysis = await call_groq(full_prompt)
    
    # 5. Save results to file
    output_file = f"{task_type}_conditions.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(analysis)
    print(f"   ✅ Analysis saved to {output_file}")
    
    return analysis
    
async def generate_summary(research_results):
    """Generate a summary notification from research results"""
    print("\n📝 Generating maritime activities summary...")
    
    # Prepare the context by joining all research results
    context = "\n\n".join([f"## {key.capitalize()} Research:\n{value}" for key, value in research_results.items()])
    
    # Format the prompt with the research context
    full_prompt = SYNTHESIS_PROMPT.format(context=context)
    
    # Call Groq API for summary generation
    summary = await call_groq(full_prompt, model=SUMMARY_MODEL)
    
    # Save the summary to file
    output_file = "maritime_notification.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"   ✅ Summary saved to {output_file}")
    
    return summary

async def run_maritime_watch(search_category="1"):
    """Main function to run the maritime watch process"""
    print("\n🌊 Starting Maritime Watch System...")
    print(f"🔍 Using search category: {SEARCH_CATEGORIES[search_category]}")
    
    # Initialize search tool
    search_tool = SerperSearch(api_key=os.getenv("SERPER_API_KEY"))
    
    # Store research results
    research_results = {}
    
    # Determine which tasks to run based on search category
    tasks = []
    if search_category in ["1", "2", "4"]:
        tasks.append("weather")
    if search_category in ["1", "2"]:
        tasks.append("fishing")
    if search_category in ["1", "3"]:
        tasks.append("diving")
    if search_category in ["1", "4"]:
        tasks.append("safety")
    
    # Execute each task with delays
    for i, task in enumerate(tasks):
        print(f"\n📌 Task {i+1}/{len(tasks)}: {task.capitalize()} Research")
        result = await execute_research_task(task, search_tool)
        if result and not result.startswith("Error:"):
            research_results[task] = result
        else:
            research_results[task] = f"Research failed: {result}"
        
        # Add delay between tasks
        if i < len(tasks) - 1:
            delay_time = 10  # Reduced delay for API testing
            print(f"\n⏱️ Adding delay of {delay_time} seconds between tasks...")
            await asyncio.sleep(delay_time)
    
    # Generate summary if we have research results
    notification = ""
    if research_results:
        notification = await generate_summary(research_results)
        
        # Display all results
        print("\n--- All Generated File Contents ---")
        for task in tasks:
            print(f"\n--- {task.upper()}_CONDITIONS.MD ---")
            print(research_results[task])
        
        print("\n--- MARITIME_NOTIFICATION.TXT ---")
        print(notification)
        
        return {
            "status": "success", 
            "notification": notification,
            "tasks": tasks
        }
    else:
        return {
            "status": "error", 
            "error": "No research results were generated.",
            "tasks": []
        }