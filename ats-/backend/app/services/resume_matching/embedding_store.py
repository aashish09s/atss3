"""
Embedding Store Module
Handles generation and storage of embeddings using sentence-transformers and FAISS.
"""

import os
import json
import pickle
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from .models import ResumeData, JobDescription
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings using sentence-transformers models.
    Optimized for batch processing and caching.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of the sentence-transformer model
        """
        self.model_name = model_name or settings.embeddings_model
        self.model = None
        self.embedding_dim = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence-transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Get embedding dimension
            sample_embedding = self.model.encode(["test"])
            self.embedding_dim = len(sample_embedding[0])
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {e}")
            raise
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Clean and truncate text if too long
        text = text.strip()[:8192]  # Most models have token limits
        
        if not text:
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        try:
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def generate_batch_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = None,
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            2D numpy array of embeddings
        """
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        if not texts:
            return np.array([]).reshape(0, self.embedding_dim)
        
        batch_size = batch_size or settings.batch_size
        
        # Clean texts
        cleaned_texts = [text.strip()[:8192] if text else "" for text in texts]
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            # Process in batches to manage memory
            all_embeddings = []
            
            for i in tqdm(range(0, len(cleaned_texts), batch_size), 
                         desc="Generating embeddings",
                         disable=not show_progress):
                batch_texts = cleaned_texts[i:i + batch_size]
                batch_embeddings = self.model.encode(
                    batch_texts, 
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                all_embeddings.append(batch_embeddings)
            
            embeddings = np.vstack(all_embeddings).astype(np.float32)
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero embeddings as fallback
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
    
    def generate_resume_embedding(self, resume: ResumeData) -> np.ndarray:
        """
        Generate embedding for a resume.
        Combines text from multiple fields for better representation.
        
        Args:
            resume: ResumeData object
            
        Returns:
            Embedding vector
        """
        # Combine relevant text fields
        text_parts = []
        
        if resume.name:
            text_parts.append(f"Name: {resume.name}")
        
        if resume.skills:
            text_parts.append(f"Skills: {', '.join(resume.skills)}")
        
        if resume.years_of_experience is not None:
            text_parts.append(f"Experience: {resume.years_of_experience} years")
        
        # Add raw text (truncated)
        if resume.raw_text:
            text_parts.append(resume.raw_text[:4096])
        
        combined_text = "\n".join(text_parts)
        return self.generate_text_embedding(combined_text)
    
    def generate_jd_embedding(self, jd: JobDescription) -> np.ndarray:
        """
        Generate embedding for a job description.
        
        Args:
            jd: JobDescription object
            
        Returns:
            Embedding vector
        """
        # Combine relevant text fields
        text_parts = []
        
        if jd.title:
            text_parts.append(f"Title: {jd.title}")
        
        if jd.company:
            text_parts.append(f"Company: {jd.company}")
        
        if jd.required_skills:
            text_parts.append(f"Required Skills: {', '.join(jd.required_skills)}")
        
        if jd.preferred_skills:
            text_parts.append(f"Preferred Skills: {', '.join(jd.preferred_skills)}")
        
        if jd.min_experience is not None:
            text_parts.append(f"Minimum Experience: {jd.min_experience} years")
        
        # Add description
        if jd.description:
            text_parts.append(jd.description)
        
        combined_text = "\n".join(text_parts)
        return self.generate_text_embedding(combined_text)


class FAISSIndex:
    """
    FAISS-based vector index for efficient similarity search.
    Handles index creation, loading, saving, and querying.
    """
    
    def __init__(self, embedding_dim: int, index_type: str = "IVF"):
        """
        Initialize FAISS index.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_type: Type of FAISS index ("Flat", "IVF", "HNSW")
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        self.index = None
        self.id_mapping = {}  # Maps FAISS index positions to resume IDs
        self.resume_metadata = {}  # Stores resume metadata
        self._create_index()
    
    def _create_index(self) -> None:
        """Create FAISS index based on specified type."""
        if self.index_type == "Flat":
            # Exact search (slower but accurate)
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product
        elif self.index_type == "IVF":
            # Approximate search with inverted file index
            quantizer = faiss.IndexFlatIP(self.embedding_dim)
            nlist = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World (good for high recall)
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        logger.info(f"Created FAISS {self.index_type} index with dimension {self.embedding_dim}")
    
    def add_embeddings(
        self, 
        embeddings: np.ndarray, 
        resume_ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: 2D array of embeddings
            resume_ids: List of resume IDs
            metadata: Optional metadata for each resume
        """
        if len(embeddings) != len(resume_ids):
            raise ValueError("Number of embeddings must match number of resume IDs")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Train index if needed (for IVF)
        if self.index_type == "IVF" and not self.index.is_trained:
            logger.info("Training FAISS index...")
            self.index.train(embeddings)
        
        # Add embeddings
        start_idx = self.index.ntotal
        self.index.add(embeddings)
        
        # Update mappings
        for i, resume_id in enumerate(resume_ids):
            faiss_idx = start_idx + i
            self.id_mapping[faiss_idx] = resume_id
            
            if metadata and i < len(metadata):
                self.resume_metadata[resume_id] = metadata[i]
        
        logger.info(f"Added {len(embeddings)} embeddings to index. Total: {self.index.ntotal}")
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10,
        threshold: float = 0.0
    ) -> Tuple[List[str], List[float]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (resume_ids, similarity_scores)
        """
        if self.index.ntotal == 0:
            return [], []
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)
        
        # Search
        similarities, indices = self.index.search(query_embedding, k)
        
        # Convert results
        resume_ids = []
        scores = []
        
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for invalid results
                continue
            
            if similarity >= threshold:
                resume_id = self.id_mapping.get(idx)
                if resume_id:
                    resume_ids.append(resume_id)
                    scores.append(float(similarity))
        
        return resume_ids, scores
    
    def save(self, file_path: str) -> None:
        """Save index and mappings to disk."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = str(file_path.with_suffix('.faiss'))
        faiss.write_index(self.index, index_path)
        
        # Save mappings and metadata
        metadata_path = str(file_path.with_suffix('.pkl'))
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'id_mapping': self.id_mapping,
                'resume_metadata': self.resume_metadata,
                'embedding_dim': self.embedding_dim,
                'index_type': self.index_type
            }, f)
        
        logger.info(f"Saved FAISS index to {index_path}")
        logger.info(f"Saved metadata to {metadata_path}")
    
    def load(self, file_path: str) -> None:
        """Load index and mappings from disk."""
        file_path = Path(file_path)
        
        # Load FAISS index
        index_path = str(file_path.with_suffix('.faiss'))
        if not Path(index_path).exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        
        self.index = faiss.read_index(index_path)
        
        # Load mappings and metadata
        metadata_path = str(file_path.with_suffix('.pkl'))
        if Path(metadata_path).exists():
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.id_mapping = data.get('id_mapping', {})
                self.resume_metadata = data.get('resume_metadata', {})
                self.embedding_dim = data.get('embedding_dim', self.embedding_dim)
                self.index_type = data.get('index_type', self.index_type)
        
        logger.info(f"Loaded FAISS index from {index_path}")
        logger.info(f"Index contains {self.index.ntotal} embeddings")


