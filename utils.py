"""
Utility functions for plasmid analysis and visualization
"""

import re
from typing import Dict, List, Tuple
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction
import json


def load_token_config() -> List[str]:
    """Load token configuration from JSON file"""
    try:
        with open("token_config.json", "r") as f:
            config = json.load(f)
        
        # Flatten all tokens into a single list
        all_tokens = []
        for category, tokens in config["special_tokens"].items():
            all_tokens.extend(tokens)
        
        return all_tokens
    except FileNotFoundError:
        # Fallback to basic tokens if file not found
        return [
            "<gc_content_low>", "<gc_content_medium>", "<gc_content_high>",
            "<copy_number_low>", "<copy_number_medium>", "<copy_number_high>",
            "<plasmid_type_expression>", "<plasmid_type_cloning>",
            "<resistance_ampicillin>", "<resistance_kanamycin>",
            "<origin_pBR322>", "<origin_pUC>", "<origin_ColE1>",
            "<promoter_T7>", "<promoter_lac>", "<promoter_tac>"
        ]


def extract_dna_from_generated_text(text: str, min_length: int = 100) -> str:
    """
    Extract DNA sequence from generated text.
    Handles various formats the model might output.
    """
    # Remove special tokens first
    text = re.sub(r'<[^>]+>', '', text)
    
    # Look for continuous DNA sequences (A, T, G, C)
    # Case insensitive
    dna_pattern = re.compile(r'[ATGCatgc]+')
    matches = dna_pattern.findall(text)
    
    # Filter matches by length and return the longest
    valid_matches = [m.upper() for m in matches if len(m) >= min_length]
    
    if valid_matches:
        # Return the longest match
        return max(valid_matches, key=len)
    
    # If no clear DNA found, try to clean the text
    cleaned = ''.join(c.upper() for c in text if c.upper() in 'ATGC')
    
    if len(cleaned) >= min_length:
        return cleaned
    
    return ""


def validate_dna_sequence(sequence: str) -> Tuple[bool, str]:
    """
    Validate DNA sequence.
    Returns (is_valid, error_message)
    """
    if not sequence:
        return False, "Empty sequence"
    
    # Check if sequence contains only ATGC
    invalid_chars = set(sequence.upper()) - set('ATGC')
    if invalid_chars:
        return False, f"Invalid characters found: {', '.join(invalid_chars)}"
    
    # Check minimum length
    if len(sequence) < 100:
        return False, f"Sequence too short: {len(sequence)} bp (minimum 100 bp)"
    
    # Check maximum length (plasmids are typically < 50kb)
    if len(sequence) > 50000:
        return False, f"Sequence too long: {len(sequence)} bp (maximum 50,000 bp)"
    
    return True, ""


def calculate_gc_content(sequence: str) -> Tuple[float, str]:
    """
    Calculate GC content and categorize it.
    Returns (gc_percentage, category)
    """
    gc_percent = gc_fraction(Seq(sequence)) * 100
    
    if gc_percent < 40:
        category = "Low"
    elif gc_percent > 55:
        category = "High"
    else:
        category = "Medium"
    
    return gc_percent, category


def estimate_copy_number(sequence: str, annotations: List[Dict] = None) -> str:
    """
    Estimate copy number based on sequence features.
    This is a simplified heuristic - improve based on your domain knowledge.
    """
    length = len(sequence)
    
    # Check for known high-copy origins if annotations available
    if annotations:
        high_copy_origins = ['pUC', 'ColE1', 'pMB1']
        medium_copy_origins = ['p15A', 'pSC101']
        low_copy_origins = ['pBR322', 'F', 'P1']
        
        for ann in annotations:
            if ann.get('type') == 'origin' or 'origin' in ann.get('name', '').lower():
                name = ann.get('name', '')
                if any(origin in name for origin in high_copy_origins):
                    return "High (>100 copies/cell)"
                elif any(origin in name for origin in medium_copy_origins):
                    return "Medium (15-100 copies/cell)"
                elif any(origin in name for origin in low_copy_origins):
                    return "Low (1-15 copies/cell)"
    
    # Fallback to length-based heuristic
    if length < 3000:
        return "High (>100 copies/cell)"
    elif length < 6000:
        return "Medium (15-100 copies/cell)"
    else:
        return "Low (1-15 copies/cell)"


