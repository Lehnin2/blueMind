import json
from typing import List, Dict
from app.tools.groq_client import GroqClient
try:
    # Importer depuis le répertoire parent pour résoudre l'erreur d'importation
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from retriverloi1 import IntelligentRetriever
except ImportError as e:
    print(f"Failed to import IntelligentRetriever: {e}")
    IntelligentRetriever = None

class TraeFishingAgent:
    def __init__(self, faiss_index_path: str = "C:/Users/user/OneDrive/Bureau/traefishing/faiss_index.bin", 
                 docstore_path: str = "C:/Users/user/OneDrive/Bureau/traefishing/docstore.json"):
        self.client = GroqClient()
        self.retriever = None
        if IntelligentRetriever:
            try:
                self.retriever = IntelligentRetriever(
                    faiss_index_path=faiss_index_path,
                    docstore_path=docstore_path,
                    embedding_model_name="BAAI/bge-m3"
                )
            except Exception as e:
                print(f"Failed to initialize retriever: {e}")
        self.memory = []
        self.max_memory_length = 10
        self.system_prompt = """You are Si lba7ri, an AI Assistant for Tunisian fishermen, integrated into the Guidmarine web app. You assist with maritime information and mapping, including:
- Providing current GPS location
- Reporting water depth at specified coordinates
- Finding the nearest port and distance to it
- Planning sea routes with waypoints and total distance
- Displaying port maps by governorate
- Checking zone restrictions (protected areas, no-fishing zones)
- Retrieving laws related to fishing restrictions, species, gears, or penalties from a database

**Instructions:**
- Analyze the user prompt (in English, French, Arabic, or Tunisian dialect) to understand intent.
- For queries about fishing laws, zones, species, gears, or penalties, use retrieved documents to provide accurate, concise answers.
- For general questions (e.g., greetings, navigation), respond conversationally without retrieval, using simple language.
- Reformulate responses to be clear, fisherman-friendly, and free of legal jargon. Summarize key points and avoid repeating document text verbatim.
- Leverage conversation history to maintain context, referencing prior exchanges if relevant.
- If no relevant documents are found, provide a helpful response based on your knowledge or ask for clarification.
- Be polite, clear, and helpful.

**Conversation History:**
{conversation_history}

**Retrieved Documents (if applicable):**
{retrieved_docs}"""

    def _update_memory(self, user_message: str, assistant_response: str):
        self.memory.append({"user": user_message, "assistant": assistant_response})
        if len(self.memory) > self.max_memory_length:
            self.memory.pop(0)

    def _get_conversation_history(self) -> str:
        if not self.memory:
            return "No prior conversation."
        history = ""
        for exchange in self.memory[-3:]:  # Limit to last 3 exchanges for brevity
            history += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n"
        return history.strip()

    def _should_use_retriever(self, message: str) -> bool:
        keywords = [
            "law", "laws", "restriction", "restrictions", "protected area", "no-fishing", 
            "zone", "regulations", "règlement", "قانون", "قوانين", "منع", "منطقة محمية",
            "penalty", "sanction", "infraction", "article", "fishing ban", "prohibited",
            "species", "gear", "method", "fishing period", "especes", "engin", "methode",
            "zembra", "galite", "kuriat", "tunis", "bizerte", "carthage", "korba", 
            "ras kapoudia", "langouste", "crevette", "poulpe", "thon", "eponge", "corail"
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in keywords)

    def handle_message(self, message: str, use_voice: bool = False) -> Dict[str, str]:
        try:
            retrieved_docs = ""
            use_retriever = self._should_use_retriever(message)

            if use_retriever and self.retriever:
                docs = self.retriever.retrieve(message, top_k=3, relevance_threshold=0.5)
                if docs:
                    retrieved_docs = "\n".join(
                        [f"Document {i+1}: {doc.page_content} (Source: {doc.metadata.get('source', 'Unknown')})"
                         for i, doc in enumerate(docs)]
                    )
                else:
                    retrieved_docs = "No relevant documents found."

            conversation_history = self._get_conversation_history()
            prompt = self.system_prompt.format(
                conversation_history=conversation_history,
                retrieved_docs=retrieved_docs
            ) + f"\n\nUser: {message}\nAssistant:"

            response = self.client.generate_response(prompt)
            text = None
            if response and "choices" in response and response["choices"]:
                choice = response["choices"][0]
                msg = choice.get("message")
                text = msg.get("content") if msg else choice.get("text")

            if not text:
                text = "Sorry, I could not understand your request. Can you clarify?"

            self._update_memory(message, text)
            return {"text": text}

        except Exception as e:
            error_msg = f"Error processing request: {str(e)}. Please try again or clarify your question."
            self._update_memory(message, error_msg)
            return {"text": error_msg}

    def listen(self):
        return ""