class EmbeddingStore:
    """
    High-level interface for embedding generation and storage.
    Combines EmbeddingGenerator and FAISSIndex for complete functionality.
    """
    
    def __init__(
        self, 
        model_name: str = None,
        index_type: str = "IVF",
        index_path: str = None
    ):
        """
        Initialize embedding store.
        
        Args:
            model_name: Sentence transformer model name
            index_type: FAISS index type
            index_path: Path to save/load index
        """
        self.generator = EmbeddingGenerator(model_name)
        self.index = FAISSIndex(self.generator.embedding_dim, index_type)
        self.index_path = index_path or settings.faiss_index_path
        
        # Try to load existing index
        self._load_index()
    
    def _load_index(self) -> None:
        """Load existing index if available."""
        try:
            if Path(f"{self.index_path}.faiss").exists():
                self.index.load(self.index_path)
                logger.info("Loaded existing FAISS index")
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
    
    def add_resumes(self, resumes: List[ResumeData]) -> None:
        """
        Add resumes to the embedding store.
        
        Args:
            resumes: List of ResumeData objects
        """
        if not resumes:
            return
        
        logger.info(f"Adding {len(resumes)} resumes to embedding store")
        
        # Generate embeddings
        embeddings = []
        resume_ids = []
        metadata = []
        
        for resume in tqdm(resumes, desc="Generating embeddings"):
            try:
                embedding = self.generator.generate_resume_embedding(resume)
                embeddings.append(embedding)
                resume_ids.append(resume.id or resume.file_name)
                
                # Store metadata
                metadata.append({
                    'file_name': resume.file_name,
                    'name': resume.name,
                    'email': resume.email,
                    'skills': resume.skills,
                    'years_of_experience': resume.years_of_experience,
                    'processed_at': resume.processed_at.isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing resume {resume.file_name}: {e}")
                continue
        
        if embeddings:
            embeddings_array = np.vstack(embeddings)
            self.index.add_embeddings(embeddings_array, resume_ids, metadata)
            
            # Save index
            self.save_index()
    
    def search_similar_resumes(
        self, 
        jd: JobDescription, 
        k: int = 500,
        threshold: float = None
    ) -> Tuple[List[str], List[float]]:
        """
        Search for resumes similar to a job description.
        
        Args:
            jd: JobDescription object
            k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (resume_ids, similarity_scores)
        """
        threshold = threshold or settings.similarity_threshold
        
        # Generate JD embedding
        jd_embedding = self.generator.generate_jd_embedding(jd)
        
        # Search similar resumes
        resume_ids, scores = self.index.search(jd_embedding, k, threshold)
        
        logger.info(f"Found {len(resume_ids)} similar resumes for JD: {jd.title}")
        
        return resume_ids, scores
    
    def get_resume_metadata(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific resume."""
        return self.index.resume_metadata.get(resume_id)
    
    def save_index(self) -> None:
        """Save the current index to disk."""
        self.index.save(self.index_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding store."""
        return {
            'total_resumes': self.index.index.ntotal,
            'embedding_dimension': self.generator.embedding_dim,
            'model_name': self.generator.model_name,
            'index_type': self.index.index_type,
            'index_path': self.index_path
        }


# Async wrapper for batch operations
class AsyncEmbeddingStore:
    """Async wrapper for EmbeddingStore operations."""
    
    def __init__(self, embedding_store: EmbeddingStore):
        self.store = embedding_store
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def add_resumes_async(self, resumes: List[ResumeData]) -> None:
        """Async version of add_resumes."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.store.add_resumes, resumes)
    
    async def search_similar_resumes_async(
        self, 
        jd: JobDescription, 
        k: int = 500,
        threshold: float = None
    ) -> Tuple[List[str], List[float]]:
        """Async version of search_similar_resumes."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.store.search_similar_resumes, 
            jd, k, threshold
        )
