# Bug Fixes Applied

## Issues Fixed

### 1. ✅ Gradio 6.0 Compatibility Warning
**Error:**
```
UserWarning: The parameters have been moved from the Blocks constructor to the launch() method in Gradio 6.0: theme
```

**Fix:**
- Moved `theme=gr.themes.Soft()` from `gr.Blocks()` to `demo.launch()`
- Updated in `app.py` lines 303 and 382

**Before:**
```python
with gr.Blocks(title="Plasmid-GPT Demo", theme=gr.themes.Soft()) as demo:
    ...
if __name__ == "__main__":
    demo.launch()
```

**After:**
```python
with gr.Blocks(title="Plasmid-GPT Demo") as demo:
    ...
if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
```

---

### 2. ✅ Google Generative AI Deprecation
**Warning:**
```
FutureWarning: All support for the `google.generativeai` package has ended.
Please switch to the `google.genai` package.
```

**Fix:**
- Updated `llm_providers.py` to use the new `google.genai` package
- Added fallback to deprecated package if new one not available
- Updated model name to `gemini-2.0-flash-exp` (latest)
- Updated `requirements.txt` to use `google-genai>=0.2.0`

**Code Changes:**
```python
# Now tries new API first, falls back to old API
try:
    from google import genai
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
    self.use_new_api = True
except (ImportError, AttributeError):
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
    self.use_new_api = False
```

---

### 3. ✅ Tokenizer Vocab/Merges Error
**Error:**
```
Error generating plasmid: `vocab` and `merges` must be both be from memory or both filenames
```

**Root Cause:**
This error occurs when the fast tokenizer has issues with vocab/merges file loading. Common with custom or older model tokenizers.

**Fix:**
- Added `use_fast=False` to tokenizer loading (uses slower but more reliable tokenizer)
- Added `trust_remote_code=True` for custom tokenizers
- Added fallback to `use_fast=True` if slow tokenizer fails
- Added better error handling and logging

**Code Changes in `app.py`:**
```python
def load_plasmid_model(model_name: str):
    try:
        plasmid_tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            use_fast=False  # Use slow tokenizer to avoid vocab/merges issues
        )
    except Exception as e:
        print(f"Error loading tokenizer with use_fast=False, trying with use_fast=True: {e}")
        plasmid_tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            use_fast=True
        )
```

**Also Added:**
- `sentencepiece>=0.1.99` to requirements.txt (needed for many tokenizers)
- `protobuf>=3.20.0` to requirements.txt (needed for tokenizer serialization)

---

## Updated Files

1. **`app.py`**
   - Fixed Gradio 6.0 theme parameter
   - Fixed tokenizer loading with better error handling

2. **`llm_providers.py`**
   - Updated Gemini provider to use new API
   - Added fallback for backward compatibility

3. **`requirements.txt`**
   - Changed `google-generativeai` to `google-genai`
   - Added `sentencepiece` and `protobuf`

---

## Testing

After these fixes, restart your app:

```bash
# Stop the current app (Ctrl+C)

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart
python app.py
```

You should no longer see:
- ✅ Gradio theme warning
- ✅ Google Generative AI deprecation warning
- ✅ Tokenizer vocab/merges error

---

## If Issues Persist

### Tokenizer Still Failing?

If you still get tokenizer errors, it might be an issue with your model's tokenizer files on HuggingFace. Try:

1. **Check your model's tokenizer files:**
   ```python
   from transformers import AutoTokenizer
   tokenizer = AutoTokenizer.from_pretrained("McClain/plasmid-gpt-244m", use_fast=False)
   print(tokenizer)
   ```

2. **If vocab/merges error persists:**
   - Your model might need a different tokenizer class
   - Check the model's `tokenizer_config.json` on HuggingFace
   - You may need to specify the tokenizer class explicitly:
   ```python
   from transformers import GPT2Tokenizer  # or appropriate class
   tokenizer = GPT2Tokenizer.from_pretrained("McClain/plasmid-gpt-244m")
   ```

3. **Alternative: Use a known-good tokenizer:**
   ```python
   # If your model is GPT-2 based
   tokenizer = AutoTokenizer.from_pretrained("gpt2")
   # Then save and upload to your model repo
   ```

### Google API Still Warning?

If you still see Google warnings:
```bash
# Uninstall old package
pip uninstall google-generativeai -y

# Install new package
pip install google-genai --upgrade
```

---

## Notes

- The slow tokenizer (`use_fast=False`) is more compatible but slightly slower
- For production, test which tokenizer works best with your model
- All changes are backward compatible - old setups should still work
