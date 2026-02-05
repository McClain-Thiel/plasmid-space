# Deploy to HuggingFace Spaces (Private)

This guide will help you deploy the Plasmid-GPT demo to a **private** HuggingFace Space.

✅ **Your Space**: https://huggingface.co/spaces/McClain/plasmid-space

## Prerequisites

1. ✅ HuggingFace account (McClain)
2. ✅ Git installed and configured
3. ✅ Space created: McClain/plasmid-space with GPU Zero
4. HuggingFace CLI installed (optional but recommended)

## Option 1: Deploy via HuggingFace Web UI (Easiest)

### Step 1: Create a New Space

1. Go to https://huggingface.co/new-space
2. Fill in the details:
   - **Space name**: `plasmid-gpt-demo` (or your preferred name)
   - **License**: MIT
   - **Select SDK**: Gradio
   - **SDK version**: 4.0.0
   - **Space hardware**: CPU basic (free) or upgrade to GPU if needed
   - **Visibility**: ⚠️ **Select "Private"** to make it private
3. Click "Create Space"

### Step 2: Set up Environment Secrets

Before pushing code, set up your API keys:

1. In your new Space, click on **Settings** tab
2. Scroll down to **Repository secrets**
3. Add these secrets (click "+ Add secret"):
   - **Name**: `ANTHROPIC_API_KEY`
     - **Value**: Your Anthropic API key (get from https://console.anthropic.com/)
   - **Name**: `GOOGLE_API_KEY` (optional)
     - **Value**: Your Google API key (get from https://aistudio.google.com/app/apikey)
   - **Name**: `OPENAI_API_KEY` (optional)
     - **Value**: Your OpenAI API key (get from https://platform.openai.com/)

> **Note**: Only `ANTHROPIC_API_KEY` is required. The others are optional fallbacks.

### Step 3: Clone the Space Repository

```bash
# Clone your new Space (replace YOUR_USERNAME with your HF username)
git clone https://huggingface.co/spaces/YOUR_USERNAME/plasmid-gpt-demo
cd plasmid-gpt-demo
```

### Step 4: Copy Files to Space

```bash
# Copy all necessary files from your local plasmid-space directory
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/app.py .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/requirements.txt .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/README.md .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/llm_providers.py .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/plasmid_tokenizer.py .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/utils.py .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/token_config.json .
cp /Users/mcclainthiel/Projects/PhD/plasmid-space/LICENSE .
```

### Step 5: Commit and Push

```bash
git add .
git commit -m "Initial deployment of Plasmid-GPT demo"
git push
```

Your Space will automatically build and deploy! 🚀

---

## Option 2: Deploy via Git Remote (Faster)

If you're already in your `plasmid-space` directory, you can add HuggingFace as a remote:

### Step 1: Create the Space on HuggingFace

1. Go to https://huggingface.co/new-space
2. Create a new **Private** Space named `plasmid-gpt-demo`
3. Set up API key secrets as described in Option 1, Step 2

### Step 2: Add HuggingFace Remote

```bash
cd /Users/mcclainthiel/Projects/PhD/plasmid-space

# Add HuggingFace as a remote (replace YOUR_USERNAME)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/plasmid-gpt-demo
```

### Step 3: Commit Current Changes

```bash
# Stage the updated README (now with private: true)
git add README.md app.py

# Commit your changes
git commit -m "Update for HuggingFace Spaces deployment (private)"
```

### Step 4: Push to HuggingFace

```bash
# Push to HuggingFace Spaces
git push hf main
```

If you get an authentication error, you may need to use a HuggingFace token:

```bash
# Get your token from https://huggingface.co/settings/tokens
# Then push with:
git push https://YOUR_USERNAME:YOUR_HF_TOKEN@huggingface.co/spaces/YOUR_USERNAME/plasmid-gpt-demo main
```

---

## Option 3: Using HuggingFace CLI (Recommended for Power Users)

### Step 1: Install HuggingFace CLI

```bash
pip install huggingface_hub[cli]
```

### Step 2: Login to HuggingFace

```bash
huggingface-cli login
```

Enter your HuggingFace token when prompted.

### Step 3: Create and Push

```bash
cd /Users/mcclainthiel/Projects/PhD/plasmid-space

# Create a private space
huggingface-cli repo create plasmid-gpt-demo --type space --space_sdk gradio --private

# Push to the space
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/plasmid-gpt-demo
git add README.md app.py
git commit -m "Deploy to HuggingFace Spaces"
git push hf main
```

---

## Post-Deployment

### 1. Verify Secrets are Set

Go to your Space settings and ensure all API keys are properly configured.

### 2. Monitor Build Logs

Click on the **"App"** tab to see build logs. The Space will:
- Install dependencies from `requirements.txt` (~5-10 minutes)
- Download model weights on first run (~2-3 GB total)
- Start the Gradio interface

### 3. Test the Space

Once built, test with a simple prompt like:
> "Create a high copy expression plasmid for E. coli with ampicillin resistance"

### 4. Share with Collaborators

Since the Space is private, you can add collaborators:
1. Go to Space Settings
2. Scroll to **"Collaborators"**
3. Add HuggingFace usernames

---

## Troubleshooting

### Build Fails

**Check logs in the App tab.** Common issues:
- Missing dependencies: Make sure `requirements.txt` is complete
- API key issues: Verify secrets are set correctly
- Memory issues: Consider upgrading to GPU hardware

### Models Not Loading

The models (~980 MB and ~1.3 GB) will download on first run. This is normal and may take a few minutes.

### API Key Errors

If you see "API key not found":
1. Go to Space Settings → Repository secrets
2. Add `ANTHROPIC_API_KEY` with your key
3. Restart the Space (Settings → Factory reboot)

### Private Space Not Loading

Make sure you're logged into HuggingFace when accessing the Space URL.

---

## Important Files for Deployment

These files MUST be in your Space:

- ✅ `app.py` - Main Gradio application
- ✅ `requirements.txt` - Python dependencies
- ✅ `README.md` - Space configuration (with `private: true`)
- ✅ `llm_providers.py` - LLM integration
- ✅ `plasmid_tokenizer.py` - Custom tokenizer
- ✅ `utils.py` - Utility functions
- ✅ `token_config.json` - Token configuration
- ✅ `LICENSE` - MIT license

Optional:
- `QUICK_START.md` - Documentation
- `SUMMARY.md` - Project summary

---

## Hardware Recommendations

- **CPU Basic (Free)**: Works but slow (60-120 seconds per generation)
- **CPU Upgrade ($0.03/hour)**: Faster CPU, recommended
- **T4 GPU Small ($0.60/hour)**: Much faster, best for demos
- **A10G GPU ($3.15/hour)**: Overkill for this model size

For a private demo, **CPU Basic is fine** for testing. Upgrade to GPU if you need faster generation times.

---

## Keeping it Private

Your Space is now **private** because we added `private: true` to the README frontmatter. This means:
- Only you (and collaborators you add) can access it
- It won't appear in search results
- The URL is still accessible if someone has it, but they'll need to be logged in with permission

To make it public later:
1. Edit `README.md` and change `private: true` to `private: false`
2. Commit and push the change
3. Or change it in Space Settings → Rename or delete
