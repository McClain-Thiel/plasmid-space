import gradio as gr
import torch
from transformers import GPT2LMHeadModel
import os
from typing import Dict, List, Tuple
import plotly.graph_objects as go
import numpy as np
from llm_providers import LLMProviderManager
from plasmid_tokenizer import PlasmidGPTTokenizer
from utils import (
    load_token_config,
    extract_dna_from_generated_text,
    validate_dna_sequence,
    calculate_gc_content,
    estimate_copy_number,
    find_orfs,
    find_common_features,
    analyze_sequence
)

# Model configuration - easily extensible for new models
MODEL_CONFIG = {
    "244m": {
        "hf_name": "McClain/plasmid-gpt-244m",
        "max_length": 4096,
        "description": "Faster, good for quick iterations (~980 MB)"
    },
    "319m": {
        "hf_name": "McClain/plasmid-gpt-319m",
        "max_length": 4096,
        "description": "Larger, potentially more accurate (~1.3 GB)"
    }
}

# Initialize models (lazy loading)
plasmid_model = None
plasmid_tokenizer = None
llm_manager = LLMProviderManager()
current_model_name = None

def load_plasmid_model(model_name: str):
    """Load the plasmid-gpt model with custom tokenizer"""
    global plasmid_model, plasmid_tokenizer, current_model_name
    
    # Only reload if model name changed
    if plasmid_model is None or current_model_name != model_name:
        print(f"Loading PlasmidGPT model: {model_name}")
        
        # Load custom tokenizer
        try:
            print("Loading custom PlasmidGPT tokenizer...")
            plasmid_tokenizer = PlasmidGPTTokenizer.from_pretrained(model_name)
            print(f"✓ Tokenizer loaded successfully (vocab size: {len(plasmid_tokenizer)})")
        except Exception as e:
            raise ValueError(
                f"Could not load custom tokenizer for {model_name}. "
                f"Error: {e}"
            )
        
        # Load the model (use GPT2LMHeadModel as per model card)
        try:
            print(f"Loading model weights...")
            plasmid_model = GPT2LMHeadModel.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            plasmid_model.eval()  # Set to evaluation mode
            print("✓ Model loaded successfully")
        except Exception as e:
            raise ValueError(
                f"Could not load model {model_name}. "
                f"Error: {e}"
            )
        
        current_model_name = model_name
    
    return plasmid_model, plasmid_tokenizer


def get_token_config(model_name: str) -> List[str]:
    """Get the special tokens configuration"""
    # Try to get tokens from the model's tokenizer
    try:
        tokenizer = PlasmidGPTTokenizer.from_pretrained(model_name)
        # Get all condition tokens (like <HOST:ECOLI>, <RESISTANCE:AMP>, etc.)
        condition_tokens = tokenizer.get_condition_tokens()
        return condition_tokens
    except:
        # Fallback to our config file
        config_tokens = load_token_config()
        return config_tokens

def natural_language_to_tokens(prompt: str, model_name: str) -> str:
    """Convert natural language prompt to special tokens using available LLM"""
    try:
        token_config = get_token_config(model_name)
        tokens = llm_manager.convert_to_tokens(prompt, token_config)
        return tokens
    except Exception as e:
        return f"Error converting prompt: {str(e)}"

