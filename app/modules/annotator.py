import tempfile
import os
from pathlib import Path
import plasmidkit.api as pk

def annotate_sequence(sequence: str):
    """
    Annotates a DNA sequence using plasmid-kit.
    Returns:
        tuple: (list of annotations, analysis dict)
    """
    if not sequence:
        return [], {}

    # PlasmidKit expects a file or SeqRecord. Writing to temp file is safest.
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as tmp:
        tmp.write(f">generated_plasmid\n{sequence}")
        tmp_path = tmp.name

    try:
        # Run analysis
        # We use the default database "engineered-core@1.0.0" which should be downloaded by plasmid-kit automatically
        # or we might need to bootstrap it.
        result = pk.analyze(Path(tmp_path), is_sequence=True)
        
        # Cleanup
        os.unlink(tmp_path)
        
        return result.get('annotations', []), result
        
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        print(f"Annotation error: {e}")
        return [], {"error": str(e)}
