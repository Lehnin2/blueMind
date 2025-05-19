from supabase import create_client, Client
from .settings import SUPABASE_URL, SUPABASE_KEY
import logging

logger = logging.getLogger(__name__)

try:
    logger.debug(f"Initialisation de Supabase avec URL: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.debug("Client Supabase initialisé avec succès")
except Exception as e:
    logger.error(f"Erreur lors de l'initialisation de Supabase: {str(e)}")
    raise 