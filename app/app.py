import gradio as gr
import os
import pandas as pd
from modules import translator, generator, annotator, visualizer, metrics

# Ensure OpenAI key is present
if not os.environ.get("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY not found. NL Translation will fail.")

def process_pipeline(prompt, model_choice):
    # Step 1: Translate NL to Tokens
    status_msg = "Translating prompt..."
    yield (status_msg, "", "", None, None, None)
    
    tokens = translator.translate_prompt(prompt, model_choice)
    if tokens.startswith("Error"):
        yield (f"Error in translation: {tokens}", "", "", None, None, None)
        return

    # Step 2: Generate Plasmid
    status_msg = f"Generating plasmid using {model_choice}..."
    yield (status_msg, tokens, "", None, None, None)
    
    dna_seq = generator.generate_plasmid(tokens, model_choice)
    if dna_seq.startswith("Error"):
        yield (f"Error in generation: {dna_seq}", tokens, "", None, None, None)
        return

    # Step 3: Annotation & Metrics
    status_msg = "Annotating and visualizing..."
    yield (status_msg, tokens, dna_seq, None, None, None)
    
    annotations, analysis = annotator.annotate_sequence(dna_seq)
    
    # Calculate metrics
    seq_metrics = metrics.calculate_metrics(dna_seq)
    metrics_df = pd.DataFrame([seq_metrics])
    
    # Create Annotations Table
    if annotations:
        ann_df = pd.DataFrame(annotations)
        # Select relevant columns for display
        cols = ['type', 'name', 'start', 'end', 'strand']
        # Filter for existing cols
        cols = [c for c in cols if c in ann_df.columns]
        ann_df = ann_df[cols]
    else:
        ann_df = pd.DataFrame(columns=['type', 'name', 'start', 'end', 'strand'])

    # Step 4: Visualization
    fig = visualizer.create_plasmid_map(dna_seq, annotations, title="Generated Plasmid")
    
    yield ("Done!", tokens, dna_seq, fig, metrics_df, ann_df)

with gr.Blocks(title="Plasmid Generator") as demo:
    gr.Markdown("# 🧬 Plasmid Generator Space")
    gr.Markdown("""
    Generate plasmids from natural language descriptions using `plasmid-gpt`.
    1. Enter a description (e.g., "A high copy plasmid with Kan resistance").
    2. The system translates it to special control tokens.
    3. The model generates the DNA sequence.
    4. We annotate and visualize the result.
    """)
    
    with gr.Row():
        with gr.Column():
            nl_input = gr.Textbox(label="Natural Language Prompt", placeholder="e.g. High copy number plasmid with Ampicillin resistance")
            model_select = gr.Dropdown(
                choices=["McClain/plasmid-gpt-244m", "McClain/plasmid-gpt-319m"], 
                value="McClain/plasmid-gpt-244m", 
                label="Model Version"
            )
            gen_btn = gr.Button("Generate Plasmid", variant="primary")
        
        with gr.Column():
            status_output = gr.Label(label="Status")
            
    with gr.Tabs():
        with gr.Tab("Visualization & Metrics"):
            with gr.Row():
                with gr.Column(scale=1):
                    plot_output = gr.Plot(label="Plasmid Map")
                with gr.Column(scale=1):
                    metrics_output = gr.Dataframe(label="Sequence Metrics", interactive=False)
                    ann_output = gr.Dataframe(label="Detected Features", interactive=False)
                    
        with gr.Tab("Raw Output"):
             tokens_output = gr.Textbox(label="Generated Control Tokens", interactive=False)
             dna_output = gr.Textbox(label="Generated DNA Sequence", lines=10, interactive=False)

    gen_btn.click(
        fn=process_pipeline,
        inputs=[nl_input, model_select],
        outputs=[status_output, tokens_output, dna_output, plot_output, metrics_output, ann_output]
    )

if __name__ == "__main__":
    demo.launch()
