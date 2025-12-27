from sentence_transformers import SentenceTransformer
import torch
import numpy as np

# Singleton to hold models
class EmbeddingModels:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingModels, cls).__new__(cls)
            cls._instance.text_model = None
            cls._instance.clip_model = None
        return cls._instance

    def load_models(self):
        """Loads the models if not already loaded."""
        if self.text_model is None:
            print("Loading Text Embedding Model (all-MiniLM-L6-v2)...")
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Placeholder for CLIP or loading a small CLIP model
        # For this hackathon sandbox, we might skip actual CLIP loading to save RAM
        # and simulate the vector
        pass

    def get_text_embedding(self, text):
        if self.text_model is None:
            self.load_models()
        return self.text_model.encode(text).tolist()

    def get_clip_embedding(self, image_input):
        """
        Returns a 512-dim vector.
        If real CLIP is not loaded, returns a random/zero vector or padded text vector.
        """
        # Mocking for Architecture demonstration if model is heavy
        return np.random.rand(512).tolist()

def get_embeddings_instance():
    return EmbeddingModels()