def generate_plasmid(special_tokens: str, model_name: str, max_length: int = 2048) -> Tuple[str, str]:
    """
    Generate plasmid DNA sequence from special tokens.
    Returns (dna_sequence, raw_output)
    """
    try:
        model, tokenizer = load_plasmid_model(model_name)
        
        # Add <SEQ> token if not present (indicates start of DNA sequence)
        prompt = special_tokens
        if "<SEQ>" not in prompt:
            prompt = prompt + "<SEQ>"
        
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt", add_bos=True)
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Generate (following model card recommendations)
        # Note: Each nucleotide (A,T,G,C) is one token, so max_new_tokens = bp length
        print(f"\n🧬 Starting DNA generation ({max_length} bp max)...")
        print(f"   This will take ~30-60 seconds depending on length")
        print(f"   Model is generating... (no progress bar available from transformers)\n")
        
        import time
        start_time = time.time()
        
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                max_new_tokens=max_length,  # Generate up to max_length nucleotides
                do_sample=True,
                temperature=0.85,  # Per model card
                top_k=50,  # Per model card
                top_p=0.95,  # Add nucleus sampling for better diversity
                repetition_penalty=1.15,  # Per model card - prevents repetitive sequences
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=15,  # Prevent 15-mer repeats (helps avoid homopolymer runs)
            )
        
        elapsed = time.time() - start_time
        print(f"\n✓ DNA generation complete in {elapsed:.1f} seconds")
        
        # Decode the generated sequence
        generated_text = tokenizer.decode(outputs[0].tolist(), skip_special_tokens=False)
        
        # Extract DNA sequence (everything after <SEQ> and before <EOS>)
        if "<SEQ>" in generated_text:
            dna_part = generated_text.split("<SEQ>", 1)[1]
            if "<EOS>" in dna_part:
                dna_part = dna_part.split("<EOS>")[0]
            dna_sequence = dna_part.strip()
        else:
            dna_sequence = generated_text
        
        # Clean up - remove any remaining special tokens
        import re
        dna_sequence = re.sub(r'<[^>]+>', '', dna_sequence)
        
        # Validate it's only ATGC
        dna_sequence = ''.join(c for c in dna_sequence.upper() if c in 'ATGC')
        
        if not dna_sequence:
            return "", f"Could not extract DNA sequence from output:\n{generated_text[:500]}..."
        
        # Validate the DNA sequence
        is_valid, error = validate_dna_sequence(dna_sequence)
        if not is_valid:
            return "", f"Invalid DNA sequence: {error}\nRaw output:\n{generated_text[:500]}..."
        
        return dna_sequence, generated_text
            
    except Exception as e:
        import traceback
        return "", f"Error generating plasmid: {str(e)}\n{traceback.format_exc()}"


