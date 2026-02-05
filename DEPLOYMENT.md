# Deployment Guide

This guide will help you deploy the Plasmid-GPT demo to HuggingFace Spaces.

## Prerequisites

1. A HuggingFace account
2. At least one API key for:
   - Anthropic Claude (recommended - fast and cheap)
   - Google Gemini
   - OpenAI

## Step 1: Create a New Space

1. Go to [HuggingFace Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose:
   - Space name: `plasmid-gpt-demo` (or your preferred name)
   - License: MIT
   - SDK: Gradio
   - Hardware: CPU Basic (free) or GPU if you want faster inference

## Step 2: Upload Files

Upload all files from this directory to your Space:
- `app.py` - Main application
- `llm_providers.py` - LLM provider implementations
- `utils.py` - Utility functions
- `requirements.txt` - Python dependencies
- `token_config.json` - Token configuration
- `README.md` - Space description

## Step 3: Configure Secrets

In your Space settings, add the API key(s) as secrets:

1. Go to your Space settings
2. Click on "Settings" → "Repository secrets"
3. Add at least one of:
   - `ANTHROPIC_API_KEY` (recommended)
   - `GOOGLE_API_KEY`
   - `OPENAI_API_KEY`

## Step 4: Wait for Build

The Space will automatically build and deploy. This may take 5-10 minutes on first deployment.

## Step 5: Test

Once deployed, test the Space with example prompts:
- "I need a high copy expression plasmid for E. coli"
- "Design a cloning vector with ampicillin resistance"
- "Create a shuttle vector for yeast and bacteria"

## Customization

### Update Token Configuration

Edit `token_config.json` to add or modify special tokens based on your model's actual tokenizer.

### Adjust Model Parameters

In `app.py`, you can adjust:
- `temperature` - Controls randomness (0.1-1.0)
- `top_p` - Nucleus sampling parameter
- `max_length` - Maximum sequence length

### Modify Visualization

The plasmid visualization in `app.py` can be customized:
- Colors for different feature types
- Radius for annotations
- Size and layout

## Troubleshooting

### Model Not Loading

If the model fails to load:
1. Check you have enough RAM/VRAM (upgrade Space hardware)
2. Verify model names are correct: `McClain/plasmid-gpt-244m` or `McClain/plasmid-gpt-319m`

### LLM API Errors

If natural language conversion fails:
1. Verify API keys are set correctly
2. Check API rate limits
3. Try a different provider (they have fallback logic)

### Annotation Issues

If plasmid-kit fails:
- The app will fallback to pattern-based annotation
- This is less accurate but still functional

### Generation Quality

To improve generation:
1. Adjust temperature (lower = more deterministic)
2. Provide more specific prompts
3. Use the larger 319m model

## Performance Tips

1. **Use CPU Basic for testing** - It's free and sufficient for demos
2. **Upgrade to GPU** - For faster inference with the larger model
3. **Cache models** - Models are cached after first load
4. **Limit concurrent users** - Free tier has usage limits

## Support

For issues or questions:
- Check the [HuggingFace Spaces documentation](https://huggingface.co/docs/hub/spaces)
- Review the Gradio [documentation](https://gradio.app/docs/)
- Open an issue on your Space repository

## Example Space Configuration

Your Space should have these settings in the README.md front matter:

```yaml
---
title: Plasmid-GPT Demo
emoji: 🧬
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---
```

## Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export ANTHROPIC_API_KEY="your-key"

# Run the app
python app.py
```

Then open http://localhost:7860 in your browser.

You can also run the test script:

```bash
python test_local.py
```

This will test individual components without requiring the full model.
