import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Global cache to prevent reloading heavy models
MODEL_CACHE = {}

def get_model_and_tokenizer(model_name: str):
    if model_name in MODEL_CACHE:
        return MODEL_CACHE[model_name]
    
    print(f"Loading model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
    
    # Move to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Mac M1/M2 Metal acceleration
    if torch.backends.mps.is_available():
        device = "mps"
        
    model.to(device)
    
    MODEL_CACHE[model_name] = (model, tokenizer, device)
    return model, tokenizer, device

def generate_plasmid(token_string: str, model_choice: str = "McClain/plasmid-gpt-244m") -> str:
    """
    Generates a plasmid sequence from the given special tokens.
    """
    try:
        model, tokenizer, device = get_model_and_tokenizer(model_choice)
        
        # tokenize input
        inputs = tokenizer(token_string, return_tensors="pt").to(device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs, 
                max_length=2048, # Adjust as needed
                do_sample=True,
                temperature=0.8,
                top_p=0.95
            )
            
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up result - sometimes prompts repeat or have artifacts
        # We assume the model outputs pure DNA sequence after the tokens, or we need to extract it.
        # For this demo, let's assume the output is the sequence.
        
        return generated_text
        
    except Exception as e:
        return f"Error during generation: {str(e)}"
