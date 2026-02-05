# Generation Parameters Fixed 🔧

## Problem

You reported:
1. **Always 500 bp output** - regardless of settings
2. **Poor performance** - not generating good plasmids

## Root Causes

### 1. Hardcoded Token Limit ❌

**Line 112 in `app.py`:**
```python
max_new_tokens=min(max_length, 500),  # ← Hardcoded to 500!
```

This limited generation to **500 nucleotides maximum**, even if the slider was set to 4096!

Since each nucleotide (A, T, G, C) is one token in your model, `max_new_tokens=500` means maximum 500 bp.

### 2. Suboptimal Sampling Parameters

Missing some important parameters for sequence generation:
- No `top_p` (nucleus sampling)
- No `no_repeat_ngram_size` (prevents repetitive sequences)

## Solution

### Updated Generation Parameters

```python
outputs = model.generate(
    inputs["input_ids"],
    max_new_tokens=max_length,           # ✅ Now uses user's slider value
    do_sample=True,                       # Sampling enabled
    temperature=0.85,                     # Per model card
    top_k=50,                             # Per model card
    top_p=0.95,                          # ✅ Added: nucleus sampling
    repetition_penalty=1.15,             # Per model card
    no_repeat_ngram_size=15,             # ✅ Added: prevent 15-mer repeats
    pad_token_id=tokenizer.pad_token_id,
    eos_token_id=tokenizer.eos_token_id,
)
```

### Updated UI Slider

**Before:**
```python
minimum=512, maximum=4096, value=2048
```

**After:**
```python
minimum=1000,      # More reasonable minimum for plasmids
maximum=10000,     # Allow larger plasmids (up to 10 kb)
value=5000,        # Better default (typical plasmid size)
step=500,          # Larger steps for easier selection
info="Typical plasmids: 2-8 kb. Longer = more features but slower generation."
```

## Parameter Explanations

### Core Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `max_new_tokens` | `max_length` | Maximum nucleotides to generate (1-10k bp) |
| `temperature` | `0.85` | Controls randomness (0.7-0.9 recommended) |
| `top_k` | `50` | Only sample from top 50 most likely tokens |
| `top_p` | `0.95` | Nucleus sampling - cumulative probability cutoff |
| `repetition_penalty` | `1.15` | Penalize repeated tokens (prevents loops) |
| `no_repeat_ngram_size` | `15` | Prevent exact 15-nucleotide repeats |

### What Each Does

**`temperature=0.85`**
- Controls randomness in sampling
- Lower (0.7): More deterministic, conservative
- Higher (1.0): More random, diverse
- 0.85 is a good balance for biological sequences

**`top_k=50`**
- Only considers the 50 most likely next tokens
- Prevents sampling very unlikely nucleotides
- Recommended by model card

**`top_p=0.95`** (NEW!)
- Nucleus sampling: only consider tokens in top 95% probability mass
- More dynamic than top_k
- Helps generate more natural sequences

**`repetition_penalty=1.15`**
- Penalizes tokens that have appeared recently
- Prevents: `ATGATGATGATGATGATG...` (repetitive patterns)
- Value > 1.0 = discourage repeats

**`no_repeat_ngram_size=15`** (NEW!)
- Prevents exact 15-nucleotide repeats from occurring
- Helps avoid homopolymer runs: `AAAAAAAAAAAAAAAA...`
- Important for realistic plasmid sequences

## Expected Behavior Now

### Small Plasmids (1-3 kb)
- **Use case:** Simple cloning vectors, minimal plasmids
- **Generation time:** ~10-30 seconds
- **Set slider:** 1000-3000 bp

### Medium Plasmids (3-6 kb)
- **Use case:** Expression vectors, standard plasmids
- **Generation time:** ~30-60 seconds
- **Set slider:** 3000-6000 bp (default: 5000)

### Large Plasmids (6-10 kb)
- **Use case:** Complex multi-feature plasmids, BACs
- **Generation time:** ~1-3 minutes
- **Set slider:** 6000-10000 bp

## Performance Tips

### For Faster Generation:
1. Use the **244m model** (smaller, faster)
2. Set slider to **3000-5000 bp**
3. Lower temperature to **0.75** (more deterministic)

### For Better Quality:
1. Use the **319m model** (larger, more accurate)
2. Set slider to **5000-8000 bp** (more realistic size)
3. Keep default parameters (0.85 temp, top_k=50)

### For Specific Features:
Make sure your prompt includes specific details:
```
"Create a 5kb expression plasmid for E. coli with:
- T7 promoter
- Ampicillin resistance  
- His tag
- High copy number"
```

The more specific, the better the conditioning tokens and generated sequence.

## Troubleshooting

### Still getting short sequences?
- Check the slider value (should be 1000-10000)
- Check console output for errors
- Model might be hitting `<EOS>` token early

### Getting repetitive sequences?
- Increase `repetition_penalty` to 1.2
- Increase `no_repeat_ngram_size` to 20
- Lower `temperature` to 0.8

### Generation too slow?
- Use 244m model instead of 319m
- Lower max_length to 3000-5000
- Consider using GPU if available

### Not enough features?
- Generate longer sequences (5-8 kb)
- Use more specific condition tokens
- Check plasmid-kit is working (`bootstrap_data()`)

## Testing

After the fix, test with:

```bash
python app.py
```

Try these prompts:
1. "Small 2kb cloning vector with ampicillin resistance" → Should generate ~2000 bp
2. "5kb expression plasmid for E. coli" → Should generate ~5000 bp (default)
3. "Large 8kb shuttle vector" → Should generate ~8000 bp

**Check the console output** for generation statistics:
```
Generated sequence length: XXXX bp
plasmid-kit found N features:
  rep_origin: X
  marker: Y
  ...
```

## Summary of Changes

✅ **Removed 500-token hardcoded limit**  
✅ **Added `top_p=0.95` for better diversity**  
✅ **Added `no_repeat_ngram_size=15` to prevent repetition**  
✅ **Increased slider range to 1000-10000 bp**  
✅ **Better default (5000 bp) and step size (500)**  
✅ **Added helpful info text to slider**

Now your plasmids should generate at the requested length with better quality! 🧬✨
