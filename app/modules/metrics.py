def calculate_gc_content(sequence: str) -> float:
    """Calculates GC content percentage of a DNA sequence."""
    if not sequence:
        return 0.0
    g = sequence.count('G') + sequence.count('g')
    c = sequence.count('C') + sequence.count('c')
    return (g + c) / len(sequence) * 100

def classify_gc_content(gc_percent: float) -> str:
    """Classifies GC content as Low, Medium, or High."""
    if gc_percent < 40:
        return "Low (<40%)"
    elif gc_percent > 55:
        return "High (>55%)"
    else:
        return "Medium (40-55%)"

def calculate_metrics(sequence: str) -> dict:
    """Calculates basic metrics for a plasmid sequence."""
    gc = calculate_gc_content(sequence)
    classification = classify_gc_content(gc)
    length = len(sequence)
    
    return {
        "Length (bp)": length,
        "GC Content": f"{gc:.1f}%",
        "GC Classification": classification
    }
