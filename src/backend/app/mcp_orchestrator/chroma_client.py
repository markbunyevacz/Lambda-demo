import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)


class ChromaClient:
    """A client for interacting with ChromaDB."""

    def __init__(self, host="chroma", port=8000):
        try:
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(anonymized_telemetry=False)
            )
            # Heartbeat to check connection
            self.client.heartbeat()
            logger.info(
                f"✅ ChromaDB client initialized and connected to {host}:{port}"
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to connect to ChromaDB at {host}:{port}. Error: {e}"
            )
            self.client = None

    def get_or_create_collection(self, name: str):
        """
        Gets or creates a collection by name.

        Args:
            name (str): The name of the collection.

        Returns:
            The ChromaDB collection object.
        """
        if not self.client:
            logger.error("ChromaDB client not available.")
            return None
        try:
            collection = self.client.get_or_create_collection(name=name)
            logger.info(f"Successfully got or created collection: '{name}'")
            return collection
        except Exception as e:
            logger.error(
                f"Failed to get or create collection '{name}'. Error: {e}"
            )
            return None
    
    def delete_collection(self, name: str):
        """Deletes a collection by name."""
        if not self.client:
            logger.error("ChromaDB client not available.")
            return
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Successfully deleted collection: '{name}'")
        except Exception as e:
            # It's okay if the collection doesn't exist
            if "does not exist" in str(e):
                logger.warning(
                    f"Collection '{name}' not found for deletion, skipping."
                )
            else:
                logger.error(
                    f"Failed to delete collection '{name}'. Error: {e}"
                )

    def add_to_collection(
        self, collection_name: str, documents: list, metadatas: list, ids: list
    ):
        """Adds documents to a specified collection."""
        collection = self.get_or_create_collection(collection_name)
        if collection:
            try:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(
                    f"Added {len(documents)} documents to "
                    f"collection '{collection_name}'."
                )
            except Exception as e:
                logger.error(
                    "Failed to add documents to collection '%s'. Error: %s",
                    collection_name, e
                ) 