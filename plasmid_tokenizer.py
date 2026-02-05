"""
Custom tokenizer for PlasmidGPT models
Based on the model's custom 72-token vocabulary
"""

import json
import re
from typing import List, Dict, Union
from huggingface_hub import hf_hub_download


class PlasmidGPTTokenizer:
    """
    Custom tokenizer for PlasmidGPT models with 72-token vocabulary.
    
    Vocabulary includes:
    - Special tokens: <BOS>, <EOS>, <SEQ>, <UNK>, <PAD>
    - Condition tokens: <HOST:...>, <RESISTANCE:...>, <GC:...>, etc.
    - Nucleotides: A, C, G, T
    """
    
    def __init__(self, vocab_file: str = None, model_name: str = None):
        """
        Initialize tokenizer.
        
        Args:
            vocab_file: Path to vocab.json file
            model_name: HuggingFace model name (will download vocab.json)
        """
        if vocab_file is None and model_name is None:
            raise ValueError("Must provide either vocab_file or model_name")
        
        # Download vocab if needed
        if vocab_file is None:
            print(f"Downloading vocab.json from {model_name}")
            vocab_file = hf_hub_download(repo_id=model_name, filename="vocab.json")
        
        # Load vocabulary
        with open(vocab_file) as f:
            self.vocab = json.load(f)
        
        # Create reverse mapping
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
        # Special tokens
        self.bos_token = "<BOS>"
        self.eos_token = "<EOS>"
        self.pad_token = "<PAD>"
        self.unk_token = "<UNK>"
        self.seq_token = "<SEQ>"
        
        # Token IDs
        self.bos_token_id = self.vocab.get(self.bos_token, 0)
        self.eos_token_id = self.vocab.get(self.eos_token, 2)
        self.pad_token_id = self.vocab.get(self.pad_token, 1)
        self.unk_token_id = self.vocab.get(self.unk_token, 3)
        
        # Pattern for special tokens (condition tokens like <HOST:ECOLI>)
        self.special_token_pattern = re.compile(r'<[A-Z_]+:[A-Z_]+>|<[A-Z]+>')
    
    def __len__(self):
        """Return vocabulary size"""
        return len(self.vocab)
    
    def encode(self, text: str, add_bos: bool = True) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Text to encode (can contain special tokens and nucleotides)
            add_bos: Whether to add <BOS> token at the start
            
        Returns:
            List of token IDs
        """
        tokens = []
        
        if add_bos:
            tokens.append(self.bos_token_id)
        
        # Parse text to extract special tokens and individual characters
        pos = 0
        for match in self.special_token_pattern.finditer(text):
            # Add characters before this match
            for char in text[pos:match.start()]:
                tokens.append(self.vocab.get(char, self.unk_token_id))
            
            # Add the special token
            tokens.append(self.vocab.get(match.group(), self.unk_token_id))
            pos = match.end()
        
        # Add remaining characters
        for char in text[pos:]:
            tokens.append(self.vocab.get(char, self.unk_token_id))
        
        return tokens
    
    def decode(self, token_ids: List[int], skip_special_tokens: bool = False) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: List of token IDs
            skip_special_tokens: Whether to skip special tokens in output
            
        Returns:
            Decoded text
        """
        tokens = []
        
        for token_id in token_ids:
            token = self.id_to_token.get(token_id, self.unk_token)
            
            if skip_special_tokens:
                # Skip special control tokens but keep condition tokens
                if token in [self.bos_token, self.eos_token, self.pad_token, self.unk_token]:
                    continue
            
            tokens.append(token)
        
        return "".join(tokens)
    
    def __call__(self, text: Union[str, List[str]], 
                 return_tensors: str = None,
                 padding: bool = False,
                 add_bos: bool = True) -> Dict:
        """
        Tokenize text (compatible with transformers API).
        
        Args:
            text: Text or list of texts to tokenize
            return_tensors: "pt" for PyTorch tensors, None for lists
            padding: Whether to pad sequences (not implemented)
            add_bos: Whether to add <BOS> token
            
        Returns:
            Dictionary with input_ids and attention_mask
        """
        # Handle single text or batch
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        # Encode all texts
        input_ids = [self.encode(t, add_bos=add_bos) for t in texts]
        
        # Create attention masks
        attention_mask = [[1] * len(ids) for ids in input_ids]
        
        # Convert to tensors if requested
        if return_tensors == "pt":
            import torch
            input_ids = torch.tensor(input_ids)
            attention_mask = torch.tensor(attention_mask)
        
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
    
    def batch_decode(self, token_ids_batch: List[List[int]], 
                     skip_special_tokens: bool = False) -> List[str]:
        """
        Decode batch of token ID sequences.
        
        Args:
            token_ids_batch: List of token ID sequences
            skip_special_tokens: Whether to skip special tokens
            
        Returns:
            List of decoded texts
        """
        return [self.decode(ids, skip_special_tokens) for ids in token_ids_batch]
    
    @classmethod
    def from_pretrained(cls, model_name: str):
        """
        Load tokenizer from HuggingFace model.
        
        Args:
            model_name: HuggingFace model name
            
        Returns:
            PlasmidGPTTokenizer instance
        """
        return cls(model_name=model_name)
    
    def get_vocab(self) -> Dict[str, int]:
        """Return vocabulary dictionary"""
        return self.vocab.copy()
    
    def get_condition_tokens(self) -> List[str]:
        """Get all condition tokens from vocabulary"""
        return [token for token in self.vocab.keys() 
                if token.startswith('<') and ':' in token]
    
    def get_special_tokens(self) -> List[str]:
        """Get special control tokens"""
        return [token for token in self.vocab.keys()
                if token.startswith('<') and ':' not in token]
