#!/usr/bin/env python3
"""
Production Configuration for Enhanced AI System
"""

from app.core.config import settings
import os

class ProductionAIConfig:
    """Production-ready AI configuration"""
    
    # Model configurations
    SENTENCE_BERT_MODEL = "all-MiniLM-L6-v2"  # Fast and accurate
    FAISS_INDEX_TYPE = "IndexFlatIP"  # Inner product for cosine similarity
    FAISS_DIMENSIONS = 384  # Dimensions for all-MiniLM-L6-v2
    
    # Performance settings
    MAX_CACHE_SIZE = 1000
    CACHE_CLEANUP_THRESHOLD = 200
    
    # Timeout settings (in seconds)
    OLLAMA_TIMEOUT = 15
    SENTENCE_BERT_TIMEOUT = 10
    FAISS_TIMEOUT = 5
    TFIDF_TIMEOUT = 2
    
    # Scoring weights
    OLLAMA_WEIGHT = 0.4
    SENTENCE_BERT_WEIGHT = 0.3
    FAISS_WEIGHT = 0.2
    TFIDF_WEIGHT = 0.1
    
    # Text processing limits
    MAX_RESUME_LENGTH = 5000
    MAX_JD_LENGTH = 2000
    TRUNCATION_LENGTH = 200
    
    # Quality thresholds
    MIN_SCORE_THRESHOLD = 60
    HIGH_SCORE_THRESHOLD = 80
    EXCELLENT_SCORE_THRESHOLD = 90
    
    @classmethod
    def get_optimized_settings(cls):
        """Get optimized settings for production"""
        return {
            "ollama_timeout": cls.OLLAMA_TIMEOUT,
            "ollama_max_tokens": 50,
            "ollama_temperature": 0.0,
            "ollama_top_p": 0.3,
            "max_cache_size": cls.MAX_CACHE_SIZE,
            "sentence_bert_model": cls.SENTENCE_BERT_MODEL,
            "faiss_dimensions": cls.FAISS_DIMENSIONS,
            "scoring_weights": {
                "ollama": cls.OLLAMA_WEIGHT,
                "sentence_bert": cls.SENTENCE_BERT_WEIGHT,
                "faiss": cls.FAISS_WEIGHT,
                "tfidf": cls.TFIDF_WEIGHT
            }
        }
    
    @classmethod
    def get_performance_metrics(cls):
        """Get expected performance metrics"""
        return {
            "single_resume_time": "5-15 seconds",
            "batch_processing": "2-5 seconds per resume",
            "memory_usage": "~500MB for models",
            "cpu_usage": "Moderate during processing",
            "accuracy": "85-95% for good matches"
        }

class AIPerformanceMonitor:
    """Monitor AI system performance"""
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "ollama_success": 0,
            "ollama_timeouts": 0,
            "sentence_bert_success": 0,
            "faiss_success": 0,
            "tfidf_success": 0,
            "average_processing_time": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def record_request(self, processing_time: float, ollama_success: bool = False, 
                      ollama_timeout: bool = False, cache_hit: bool = False):
        """Record a request and its metrics"""
        self.metrics["total_requests"] += 1
        self.metrics["average_processing_time"] = (
            (self.metrics["average_processing_time"] * (self.metrics["total_requests"] - 1) + processing_time) 
            / self.metrics["total_requests"]
        )
        
        if ollama_success:
            self.metrics["ollama_success"] += 1
        if ollama_timeout:
            self.metrics["ollama_timeouts"] += 1
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
    
    def get_performance_report(self):
        """Get current performance report"""
        total = self.metrics["total_requests"]
        if total == 0:
            return "No requests processed yet"
        
        ollama_success_rate = (self.metrics["ollama_success"] / total) * 100
        cache_hit_rate = (self.metrics["cache_hits"] / total) * 100
        
        return {
            "total_requests": total,
            "average_processing_time": f"{self.metrics['average_processing_time']:.2f}s",
            "ollama_success_rate": f"{ollama_success_rate:.1f}%",
            "ollama_timeout_rate": f"{(self.metrics['ollama_timeouts'] / total) * 100:.1f}%",
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "performance_grade": self._get_performance_grade()
        }
    
    def _get_performance_grade(self):
        """Get performance grade based on metrics"""
        avg_time = self.metrics["average_processing_time"]
        ollama_success_rate = (self.metrics["ollama_success"] / max(1, self.metrics["total_requests"])) * 100
        
        if avg_time < 10 and ollama_success_rate > 80:
            return "A+ (Excellent)"
        elif avg_time < 15 and ollama_success_rate > 60:
            return "A (Very Good)"
        elif avg_time < 20 and ollama_success_rate > 40:
            return "B (Good)"
        elif avg_time < 30:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"

# Global performance monitor
performance_monitor = AIPerformanceMonitor()
