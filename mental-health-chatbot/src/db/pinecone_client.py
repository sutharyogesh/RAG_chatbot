"""
Pinecone Vector Database Client for Semantic Search
"""

import os
import json
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import openai
from openai import OpenAI

class PineconeClient:
    """Pinecone client for vector database operations"""
    
    def __init__(self):
        """Initialize Pinecone client"""
        self.api_key = os.environ.get('PINECONE_API_KEY')
        self.environment = os.environ.get('PINECONE_ENVIRONMENT', 'us-east-1')
        self.index_name = os.environ.get('PINECONE_INDEX_NAME', 'mental-health-embeddings')
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        # Get or create index
        self.index = self._get_or_create_index()
    
    def _get_or_create_index(self):
        """Get existing index or create new one"""
        try:
            # Check if index exists
            if self.index_name in self.pc.list_indexes().names():
                return self.pc.Index(self.index_name)
            else:
                # Create new index
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=self.environment
                    )
                )
                return self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Error creating Pinecone index: {e}")
            return None
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []
    
    def store_embedding(self, 
                       vector_id: str, 
                       text: str, 
                       metadata: Dict[str, Any] = None) -> bool:
        """Store text embedding in Pinecone"""
        try:
            embedding = self.generate_embedding(text)
            if not embedding:
                return False
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata['text'] = text
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[{
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                }]
            )
            return True
        except Exception as e:
            print(f"Error storing embedding: {e}")
            return False
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5,
                      filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Search Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            similar_items = []
            for match in results.matches:
                similar_items.append({
                    'id': match.id,
                    'score': match.score,
                    'text': match.metadata.get('text', ''),
                    'metadata': match.metadata
                })
            
            return similar_items
        except Exception as e:
            print(f"Error searching similar vectors: {e}")
            return []
    
    def store_conversation_context(self, 
                                 session_id: str, 
                                 message: str, 
                                 context_type: str = 'conversation') -> bool:
        """Store conversation context for semantic search"""
        metadata = {
            'session_id': session_id,
            'context_type': context_type,
            'timestamp': str(datetime.now())
        }
        
        vector_id = f"{session_id}_{context_type}_{int(datetime.now().timestamp())}"
        return self.store_embedding(vector_id, message, metadata)
    
    def search_mental_health_resources(self, 
                                     query: str, 
                                     resource_type: str = None) -> List[Dict[str, Any]]:
        """Search for mental health resources"""
        filter_dict = {'context_type': 'resource'}
        if resource_type:
            filter_dict['resource_type'] = resource_type
        
        return self.search_similar(query, top_k=10, filter_dict=filter_dict)
    
    def search_similar_conversations(self, 
                                   query: str, 
                                   session_id: str = None) -> List[Dict[str, Any]]:
        """Search for similar past conversations"""
        filter_dict = {'context_type': 'conversation'}
        if session_id:
            filter_dict['session_id'] = session_id
        
        return self.search_similar(query, top_k=5, filter_dict=filter_dict)
    
    def store_mental_health_resource(self, 
                                   resource_id: str,
                                   title: str,
                                   content: str,
                                   resource_type: str,
                                   category: str = None) -> bool:
        """Store mental health resource for semantic search"""
        metadata = {
            'title': title,
            'resource_type': resource_type,
            'category': category or 'general',
            'context_type': 'resource'
        }
        
        return self.store_embedding(resource_id, content, metadata)
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        try:
            self.index.delete(ids=vector_ids)
            return True
        except Exception as e:
            print(f"Error deleting vectors: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness
            }
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {}

# Initialize global Pinecone client
pinecone_client = None

def get_pinecone_client() -> PineconeClient:
    """Get global Pinecone client instance"""
    global pinecone_client
    if pinecone_client is None:
        pinecone_client = PineconeClient()
    return pinecone_client