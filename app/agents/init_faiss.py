import os
from .rag_agent import RAGAgent

def initialize_faiss_index():
    """Initialise l'index FAISS en utilisant le fichier loi.txt"""
    try:
        # Créer une instance de RAGAgent
        agent = RAGAgent()
        
        # Vérifier si le fichier loi.txt existe
        data_file = os.path.join(agent.data_path, "loi.txt")
        if not os.path.exists(data_file):
            print(f"Erreur: Le fichier {data_file} n'existe pas.")
            return False
            
        # Construire l'index
        print("Construction de l'index FAISS...")
        agent.build_index()
        print("Index FAISS créé avec succès!")
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de l'index FAISS: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_faiss_index()