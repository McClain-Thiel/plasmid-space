"""
LLM Provider implementations for natural language to token conversion.
Supports multiple providers with fallback options using structured outputs.
"""

import os
import json
from typing import List, Optional, Dict
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for LLM providers with structured output support"""
    
    @abstractmethod
    def convert_to_tokens(self, prompt: str, token_config: List[str]) -> str:
        """Convert natural language to special tokens"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (API key set)"""
        pass
    
    def create_token_schema(self, token_config: List[str]) -> Dict:
        """
        Create JSON schema for structured output.
        Groups tokens by category (HOST, RESISTANCE, GC, etc.)
        """
        # Group tokens by category
        token_groups = {}
        for token in token_config:
            if ':' in token:
                category = token.split(':')[0].replace('<', '').replace('>', '')
                if category not in token_groups:
                    token_groups[category] = []
                token_groups[category].append(token)
        
        # Create schema properties
        properties = {}
        for category, tokens in token_groups.items():
            properties[category.lower()] = {
                "type": "string",
                "enum": tokens,
                "description": f"{category} token for plasmid generation"
            }
        
        # JSON schema
        schema = {
            "type": "object",
            "properties": properties,
            "required": [],  # None are strictly required
            "additionalProperties": False
        }
        
        return schema


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider with structured output"""
    
    def __init__(self):
        self.client = None
        
    def is_available(self) -> bool:
        return os.environ.get("ANTHROPIC_API_KEY") is not None
    
    def convert_to_tokens(self, prompt: str, token_config: List[str]) -> str:
        if self.client is None:
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        
        # Create structured output schema
        schema = self.create_token_schema(token_config)
        
        # System prompt with JSON schema
        system_prompt = f"""You are a specialized assistant that converts natural language descriptions of plasmids into condition tokens.

You must respond with ONLY a JSON object containing the appropriate tokens from these categories:
{json.dumps(schema['properties'], indent=2)}

Analyze the user's description and select the most appropriate token for each relevant category.
Do not include categories that are not mentioned or implied.

Example input: "I need a high copy expression plasmid for E. coli with ampicillin resistance"
Example output: {{"host": "<HOST:ECOLI>", "copy": "<COPY:HIGH>", "application": "<APPLICATION:EXPRESSION>", "resistance": "<RESISTANCE:AMP>"}}
"""
        
        message = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON response and extract tokens
        try:
            response_text = message.content[0].text.strip()
            # Try to extract JSON if wrapped in markdown
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            token_dict = json.loads(response_text)
            tokens = ' '.join(token_dict.values())
            return tokens
        except json.JSONDecodeError:
            # Fallback: return as-is if JSON parsing fails
            return message.content[0].text.strip()
    
    def _create_system_prompt(self, token_config: List[str]) -> str:
        return f"""You are a specialized assistant that converts natural language descriptions of plasmids into special tokens.

Available tokens: {', '.join(token_config[:100])}

Your task is to analyze the user's description and output ONLY the appropriate special tokens in sequence.
Do not include any explanation, just the tokens separated by spaces.

Common token categories:
- GC content: <gc_content_low>, <gc_content_medium>, <gc_content_high>
- Copy number: <copy_number_low>, <copy_number_medium>, <copy_number_high>
- Plasmid type: <plasmid_type_expression>, <plasmid_type_cloning>, <plasmid_type_shuttle>
- Resistance markers: <resistance_ampicillin>, <resistance_kanamycin>, <resistance_chloramphenicol>
- Origins: <origin_pBR322>, <origin_pUC>, <origin_ColE1>
- Promoters: <promoter_T7>, <promoter_lac>, <promoter_tac>

Output format: <token1> <token2> <token3> ..."""


class GeminiProvider(LLMProvider):
    """Google Gemini provider with structured output"""
    
    def __init__(self):
        self.client = None
        self.model_name = None
    
    def is_available(self) -> bool:
        return os.environ.get("GOOGLE_API_KEY") is not None
    
    def convert_to_tokens(self, prompt: str, token_config: List[str]) -> str:
        if self.client is None:
            try:
                # Try the new google.genai package first
                from google import genai
                self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
                self.model_name = 'gemini-2.0-flash-exp'
                self.use_new_api = True
            except (ImportError, AttributeError):
                # Fall back to deprecated google.generativeai
                import google.generativeai as genai
                genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
                self.model_name = 'gemini-3-flash-preview'
                self.client = genai
                self.use_new_api = False
        
        # Create structured output schema
        schema = self.create_token_schema(token_config)
        
        system_instruction = """You are a specialized assistant that converts natural language descriptions of plasmids into condition tokens.

