"""
Integration module for Groq LLM API.
Provides a client class to interact with Groq's API in a secure and reusable way.
"""

import os
import json
import requests
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GroqClient:
    """Client for interacting with Groq's LLM API"""
    
    def __init__(self):
        """Initialize the Groq client with API key from config"""
        config_path = Path(__file__).parent.parent / 'config' / 'api_keys.json'
        try:
            with open(config_path) as f:
                config = json.load(f)
                self.api_key = config.get('GROQ_API_KEY')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading Groq API key: {e}")
            self.api_key = None
            
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.default_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.HTTPError),
        before_sleep=lambda retry_state: logger.info(
            f"Retrying API call (attempt {retry_state.attempt_number}/3) after {retry_state.next_action.sleep} seconds..."
        )
    )
    def generate_response(self, prompt, model=None):
        """
        Generate a response using Groq's API.
        
        Args:
            prompt (str): The input prompt
            model (str, optional): Model to use. Defaults to llama-4-scout
            
        Returns:
            dict: The API response
            
        Raises:
            ValueError: If API key is not configured
            requests.exceptions.RequestException: If API call fails
        """
        if not self.api_key:
            raise ValueError("Groq API key not configured")
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model or self.default_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30  # Increased timeout
            )
            response.raise_for_status()
            logger.info("Groq API call successful")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"Groq API HTTP error: {e}, Response: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request error: {e}")
            raise