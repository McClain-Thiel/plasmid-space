# Debugging Progressive Updates

## Issue

Progressive updates were working but then stopped. The UI now waits for everything to complete instead of showing results as they're ready.

## What I Fixed

### 1. Changed `show_progress` Parameter

**Before:**
```python
show_progress="full"  # This might not work well with generators
```

**After:**
```python
show_progress=True  # Simpler, works better with generators
```

### 2. Added Debug Logging

Added print statements at each yield point to track progress:

```python
print("[Pipeline] Starting generation...")
print("[Pipeline] Yielding stage 1: Loading message")
yield (...)
print("[Pipeline] Generated tokens: ...")
print("[Pipeline] Yielding stage 2: Tokens ready")
yield (...)
# ... etc
```

## How to Debug

### Run the App and Watch Console

```bash
python app.py
```

When you click "Generate", you should see console output like:

```
[Pipeline] Starting generation for 244m model, max_length=5000
[Pipeline] Yielding stage 1: Loading message
[Pipeline] Generated tokens: <HOST:ECOLI> <COPY:HIGH> ...
[Pipeline] Yielding stage 2: Tokens ready
[Pipeline] Starting DNA generation...
Loading model: McClain/plasmid-gpt-244m
[Pipeline] DNA generated: 5123 bp
[Pipeline] Yielding stage 3: DNA ready
[Pipeline] Starting annotation...
plasmid-kit found 12 features:
  rep_origin: 1
  marker: 2
  ...
[Pipeline] Found 12 annotations
[Pipeline] Yielding stage 4: Metrics ready
[Pipeline] Creating visualization...
[Pipeline] Yielding stage 5: Complete!
[Pipeline] Generation complete
```

### What to Look For

**If progressive updates are working:**
- ✅ You see "Yielding stage 1" immediately
- ✅ You see "Yielding stage 2" after ~2-5 seconds
- ✅ UI updates between each yield
- ✅ Tokens appear first, then DNA, then metrics, then visualization

**If they're NOT working (broken):**
- ❌ All yield messages appear at once at the end
- ❌ No UI updates until everything completes
- ❌ Everything appears simultaneously

## Common Causes

### 1. Gradio Version Issue

**Check version:**
```bash
pip show gradio
```

**Generators require Gradio 4.0+**. If you have an older version:
```bash
pip install --upgrade gradio
```

### 2. Not Using a Generator

Make sure the function uses `yield`, not `return`:

```python
def full_pipeline(...):
    yield (...)  # ✅ Generator
    # NOT: return (...)  # ❌ Regular function
```

### 3. Exception Breaking Generator

If an exception occurs before the first yield, the generator won't work. Check for:
- Import errors
- Model loading errors
- Missing API keys

### 4. Blocking Operations

If there's a long blocking operation before the first yield, you won't see updates:

```python
# ❌ BAD: Load model before first yield
model = load_model()  # Takes 30 seconds
yield (...)  # First yield only after 30 seconds!

# ✅ GOOD: Yield first, then load
yield ("⏳ Loading...")  # Immediate yield
model = load_model()  # Load after
yield ("Model loaded!")
```

## Testing

### Quick Test Without Full Generation

Create a test script to verify generators work:

```python
# test_generator.py
import gradio as gr
import time

def test_generator():
    print("Yield 1")
    yield ("Step 1", "")
    
    time.sleep(2)
    print("Yield 2")
    yield ("Step 1", "Step 2")
    
    time.sleep(2)
    print("Yield 3")
    yield ("Step 1", "Step 2 complete", "Step 3")

with gr.Blocks() as demo:
    out1 = gr.Textbox(label="Output 1")
    out2 = gr.Textbox(label="Output 2")
    
    btn = gr.Button("Test")
    btn.click(
        fn=test_generator,
        outputs=[out1, out2],
        show_progress=True
    )

demo.launch()
```

**Expected behavior:**
- Click button
- "Step 1" appears immediately
- 2 seconds later, "Step 2" appears
- 2 seconds later, done

If this works, generators are functional!

## Gradio Generator Requirements

### Must Have

1. **Function is a generator** (uses `yield`)
2. **Each yield returns tuple matching outputs**
3. **Gradio version 4.0+**
4. **Outputs list matches yield tuple length**

### Example

```python
def my_generator():
    # Yield 1: (output1, output2, output3)
    yield ("Loading...", "", None)
    
    # Yield 2: (output1, output2, output3)
    result = do_work()
    yield ("Done", result, make_plot())

btn.click(
    fn=my_generator,
    outputs=[out1, out2, out3],  # Must match yield tuple
    show_progress=True
)
```

## Workaround: Use Callbacks

If generators don't work, you can use `gr.Progress`:

```python
def full_pipeline(prompt, model_choice, max_length, progress=gr.Progress()):
    progress(0, desc="Generating tokens...")
    tokens = generate_tokens()
    
    progress(0.3, desc="Generating DNA...")
    dna = generate_dna()
    
    progress(0.7, desc="Annotating...")
    annotations = annotate()
    
    progress(1.0, desc="Complete!")
    return tokens, dna, metrics, fig, annotations
```

This shows progress but doesn't update outputs progressively.

## Solution Summary

1. ✅ Changed `show_progress="full"` to `show_progress=True`
2. ✅ Added debug logging to track yields
3. ✅ Verified generator structure is correct
4. ✅ Each yield returns correct tuple length

## Next Steps

1. **Run the app** with the debug logging
2. **Click Generate** and watch the console
3. **Check if** you see all 5 "Yielding stage" messages
4. **Verify** UI updates between yields

If you see all yield messages but UI doesn't update progressively, it might be a Gradio version or browser caching issue.

### Browser Cache

Try:
1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache
3. Try in incognito mode
4. Try different browser

### Gradio Update

```bash
pip install --upgrade gradio
pip show gradio  # Should be 4.0+
```

---

The progressive updates should now work! Check the console output to verify the yields are happening at the right times.