def annotate_plasmid(sequence: str) -> List[Dict]:
    """Annotate plasmid features using plasmid-kit or fallback methods"""
    annotations = []
    
    try:
        # Try to use plasmid-kit if available
        import plasmidkit as pk
        
        # Initialize plasmid-kit data if needed (downloads databases on first run)
        try:
            pk.bootstrap_data()
        except:
            pass  # Already bootstrapped or not needed
        
        # Use analyze() for comprehensive report (includes origins, markers, promoters, etc.)
        # IMPORTANT: is_sequence=True tells plasmid-kit this is a raw DNA string, not a file path!
        report = pk.analyze(sequence, is_sequence=True, skip_prodigal=False)
        
        # Extract annotations from report
        if report and 'annotations' in report:
            # Convert plasmid-kit format to our format
            for ann in report['annotations']:
                annotations.append({
                    'name': ann.get('id', ann.get('name', 'Unknown')),
                    'type': ann.get('type', 'feature'),
                    'start': ann.get('start', 0),
                    'end': ann.get('end', 0),
                    'strand': ann.get('strand', '+')
                })
            
            if annotations:
                print(f"plasmid-kit found {len(annotations)} features:")
                feature_counts = report.get('feature_counts', {})
                for feature_type, count in feature_counts.items():
                    print(f"  {feature_type}: {count}")
                return annotations
        
    except ImportError:
        print("plasmid-kit not available (not installed)")
    except Exception as e:
        print(f"plasmid-kit failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback: use our utility functions
    print("Using fallback annotation methods...")
    try:
        # Find common features using pattern matching
        features = find_common_features(sequence)
        annotations.extend(features)
        
        # Find ORFs (but limit them since they're less specific)
        orfs = find_orfs(sequence, min_length=300)
        annotations.extend(orfs[:5])  # Limit to first 5 ORFs
        
        print(f"Fallback found {len(annotations)} features")
        return annotations
    except Exception as e:
        print(f"Fallback annotation failed: {e}")
        return [{"error": str(e)}]

def create_plasmid_visualization(sequence: str, annotations: List[Dict]) -> go.Figure:
    """Create circular plasmid visualization similar to pLannotate"""
    length = len(sequence)
    
    # Create circular plot
    fig = go.Figure()
    
    # Main plasmid circle
    theta = np.linspace(0, 2*np.pi, 100)
    radius = 1.0
    x_circle = radius * np.cos(theta)
    y_circle = radius * np.sin(theta)
    
    fig.add_trace(go.Scatter(
        x=x_circle, y=y_circle,
        mode='lines',
        line=dict(color='gray', width=3),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add annotations as arcs
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
    
    for i, ann in enumerate(annotations):
        if 'error' in ann:
            continue
            
        start = ann.get('start', 0)
        end = ann.get('end', 0)
        name = ann.get('name', 'Unknown')
        
        # Convert position to angle
        start_angle = (start / length) * 2 * np.pi
        end_angle = (end / length) * 2 * np.pi
        
        # Create arc for annotation
        arc_theta = np.linspace(start_angle, end_angle, 20)
        arc_radius = 1.15
        x_arc = arc_radius * np.cos(arc_theta)
        y_arc = arc_radius * np.sin(arc_theta)
        
        color = colors[i % len(colors)]
        
        fig.add_trace(go.Scatter(
            x=x_arc, y=y_arc,
            mode='lines',
            line=dict(color=color, width=8),
            name=name,
            hovertemplate=f"{name}<br>Position: {start}-{end}<extra></extra>"
        ))
    
    # Add size label in center
    fig.add_annotation(
        x=0, y=0,
        text=f"{length} bp",
        showarrow=False,
        font=dict(size=20, color="black")
    )
    
    fig.update_layout(
        showlegend=True,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='white',
        height=600,
        width=600,
        title="Plasmid Map"
    )
    
    fig.update_xaxes(range=[-1.5, 1.5])
    fig.update_yaxes(range=[-1.5, 1.5])
    
    return fig

def format_annotations_table(annotations: List[Dict]) -> str:
    """Format annotations as an HTML table"""
    if not annotations or (len(annotations) == 1 and 'error' in annotations[0]):
        return "<p>No annotations found or error occurred.</p>"
    
    html = """
    <table style="width:100%; border-collapse: collapse;">
        <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px;">Feature</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Type</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Position</th>
            <th style="border: 1px solid #ddd; padding: 8px;">Strand</th>
        </tr>
    """
    
    for ann in annotations:
        if 'error' in ann:
            continue
        name = ann.get('name', 'Unknown')
        type_ = ann.get('type', 'Unknown')
        start = ann.get('start', 0)
        end = ann.get('end', 0)
        strand = ann.get('strand', '?')
        
        html += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{name}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{type_}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{start}-{end}</td>
            <td style="border: 1px solid #ddd; padding: 8px;">{strand}</td>
        </tr>
        """
    
    html += "</table>"
    return html

def full_pipeline(prompt: str, model_choice: str, max_length: int = 2048):
    """
    Run the full pipeline from prompt to visualization with progressive updates.
    This is a generator that yields intermediate results as they become available.
    """
    
    print(f"\n{'='*60}")
    print(f"[Pipeline] USER SELECTED MODEL: {model_choice}")
    print(f"[Pipeline] Max length: {max_length} bp")
    print(f"[Pipeline] Prompt: {prompt[:100]}...")
    print(f"{'='*60}\n")
    
    # Get model config
    if model_choice not in MODEL_CONFIG:
        error_msg = f"Unknown model: {model_choice}"
        print(f"[Pipeline] ERROR: {error_msg}")
        yield (error_msg, error_msg, "", None, "")
        return
    
    model_config = MODEL_CONFIG[model_choice]
    model_name = model_config["hf_name"]
    print(f"[Pipeline] Full model name: {model_name}")
    print(f"[Pipeline] Model max length: {model_config['max_length']} bp")
    
    # Step 1: Convert natural language to special tokens (fast - seconds)
    # Show "Generating tokens..." placeholder
    print("[Pipeline] Yielding stage 1: Loading message")
    yield (
        "⏳ Generating condition tokens...",  # tokens
        "",  # dna
        "",  # metrics
        None,  # plot
        ""  # annotations
    )
    
    special_tokens = natural_language_to_tokens(prompt, model_name)
    print(f"[Pipeline] Generated tokens: {special_tokens[:100]}")
    
    # Check if token conversion failed
    if special_tokens.startswith("Error"):
        print(f"[Pipeline] Token generation failed")
        yield (special_tokens, special_tokens, "", None, "")
        return
    
    # Yield tokens immediately when ready
    print("[Pipeline] Yielding stage 2: Tokens ready")
    yield (
        special_tokens,  # Show the tokens!
        "⏳ Generating DNA sequence... (this may take 30-60 seconds)",  # dna placeholder
        "",  # metrics
        None,  # plot
        ""  # annotations
    )
    
    # Step 2: Generate plasmid DNA (slower - 30-60 seconds)
    print("\n" + "="*60)
    print("[Pipeline] STAGE 2: DNA GENERATION")
    print("="*60)
    print(f"[Pipeline] This stage typically takes 30-60 seconds...")
    print(f"[Pipeline] Calling generate_plasmid() now...\n")
    
    import time
    gen_start = time.time()
    dna_sequence, raw_output = generate_plasmid(special_tokens, model_name, max_length)
    gen_elapsed = time.time() - gen_start
    
    print(f"\n[Pipeline] DNA generation took {gen_elapsed:.1f} seconds")
    print(f"[Pipeline] DNA generated: {len(dna_sequence) if dna_sequence else 0} bp")
    print("="*60 + "\n")
    
    # Check if generation failed
    if not dna_sequence:
        error_msg = raw_output if raw_output else "Failed to generate DNA sequence"
        print(f"[Pipeline] DNA generation failed")
        yield (special_tokens, error_msg, "", None, "")
        return
    
    # Yield DNA sequence when ready
    print("[Pipeline] Yielding stage 3: DNA ready")
    yield (
        special_tokens,  # tokens (already shown)
        dna_sequence,  # Show the DNA!
        "⏳ Analyzing sequence and annotating features...",  # metrics placeholder
        None,  # plot
        "⏳ Annotating features..."  # annotations placeholder
    )
    
    # Step 3: Annotate plasmid (medium - 5-10 seconds)
    print("[Pipeline] Starting annotation...")
    annotations = annotate_plasmid(dna_sequence)
    print(f"[Pipeline] Found {len(annotations)} annotations")
    
    # Step 4: Calculate metrics
    gc_percent, gc_category = calculate_gc_content(dna_sequence)
    copy_number = estimate_copy_number(dna_sequence, annotations)
    
    # Count features
    num_features = len([a for a in annotations if 'error' not in a])
    
    metrics = f"""
**Sequence Length:** {len(dna_sequence):,} bp

**GC Content:** {gc_percent:.2f}% ({gc_category})

**Estimated Copy Number:** {copy_number}

**Features Detected:** {num_features}
    """
    
    # Yield metrics when ready
    print("[Pipeline] Yielding stage 4: Metrics ready")
    yield (
        special_tokens,  # tokens
        dna_sequence,  # dna
        metrics,  # Show metrics!
        None,  # plot still loading
        "⏳ Creating visualization..."  # annotations placeholder
    )
    
    # Step 5: Create visualization (medium - 5-10 seconds)
    print("[Pipeline] Creating visualization...")
    fig = create_plasmid_visualization(dna_sequence, annotations)
    
    # Step 6: Format annotations table
    annotations_html = format_annotations_table(annotations)
    
    # Final yield with everything complete
    print("[Pipeline] Yielding stage 5: Complete!")
    yield (
        special_tokens,
        dna_sequence,
        metrics,
        fig,  # Show visualization!
        annotations_html  # Show annotations!
    )
    print("[Pipeline] Generation complete")

# Create Gradio interface
with gr.Blocks(title="Plasmid-GPT Demo") as demo:
    gr.Markdown("""
    # 🧬 Plasmid-GPT: AI-Powered Plasmid Design
    
    Generate custom plasmids using natural language! This demo uses AI to convert your description 
    into a plasmid sequence, then annotates and visualizes it.
    
    ## About the Models:
    - **244M**: Faster, good for quick iterations (~980 MB)
    - **319M**: Larger, potentially more accurate (~1.3 GB)
    - **GPU**: Will automatically use CUDA GPU if available, otherwise runs on CPU
    
    ## Example Prompts:
    - "Design a low copy number cloning vector with ampicillin resistance"
    - "Create a high copy expression plasmid for protein production in E. coli"
    - "Generate a shuttle vector with both bacterial and yeast origins of replication"
    
    ## How it works:
    1. **Describe** your desired plasmid in natural language
    2. **AI translates** your description to special tokens (~2-5 seconds)
    3. **Model generates** the DNA sequence (~30-60 seconds)
    4. **Automatic annotation** and visualization (~10-15 seconds)
    """)
    
    # Status indicator
    status_display = gr.Markdown("", visible=True)
    
    with gr.Row():
        with gr.Column(scale=1):
            prompt_input = gr.Textbox(
                label="Describe your plasmid",
                placeholder="E.g., 'I need a high copy number expression plasmid with a T7 promoter for E. coli'",
                lines=4
            )
            
            model_selector = gr.Radio(
                choices=list(MODEL_CONFIG.keys()),
                value="244m",
                label="Model Size",
                info="244m is faster, 319m is more accurate",
                interactive=True
            )
            
            # Get max value from model config (all models currently support 4096)
            model_max_length = max([config["max_length"] for config in MODEL_CONFIG.values()])
            
            max_length_slider = gr.Slider(
                minimum=1000,
                maximum=model_max_length,
                value=min(5000, model_max_length),
                step=500,
                label="Maximum Sequence Length (bp)",
                info=f"Typical plasmids: 2-8 kb. Max supported: {model_max_length} bp"
            )
            
            generate_btn = gr.Button("🧬 Generate Plasmid", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            gr.Markdown("### Condition Tokens")
            tokens_output = gr.Textbox(
                label="Generated Tokens", 
                lines=3,
                info="Appears first (~2-5 seconds)"
            )
            
            gr.Markdown("### Plasmid Metrics")
            metrics_output = gr.Markdown(value="*Metrics will appear after sequence generation*")
    
    gr.Markdown("---")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Generated DNA Sequence")
            dna_output = gr.Textbox(
                label="DNA Sequence", 
                lines=10, 
                max_lines=20,
                info="Appears second (~30-60 seconds)"
            )
        
        with gr.Column(scale=1):
            gr.Markdown("### Plasmid Visualization")
            plasmid_plot = gr.Plot(label="Circular Plasmid Map")
    
    gr.Markdown("### Feature Annotations")
    annotations_output = gr.HTML(value="<p><i>Annotations will appear after sequence is generated and analyzed...</i></p>")
    
    # Connect the pipeline (supports generators for progressive updates)
    generate_btn.click(
        fn=full_pipeline,
        inputs=[prompt_input, model_selector, max_length_slider],
        outputs=[tokens_output, dna_output, metrics_output, plasmid_plot, annotations_output],
        show_progress=True,  # Changed from "full" - works better with generators
        api_name="generate_plasmid"
    )
    
    # Add model selector change event for visual feedback
    def on_model_change(choice):
        if choice in MODEL_CONFIG:
            config = MODEL_CONFIG[choice]
            return f"**Selected:** {choice} ({config['description']})"
        return ""
    
    model_selector.change(
        fn=on_model_change,
        inputs=[model_selector],
        outputs=[metrics_output]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