def find_orfs(sequence: str, min_length: int = 300) -> List[Dict]:
    """
    Find Open Reading Frames (ORFs) in the sequence.
    Returns list of ORF annotations.
    """
    orfs = []
    seq = Seq(sequence)
    
    # Check all 6 reading frames (3 forward, 3 reverse)
    for strand, seq_strand in [(1, seq), (-1, seq.reverse_complement())]:
        for frame in range(3):
            length = 3 * ((len(seq_strand) - frame) // 3)
            for start in range(frame, frame + length, 3):
                codon = str(seq_strand[start:start + 3])
                if codon in ['ATG', 'GTG', 'TTG']:  # Start codons
                    # Look for stop codon
                    for end in range(start + 3, frame + length, 3):
                        codon = str(seq_strand[end:end + 3])
                        if codon in ['TAA', 'TAG', 'TGA']:  # Stop codons
                            orf_length = end - start + 3
                            if orf_length >= min_length:
                                orfs.append({
                                    'type': 'ORF',
                                    'start': start if strand == 1 else len(seq) - end - 3,
                                    'end': end + 3 if strand == 1 else len(seq) - start,
                                    'strand': '+' if strand == 1 else '-',
                                    'length': orf_length,
                                    'name': f'ORF_{len(orfs)+1}'
                                })
                            break
    
    # Sort by position
    orfs.sort(key=lambda x: x['start'])
    return orfs


def find_common_features(sequence: str) -> List[Dict]:
    """
    Find common plasmid features using pattern matching.
    Returns list of feature annotations.
    """
    features = []
    seq_upper = sequence.upper()
    
    # Common promoter sequences
    promoters = {
        'T7 Promoter': 'TAATACGACTCACTATAGGG',
        'T3 Promoter': 'AATTAACCCTCACTAAAGGG',
        'lac Promoter': 'TGGAATTGTGAGCGGATAACAATT',
        'tac Promoter': 'TTTACACTTTATGCTTCCGGCTC',
    }
    
    for name, pattern in promoters.items():
        pos = seq_upper.find(pattern)
        if pos != -1:
            features.append({
                'name': name,
                'type': 'promoter',
                'start': pos,
                'end': pos + len(pattern),
                'strand': '+'
            })
    
    # Common terminator sequences
    terminators = {
        'T7 Terminator': 'CTAGCATAACCCCTTGGGGCCTCTAAACGGGTCTTGAGGGGTTTTTTG',
        'rrnB T1 Terminator': 'TCTCGTGGGCTCGTGTTGTGTGTATTTTTTTTGTTTAG',
    }
    
    for name, pattern in terminators.items():
        pos = seq_upper.find(pattern)
        if pos != -1:
            features.append({
                'name': name,
                'type': 'terminator',
                'start': pos,
                'end': pos + len(pattern),
                'strand': '+'
            })
    
    # Ribosome Binding Site (RBS)
    rbs_pattern = 'AGGAGG'
    start = 0
    while True:
        pos = seq_upper.find(rbs_pattern, start)
        if pos == -1:
            break
        features.append({
            'name': 'RBS',
            'type': 'RBS',
            'start': pos,
            'end': pos + len(rbs_pattern),
            'strand': '+'
        })
        start = pos + 1
    
    return features


def analyze_sequence(sequence: str) -> Dict:
    """
    Comprehensive sequence analysis.
    Returns dictionary with all metrics and features.
    """
    # Validate sequence
    is_valid, error = validate_dna_sequence(sequence)
    if not is_valid:
        return {'error': error}
    
    # Calculate metrics
    gc_percent, gc_category = calculate_gc_content(sequence)
    copy_number = estimate_copy_number(sequence)
    
    # Find features
    orfs = find_orfs(sequence)
    common_features = find_common_features(sequence)
    
    return {
        'length': len(sequence),
        'gc_content': gc_percent,
        'gc_category': gc_category,
        'copy_number': copy_number,
        'orfs': orfs,
        'features': common_features,
        'num_orfs': len(orfs),
        'num_features': len(common_features)
    }
