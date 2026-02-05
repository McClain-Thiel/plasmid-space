# Quick Start Guide

Get your Plasmid-GPT demo running in minutes!

## Option 1: Deploy to HuggingFace Spaces (Recommended)

This is the easiest way to get started - no local setup required!

### Steps:

1. **Create a HuggingFace account** at https://huggingface.co if you don't have one

2. **Get an API key** from one of these providers:
   - [Anthropic Claude](https://console.anthropic.com/) (Recommended - cheapest and fastest)
   - [Google Gemini](https://ai.google.dev/)
   - [OpenAI](https://platform.openai.com/)

3. **Create a new Space**:
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `plasmid-gpt-demo`
   - SDK: Gradio
   - Hardware: CPU Basic (free tier works!)

4. **Upload files**:
   - Drag and drop all files from this directory to your Space
   - Or use git: `git push` to your Space repository

5. **Add API key as secret**:
   - In Space settings → "Repository secrets"
   - Add `ANTHROPIC_API_KEY` (or `GOOGLE_API_KEY` or `OPENAI_API_KEY`)

6. **Wait for build** (5-10 minutes)

7. **Test it!** Visit your Space URL

## Option 2: Run Locally

### Prerequisites:
- Python 3.9 or higher
- pip

### Steps:

```bash
# Clone or navigate to this directory
cd plasmid-space

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"
# OR
export GOOGLE_API_KEY="your-key-here"
# OR
export OPENAI_API_KEY="your-key-here"

# Run the app
python app.py
```

Open http://localhost:7860 in your browser.

## Test Without Full Setup

Want to test individual components without running the full model?

```bash
# Edit test_local.py and add your API key at the top
# Then run:
python test_local.py
```

This tests:
- Token configuration loading
- Sequence analysis
- Feature detection
- ORF detection
- LLM provider connectivity

## Example Prompts to Try

Once running, try these prompts:

### Expression Plasmids
- "Create a high copy number expression plasmid with a T7 promoter for E. coli protein production"
- "I need an expression vector with a His tag for protein purification"
- "Design a mammalian expression plasmid with CMV promoter"

### Cloning Vectors
- "Generate a low copy cloning vector with ampicillin resistance and a multiple cloning site"
- "Create a cloning plasmid with blue-white screening capability"

### Shuttle Vectors
- "Design a shuttle vector that works in both E. coli and yeast"
- "Create a binary vector for plant transformation"

### Specific Features
- "Generate a plasmid with kanamycin resistance, lac promoter, and high GC content"
- "Create a low copy plasmid with a tetracycline resistance marker"

## Troubleshooting

### "No LLM provider available"
- Make sure you've set at least one API key as an environment variable or Space secret

### "Error generating plasmid"
- Check that your model names are correct: `McClain/plasmid-gpt-244m` or `McClain/plasmid-gpt-319m`
- If running locally, ensure you have enough RAM (at least 4GB free)
- Try the smaller 244m model first

### "plasmid-kit" errors
- The app has fallback annotation methods, so this is usually not critical
- If you see annotation errors, the app will use pattern-based annotation instead

### Slow generation
- Use the 244m model for faster inference
- Consider upgrading to GPU hardware on HuggingFace Spaces
- Reduce `max_length` parameter in the UI

## Next Steps

Once you have it running:

1. **Customize tokens**: Edit `token_config.json` to match your model's actual tokenizer
2. **Adjust parameters**: Modify temperature, top_p in `app.py` for different generation behavior
3. **Improve visualization**: Customize colors and layout in the visualization functions
4. **Add more features**: Extend `utils.py` with additional analysis functions

## Getting Help

- Check `DEPLOYMENT.md` for detailed deployment instructions
- Review code comments in `app.py`, `llm_providers.py`, and `utils.py`
- Look at example outputs in the test script

## Tips for Best Results

1. **Be specific in prompts**: "high copy expression plasmid with T7 promoter" works better than "plasmid"
2. **Use the 319m model**: For more accurate results (but slower)
3. **Adjust max length**: Longer sequences take more time but may be more complete
4. **Check the annotations**: Verify the generated plasmid has expected features

Enjoy generating plasmids! 🧬
