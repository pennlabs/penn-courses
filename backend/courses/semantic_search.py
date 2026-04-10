# ============================================
# 🚀 Semantic Search Backend for Penn Courses
# ============================================

import numpy as np
import torch
from django.conf import settings
from django.db.models import Q
from rest_framework import filters
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class SemanticCourseSearchBackend(filters.BaseFilterBackend):
    """
    Semantic search backend for courses using sentence transformers.
    Integrates with Django REST framework filter system.
    """
    
    def __init__(self):
        self.model_name = getattr(settings, 'SEMANTIC_SEARCH_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        self.batch_size = getattr(settings, 'SEMANTIC_SEARCH_BATCH_SIZE', 32)
        self.max_length = getattr(settings, 'SEMANTIC_SEARCH_MAX_LENGTH', 256)
        self.top_k = getattr(settings, 'SEMANTIC_SEARCH_TOP_K', 10)
        self.similarity_threshold = getattr(settings, 'SEMANTIC_SEARCH_THRESHOLD', 0.3)
        
        # Initialize model components
        self.tokenizer = None
        self.model = None
        self.device = torch.device('cpu')
        self._model_loaded = False
        
    def _load_model(self):
        """Lazy load the embedding model"""
        if self._model_loaded:
            return
            
        try:
            logger.info(f"Loading semantic search model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            ).eval()
            self._model_loaded = True
            logger.info("Semantic search model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load semantic search model: {e}")
            raise
    
    @torch.no_grad()
    def _embed_batch(self, batch_texts):
        """Generate embeddings for a batch of texts"""
        if not batch_texts or not any(text.strip() for text in batch_texts):
            return np.array([])
            
        # Filter out empty texts
        valid_texts = [text for text in batch_texts if text and text.strip()]
        if not valid_texts:
            return np.array([])
            
        inputs = self.tokenizer(
            valid_texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=self.max_length
        ).to(self.device)

        outputs = self.model(**inputs)
        
        # Mean pooling with attention mask
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        mean_embeddings = sum_embeddings / sum_mask
        
        # Normalize embeddings
        mean_embeddings = torch.nn.functional.normalize(mean_embeddings, p=2, dim=1)
        return mean_embeddings.cpu().numpy().astype(np.float32)
    
    def _generate_query_embedding(self, query):
        """Generate embedding for search query"""
        self._load_model()
        query_embedding = self._embed_batch([query])
        if len(query_embedding) > 0:
            return query_embedding[0]
        return None
    
    def _get_course_texts(self, queryset):
        """Extract searchable text from courses"""
        course_texts = []
        course_ids = []
        
        for course in queryset:
            # Combine course title, description, and instructor names
            text_parts = []
            
            if course.title:
                text_parts.append(course.title)
            
            if hasattr(course, 'description') and course.description:
                text_parts.append(course.description)
            
            # Add instructor names
            if hasattr(course, 'sections'):
                instructors = set()
                for section in course.sections.all():
                    for instructor in section.instructors.all():
                        instructors.add(instructor.name)
                text_parts.extend(list(instructors))
            
            # Add department name if available
            if hasattr(course, 'department') and course.department:
                text_parts.append(course.department.name)
            
            combined_text = " ".join(text_parts)
            course_texts.append(combined_text)
            course_ids.append(course.id)
        
        return course_texts, course_ids
    
    def _semantic_search_courses(self, query, queryset):
        """Perform semantic search on courses"""
        self._load_model()
        
        # Generate query embedding
        query_embedding = self._generate_query_embedding(query)
        if query_embedding is None:
            return queryset.none()
        
        # Get course texts and IDs
        course_texts, course_ids = self._get_course_texts(queryset)
        
        if not course_texts:
            return queryset.none()
        
        # Generate embeddings for all courses in batches
        course_embeddings = []
        for i in range(0, len(course_texts), self.batch_size):
            batch = course_texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch)
            course_embeddings.extend(batch_embeddings)
        
        if not course_embeddings:
            return queryset.none()
        
        # Calculate similarities
        course_embeddings = np.array(course_embeddings)
        query_embedding = query_embedding.reshape(1, -1)
        similarities = cosine_similarity(query_embedding, course_embeddings)[0]
        
        # Get top results above threshold
        valid_indices = np.where(similarities >= self.similarity_threshold)[0]
        if len(valid_indices) == 0:
            return queryset.none()
        
        # Sort by similarity and get top k
        sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]][:self.top_k]
        
        # Get corresponding course IDs
        top_course_ids = [course_ids[i] for i in sorted_indices]
        
        # Return filtered queryset
        return queryset.filter(id__in=top_course_ids)
    
    def get_schema_operation_parameters(self, view):
        """For API documentation"""
        return [
            {
                "name": "semantic_search",
                "schema": {"type": "string"},
                "required": False,
                "in": "query",
                "description": "Semantic search query. Finds courses based on meaning and context, "
                              "not just exact keyword matches. Works well for conceptual searches "
                              "like 'machine learning', 'data analysis', 'programming courses'.",
            },
            {
                "name": "semantic_threshold",
                "schema": {"type": "number", "minimum": 0, "maximum": 1},
                "required": False,
                "in": "query",
                "description": "Similarity threshold for semantic search results (0-1). "
                              "Higher values return more precise but fewer results.",
            },
            {
                "name": "semantic_top_k",
                "schema": {"type": "integer", "minimum": 1, "maximum": 50},
                "required": False,
                "in": "query",
                "description": "Maximum number of semantic search results to return.",
            },
        ]
    
    def filter_queryset(self, request, queryset, view):
        """Main filter method called by Django REST framework"""
        semantic_query = request.query_params.get('semantic_search', '').strip()
        
        if not semantic_query:
            return queryset
        
        # Allow override of default settings via query parameters
        threshold = request.query_params.get('semantic_threshold')
        if threshold is not None:
            try:
                self.similarity_threshold = float(threshold)
            except ValueError:
                pass
        
        top_k = request.query_params.get('semantic_top_k')
        if top_k is not None:
            try:
                self.top_k = int(top_k)
            except ValueError:
                pass
        
        try:
            return self._semantic_search_courses(semantic_query, queryset)
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            # Fall back to empty results on error
            return queryset.none()


