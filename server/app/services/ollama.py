"""Ollama LLM client service."""

import httpx
import logging
from typing import Optional, AsyncGenerator
from config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama LLM API."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = "mistral"  # Default model
        self.timeout = 60  # LLM calls can take time
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5
                )
                
                if response.status_code == 200:
                    logger.info("✅ Ollama service is healthy")
                    return True
                else:
                    logger.error(f"❌ Ollama health check failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ollama connection error: {str(e)}")
            return False
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40
    ) -> Optional[str]:
        """Generate text using Ollama."""
        
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("response", "").strip()
                    
                    logger.info(f"✅ Generated text ({len(text)} chars)")
                    return text
                else:
                    logger.error(f"❌ Generation failed: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"❌ Ollama generation error: {str(e)}")
            return None
    
    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Generate text using Ollama with streaming."""
        
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "temperature": temperature
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                import json
                                try:
                                    data = json.loads(line)
                                    text = data.get("response", "")
                                    if text:
                                        yield text
                                except json.JSONDecodeError:
                                    continue
                    else:
                        logger.error(f"❌ Stream generation failed: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Ollama stream error: {str(e)}")
    
    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """Chat interface for Ollama."""
        
        model = model or self.model
        
        # Convert messages to prompt format
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        
        prompt += "Assistant:"
        
        return await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature
        )
    
    async def embedding(self, text: str, model: str = "mistral") -> Optional[list]:
        """Generate embeddings for text (if model supports it)."""
        
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embedding = data.get("embedding", [])
                    logger.info(f"✅ Generated embedding ({len(embedding)} dims)")
                    return embedding
                else:
                    logger.error(f"❌ Embedding failed: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"❌ Ollama embedding error: {str(e)}")
            return None


# Global instance
ollama_client = OllamaClient()
