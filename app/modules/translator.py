import os
import openai
from openai import OpenAI

def translate_prompt(user_prompt: str, model_version: str = "244m") -> str:
    """
    Translates a natural language prompt into special tokens for the plasmid-gpt model.
    Uses OpenAI GPT-4o-mini (or similar) to map constraints.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OPENAI_API_KEY not found in environment variables."

    client = OpenAI(api_key=api_key)

    # Conceptual mapping logic - in a real scenario we'd feed the schema of valid tokens
    # For now, we instruct the LLM to output specific tokens based on knowledge or examples.
    # We assume the user wants standard plasmid parts.
    
    system_prompt = f"""You are an expert synthetic biologist and AI engineer. 
Your task is to convert natural language descriptions of plasmids into a sequence of special control tokens for the plasmid-gpt model.
The model `{model_version}` expects tokens that describe features like origin of replication, resistance markers, etc.

Valid token examples (conceptual):
<start>
<origin_high_copy>
<amp_resistance>
<promoter_strong>
<end>
... (and so on)

INSTRUCTIONS:
1. Analyze the user's request.
2. Select appropriate special tokens.
3. Output ONLY the string of special tokens separated by spaces.
4. Do not include markdown or explanations.

Example User Input: "A high copy plasmid with ampicillin resistance"
Example Output: "<start> <origin_high_copy> <amp_resistance> <end>"

(Note: Since I don't have the exact token vocabulary of plasmid-gpt loaded, generate plausible tokens that fit the user's intent. The downstream model will try to interpret them or we can map them.)
""" 
    # NOTE: In a production app, we would load the tokenizer and valid vocab to constrain generations.

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using a fast, smart model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI: {str(e)}"
