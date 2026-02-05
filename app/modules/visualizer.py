import matplotlib.pyplot as plt
from dna_features_viewer import CircularGraphicRecord, GraphicFeature

def create_plasmid_map(sequence: str, annotations: list, title: str = "Generated Plasmid"):
    """
    Generates a circular plasmid map image.
    """
    if not sequence:
        return None
        
    features = []
    # Convert plasmid-kit features to dna_features_viewer features
    # PlasmidKit features likely have type, start, end, strand, label/name
    
    # Simple color mapping
    color_map = {
        "promoter": "#ffcccc",
        "terminator": "#ffcccc",
        "rep_origin": "#ffffcc",
        "CDS": "#cce5ff",
        "resistance_marker": "#ffccff",
        "marker": "#ffccff"
    }

    for ann in annotations:
        # Check structure of 'ann' - it might be a dict or object depending on plasmid-kit version
        # Based on api.py it returns a list of Features (objects), but analyze returns dicts in 'annotations' key
        # "annotations": [feature.to_dict() for feature in annotations] -> It is a dict.
        
        ft_type = ann.get('type', 'misc_feature')
        start = ann.get('start', 0)
        end = ann.get('end', 0)
        strand = ann.get('strand', 1)
        label = ann.get('name', ft_type)
        
        color = color_map.get(ft_type, "#e0e0e0")
        
        features.append(GraphicFeature(
            start=start, end=end, strand=strand, color=color, label=label, type=ft_type
        ))

    record = CircularGraphicRecord(sequence_length=len(sequence), features=features)
    
    # Plot
    fig, ax = plt.subplots(figsize=(8, 8))
    record.plot(ax=ax)
    ax.set_title(title)
    
    return fig