Analyze the user's description and return a JSON object with the appropriate tokens for each relevant category.
Only include categories that are mentioned or clearly implied in the description."""
        
        if self.use_new_api:
            # New API with structured output
            full_prompt = f"{system_instruction}\n\nUser request: {prompt}\n\nReturn only a JSON object with the appropriate tokens."
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': schema
                }
            )
            # Parse JSON response
            try:
                token_dict = json.loads(response.text)
                tokens = ' '.join(token_dict.values())
                return tokens
            except json.JSONDecodeError:
                return response.text.strip()
        else:
            # Old API with generation config
            generation_config = {
                'temperature': 0.7,
                'response_mime_type': 'application/json',
            }
            
            model = self.client.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_instruction
            )
            
            full_prompt = f"User request: {prompt}\n\nAvailable tokens: {json.dumps(schema['properties'], indent=2)}\n\nReturn only a JSON object with the appropriate tokens."
            response = model.generate_content(full_prompt)
            
            # Parse JSON response
            try:
                response_text = response.text.strip()
                # Clean up if wrapped in markdown
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                token_dict = json.loads(response_text)
                tokens = ' '.join(token_dict.values())
                return tokens
            except json.JSONDecodeError:
                return response.text.strip()
    
    def _create_system_prompt(self, token_config: List[str]) -> str:
        """Deprecated - kept for compatibility"""
        return f"""You are a specialized assistant that converts natural language descriptions of plasmids into special tokens.

Available tokens: {', '.join(token_config[:100])}

Your task is to analyze the user's description and output ONLY the appropriate special tokens in sequence.
Do not include any explanation, just the tokens separated by spaces.

Output format: <token1> <token2> <token3> ..."""


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider with structured output"""
    
    def __init__(self):
        self.client = None
    
    def is_available(self) -> bool:
        return os.environ.get("OPENAI_API_KEY") is not None
    
    def convert_to_tokens(self, prompt: str, token_config: List[str]) -> str:
        if self.client is None:
            import openai
            self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Create structured output schema
        schema = self.create_token_schema(token_config)
        
        system_prompt = """You are a specialized assistant that converts natural language descriptions of plasmids into condition tokens.

Analyze the user's description and return a JSON object with the appropriate tokens for each relevant category.
Only include categories that are mentioned or clearly implied in the description."""
        
        # Use OpenAI's structured output feature
        response = self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "plasmid_tokens",
                    "strict": True,
                    "schema": schema
                }
            },
            max_tokens=1024,
            temperature=0.7
        )
        
        # Parse JSON response and extract tokens
        try:
            token_dict = json.loads(response.choices[0].message.content)
            tokens = ' '.join(token_dict.values())
            return tokens
        except json.JSONDecodeError:
            # Fallback
            return response.choices[0].message.content.strip()
    
    def _create_system_prompt(self, token_config: List[str]) -> str:
        return f"""You are a specialized assistant that converts natural language descriptions of plasmids into special tokens.

Available tokens: {', '.join(token_config[:100])}

Your task is to analyze the user's description and output ONLY the appropriate special tokens in sequence.
Do not include any explanation, just the tokens separated by spaces.

Common token categories:
- GC content: <gc_content_low>, <gc_content_medium>, <gc_content_high>
- Copy number: <copy_number_low>, <copy_number_medium>, <copy_number_high>
- Plasmid type: <plasmid_type_expression>, <plasmid_type_cloning>, <plasmid_type_shuttle>
- Resistance markers: <resistance_ampicillin>, <resistance_kanamycin>, <resistance_chloramphenicol>
- Origins: <origin_pBR322>, <origin_pUC>, <origin_ColE1>
- Promoters: <promoter_T7>, <promoter_lac>, <promoter_tac>

Output format: <token1> <token2> <token3> ..."""


class LLMProviderManager:
    """Manages multiple LLM providers with automatic fallback"""
    
    def __init__(self):
        self.providers = [
            AnthropicProvider(),
            GeminiProvider(),
            OpenAIProvider()
        ]
        self.active_provider: Optional[LLMProvider] = None
    
    def get_available_provider(self) -> Optional[LLMProvider]:
        """Get the first available provider"""
        if self.active_provider and self.active_provider.is_available():
            return self.active_provider
        
        for provider in self.providers:
            if provider.is_available():
                self.active_provider = provider
                return provider
        
        return None
    
    def convert_to_tokens(self, prompt: str, token_config: List[str]) -> str:
        """Convert prompt to tokens using the first available provider"""
        provider = self.get_available_provider()
        
        if provider is None:
            raise ValueError(
                "No LLM provider available. Please set at least one API key: "
                "ANTHROPIC_API_KEY, GOOGLE_API_KEY, or OPENAI_API_KEY"
            )
        
        try:
            return provider.convert_to_tokens(prompt, token_config)
        except Exception as e:
            # Try next provider
            self.active_provider = None
            next_provider = self.get_available_provider()
            if next_provider and next_provider != provider:
                return next_provider.convert_to_tokens(prompt, token_config)
            raise e
