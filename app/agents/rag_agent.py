# Agent RAG (Retrieval Augmented Generation)
# Responsable de l'indexation et de la recherche sémantique dans les documents réglementaires

import os
import json
from typing import List, Dict, Any, Optional

# Imports pour LlamaIndex
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.core.schema import Document
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

class RAGAgent:
    """
    Agent responsable de l'indexation et de la recherche sémantique dans les documents réglementaires.
    
    Cet agent utilise LlamaIndex avec FAISS comme base de données vectorielle et BGE comme modèle d'embedding
    pour indexer et rechercher des informations pertinentes dans les documents réglementaires.
    """
    
    def __init__(self, data_path: str = None, index_path: str = None):
        """
        Initialise l'agent RAG.
        
        Args:
            data_path (str): Chemin vers le répertoire ou fichier contenant les données à indexer
            index_path (str): Chemin où sauvegarder/charger l'index vectoriel
        """
        self.data_path = data_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
        self.index_path = index_path or os.path.join(self.data_path, "index")
        self.index = None
        self.search_history = []
        
        # Créer le répertoire d'index s'il n'existe pas
        if not os.path.exists(self.index_path):
            os.makedirs(self.index_path)
        
        # Initialiser le modèle d'embedding BGE
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-fr")
        
        # Initialiser le contexte de service
        self.service_context = ServiceContext.from_defaults(embed_model=self.embed_model)
    
    def load_documents(self, file_path: Optional[str] = None) -> List[Document]:
        """
        Charge les documents à partir d'un fichier ou d'un répertoire.
        
        Args:
            file_path (str, optional): Chemin vers le fichier ou répertoire à charger
            
        Returns:
            List[Document]: Liste des documents chargés
        """
        if file_path is None:
            file_path = os.path.join(self.data_path, "loi.txt")
        
        if os.path.isfile(file_path):
            # Charger un fichier unique
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                # Diviser le texte en chunks de taille raisonnable (paragraphes)
                chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
                documents = [Document(text=chunk) for chunk in chunks]
                return documents
        else:
            # Charger un répertoire
            documents = SimpleDirectoryReader(file_path).load_data()
            return documents
    
    def build_index(self, documents: Optional[List[Document]] = None) -> None:
        """
        Construit l'index vectoriel à partir des documents.
        
        Args:
            documents (List[Document], optional): Liste des documents à indexer
        """
        if documents is None:
            documents = self.load_documents()
        
        # Initialiser le vector store FAISS
        vector_store = FaissVectorStore(dim=self.embed_model.get_embedding_dimension())
        
        # Créer l'index
        self.index = VectorStoreIndex.from_documents(
            documents,
            service_context=self.service_context,
            vector_store=vector_store
        )
        
        # Sauvegarder l'index
        self.save_index()
        
        print(f"Index construit avec succès avec {len(documents)} documents.")
    
    def save_index(self) -> None:
        """
        Sauvegarde l'index vectoriel sur le disque.
        """
        if self.index is not None:
            self.index.storage_context.persist(persist_dir=self.index_path)
            print(f"Index sauvegardé dans {self.index_path}")
    
    def load_index(self) -> None:
        """
        Charge l'index vectoriel depuis le disque.
        """
        if os.path.exists(os.path.join(self.index_path, "vector_store.faiss")):
            # Initialiser le vector store FAISS
            vector_store = FaissVectorStore.from_persist_dir(self.index_path)
            
            # Charger l'index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store,
                service_context=self.service_context
            )
            print(f"Index chargé depuis {self.index_path}")
        else:
            print("Aucun index trouvé. Veuillez construire l'index d'abord.")
    
    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Effectue une recherche sémantique dans l'index.
        
        Args:
            query (str): Requête de recherche
            top_k (int): Nombre de résultats à retourner
            filters (Dict[str, Any], optional): Filtres à appliquer
            
        Returns:
            Dict[str, Any]: Résultats de la recherche
        """
        # Charger l'index s'il n'est pas déjà chargé
        if self.index is None:
            try:
                self.load_index()
            except Exception as e:
                print(f"Erreur lors du chargement de l'index: {str(e)}")
                print("Construction d'un nouvel index...")
                self.build_index()
        
        # Créer un moteur de requête
        query_engine = self.index.as_query_engine(similarity_top_k=top_k)
        
        # Exécuter la requête
        response = query_engine.query(query)
        
        # Formater les résultats
        results = {
            "query": query,
            "results": []
        }
        
        # Extraire les nœuds sources
        for node in response.source_nodes:
            result = {
                "text": node.node.text,
                "score": node.score,
                "metadata": node.node.metadata
            }
            results["results"].append(result)
        
        # Ajouter la réponse générée
        results["generated_response"] = str(response)
        
        # Enregistrer dans l'historique de recherche
        self.search_history.append({
            "query": query,
            "filters": filters,
            "results_count": len(results["results"])
        })
        
        return results
    
    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des recherches.
        
        Args:
            limit (int): Nombre maximum d'entrées à retourner
            
        Returns:
            List[Dict[str, Any]]: Historique des recherches
        """
        return self.search_history[-limit:]
    
    def clear_search_history(self) -> None:
        """
        Efface l'historique des recherches.
        """
        self.search_history = []
        print("Historique de recherche effacé.")