class HybridCourseSearchBackend(filters.BaseFilterBackend):
    """
    Hybrid search backend that combines semantic and traditional keyword search.
    """
    
    def __init__(self):
        self.semantic_backend = SemanticCourseSearchBackend()
        self.keyword_backend = filters.SearchFilter()
        
    def get_schema_operation_parameters(self, view):
        """For API documentation"""
        params = self.semantic_backend.get_schema_operation_parameters(view)
        params.extend([
            {
                "name": "search",
                "schema": {"type": "string"},
                "required": False,
                "in": "query",
                "description": "Traditional keyword search query. Searches course codes, titles, "
                              "and instructor names using exact matches and regex patterns.",
            },
            {
                "name": "search_type",
                "schema": {"type": "string", "enum": ["semantic", "keyword", "hybrid"]},
                "required": False,
                "in": "query",
                "description": "Search type: 'semantic' for meaning-based search, 'keyword' for "
                              "traditional search, 'hybrid' for combined results.",
            },
        ])
        return params
    
    def filter_queryset(self, request, queryset, view):
        """Combine semantic and keyword search results"""
        semantic_query = request.query_params.get('semantic_search', '').strip()
        keyword_query = request.query_params.get('search', '').strip()
        search_type = request.query_params.get('search_type', 'hybrid').lower()
        
        if not semantic_query and not keyword_query:
            return queryset
        
        results = []
        
        # Semantic search
        if semantic_query and search_type in ['semantic', 'hybrid']:
            try:
                semantic_results = self.semantic_backend.filter_queryset(request, queryset, view)
                results.extend(semantic_results)
            except Exception as e:
                logger.error(f"Semantic search error in hybrid: {e}")
        
        # Keyword search
        if keyword_query and search_type in ['keyword', 'hybrid']:
            try:
                keyword_results = self.keyword_backend.filter_queryset(request, queryset, view)
                results.extend(keyword_results)
            except Exception as e:
                logger.error(f"Keyword search error in hybrid: {e}")
        
        # Combine and deduplicate results
        if results:
            # Get unique course IDs
            course_ids = set()
            for result in results:
                if hasattr(result, 'id'):
                    course_ids.add(result.id)
                else:
                    # Handle queryset results
                    for course in result:
                        course_ids.add(course.id)
            
            return queryset.filter(id__in=list(course_ids))
        
        return queryset.none()


# ============================================
# 🛠️ Utility Functions for Course Embeddings
# ============================================

def generate_course_embeddings_batch(courses, model_name='sentence-transformers/all-MiniLM-L6-v2', batch_size=32):
    """
    Generate embeddings for a batch of courses.
    Useful for pre-computing embeddings and storing them in the database.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    ).eval()
    
    device = torch.device('cpu')
    
    @torch.no_grad()
    def embed_batch(batch_texts):
        if not batch_texts or not any(text.strip() for text in batch_texts):
            return np.array([])
            
        valid_texts = [text for text in batch_texts if text and text.strip()]
        if not valid_texts:
            return np.array([])
            
        inputs = tokenizer(
            valid_texts,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=256
        ).to(device)

        outputs = model(**inputs)
        
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        mean_embeddings = sum_embeddings / sum_mask
        
        mean_embeddings = torch.nn.functional.normalize(mean_embeddings, p=2, dim=1)
        return mean_embeddings.cpu().numpy().astype(np.float32)
    
    # Prepare course texts
    course_texts = []
    course_ids = []
    
    for course in courses:
        text_parts = []
        
        if course.title:
            text_parts.append(course.title)
        
        if hasattr(course, 'description') and course.description:
            text_parts.append(course.description)
        
        if hasattr(course, 'sections'):
            instructors = set()
            for section in course.sections.all():
                for instructor in section.instructors.all():
                    instructors.add(instructor.name)
            text_parts.extend(list(instructors))
        
        if hasattr(course, 'department') and course.department:
            text_parts.append(course.department.name)
        
        combined_text = " ".join(text_parts)
        course_texts.append(combined_text)
        course_ids.append(course.id)
    
    # Generate embeddings in batches
    embeddings = []
    for i in tqdm(range(0, len(course_texts), batch_size), desc="Generating embeddings"):
        batch = course_texts[i:i + batch_size]
        batch_embeddings = embed_batch(batch)
        embeddings.extend(batch_embeddings)
    
    return dict(zip(course_ids, embeddings))


def cosine_similarity_search(query_embedding, course_embeddings_dict, top_k=10, threshold=0.3):
    """
    Perform cosine similarity search using pre-computed embeddings.
    
    Args:
        query_embedding: numpy array of query embedding
        course_embeddings_dict: dict mapping course_id to embedding
        top_k: number of top results to return
        threshold: minimum similarity threshold
    
    Returns:
        list of (course_id, similarity_score) tuples
    """
    if not course_embeddings_dict:
        return []
    
    course_ids = list(course_embeddings_dict.keys())
    embeddings = np.array(list(course_embeddings_dict.values()))
    
    query_embedding = query_embedding.reshape(1, -1)
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Filter by threshold and get top k
    valid_indices = np.where(similarities >= threshold)[0]
    if len(valid_indices) == 0:
        return []
    
    sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]][:top_k]
    
    return [(course_ids[i], similarities[i]) for i in sorted_indices]



