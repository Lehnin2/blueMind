from typing import Dict
from chatbot_agent import TraeFishingAgent
from ui_chatbot import UIChatbot

class AgentRouter:
    def __init__(self):
        # Initialize the chatbot agent
        self.chatbot_agent = TraeFishingAgent()
        # Initialize the UI chatbot (assistant contextuel d'interface)
        self.ui_chatbot = UIChatbot()
        
    def handle_message(self, message: str, use_voice: bool = False, force_maritime: bool = False) -> Dict[str, str]:
        """Handle the message using the chatbot agent."""
        return self.chatbot_agent.handle_message(message, use_voice)
        
    def handle_ui_message(self, message: str) -> Dict[str, str]:
        """Handle the message using the UI chatbot (assistant contextuel d'interface)."""
        return self.ui_chatbot.handle_message(message)

    def listen(self):
        """Pass through to the chatbot agent's listen method."""
        return self.chatbot_agent.listen()