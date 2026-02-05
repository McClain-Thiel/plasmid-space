# Project Structure

Overview of all files in the Plasmid-GPT demo application.

## Core Application Files

### `app.py` (Main Application)
The main Gradio application that ties everything together.

**Key Functions:**
- `load_plasmid_model()` - Loads the plasmid-gpt model (244m or 319m)
- `natural_language_to_tokens()` - Converts user prompt to special tokens using LLM
- `generate_plasmid()` - Generates DNA sequence from special tokens
- `annotate_plasmid()` - Annotates features in the generated sequence
- `create_plasmid_visualization()` - Creates circular plasmid map visualization
- `full_pipeline()` - Orchestrates the complete workflow
- Gradio UI definition at the bottom

**Technologies:**
- Gradio for UI
- PyTorch + Transformers for model inference
- Plotly for visualization

### `llm_providers.py` (LLM Integration)
Implements multiple LLM providers with automatic fallback.

**Classes:**
- `LLMProvider` - Abstract base class
- `AnthropicProvider` - Claude Haiku implementation
- `GeminiProvider` - Google Gemini implementation
- `OpenAIProvider` - GPT-4o-mini implementation
- `LLMProviderManager` - Manages providers with fallback logic

**Features:**
- Automatic provider selection based on available API keys
- Fallback to next provider if one fails
- Standardized prompt format across providers

### `utils.py` (Utility Functions)
Core utility functions for sequence analysis and processing.

**Key Functions:**
- `load_token_config()` - Loads special tokens from JSON
- `extract_dna_from_generated_text()` - Extracts DNA from model output
- `validate_dna_sequence()` - Validates DNA sequences
- `calculate_gc_content()` - Calculates and categorizes GC content
- `estimate_copy_number()` - Estimates plasmid copy number
- `find_orfs()` - Finds Open Reading Frames
- `find_common_features()` - Pattern-based feature detection
- `analyze_sequence()` - Comprehensive sequence analysis

**Use Cases:**
- Sequence validation and cleaning
- Feature detection without external libraries
- Plasmid characterization

## Configuration Files

### `token_config.json`
Defines the special tokens used to condition the model.

**Token Categories:**
- `gc_content` - GC content levels (low/medium/high)
- `copy_number` - Copy number levels
- `plasmid_type` - Expression, cloning, shuttle, binary
- `resistance_markers` - Antibiotic resistance genes
- `origins` - Origins of replication
- `promoters` - Promoter sequences
- `tags` - Protein tags
- `features` - Other genetic elements
- `organisms` - Target organisms

**Customization:**
Edit this file to match your model's actual tokenizer vocabulary.

### `requirements.txt`
Python dependencies for the application.

**Key Dependencies:**
- `gradio` - Web UI framework
- `torch` + `transformers` - Model inference
- `anthropic`, `google-generativeai`, `openai` - LLM APIs
- `biopython` - Sequence analysis
- `plotly` - Visualization
- `plasmid-kit` - Plasmid annotation (from GitHub)

### `.gitignore`
Specifies files to ignore in git.

**Ignored:**
- Environment variables (`.env`)
- Python cache files
- Virtual environments
- Model cache files
- IDE settings

### `.env.example`
Template for environment variables.

**Variables:**
- `ANTHROPIC_API_KEY` - For Claude
- `GOOGLE_API_KEY` - For Gemini
- `OPENAI_API_KEY` - For GPT

## Documentation Files

### `README.md` (HuggingFace Space README)
Main documentation displayed on the HuggingFace Space.

**Sections:**
- Feature overview
- How it works (with diagram)
- Model information
- Setup instructions
- Citation information

**Front Matter:**
Contains HuggingFace Space metadata (title, emoji, SDK, etc.)

### `DEPLOYMENT.md`
Detailed deployment guide for HuggingFace Spaces.

**Contents:**
- Step-by-step deployment instructions
- Configuration guide
- Troubleshooting tips
- Performance optimization
- Local testing instructions

### `QUICK_START.md`
Quick reference for getting started.

**Contents:**
- Simplified deployment steps
- Local setup instructions
- Example prompts
- Common troubleshooting
- Tips for best results

### `PROJECT_STRUCTURE.md` (This File)
Documentation of the project structure and file organization.

### `LICENSE`
MIT License for the project.

## Testing Files

### `test_local.py`
Local testing script for individual components.

**Tests:**
- Token configuration loading
- Sequence analysis
- Feature detection
- ORF detection
- LLM provider connectivity

**Usage:**
```bash
python test_local.py
```

Useful for testing without running the full Gradio app or loading the models.

## Workflow Diagram

```
User Input (Natural Language)
    ↓
[llm_providers.py]
Convert to Special Tokens
    ↓
[app.py: generate_plasmid()]
Generate DNA with plasmid-gpt
    ↓
[utils.py: extract_dna_from_generated_text()]
Extract and Validate DNA
    ↓
[app.py: annotate_plasmid()]
↓                    ↓
plasmid-kit     [utils.py: find_common_features()]
(if available)    (fallback)
    ↓
[utils.py: calculate_gc_content(), estimate_copy_number()]
Calculate Metrics
    ↓
[app.py: create_plasmid_visualization()]
Generate Circular Map
    ↓
Display in Gradio UI
```

## File Dependencies

```
app.py
├── llm_providers.py
│   ├── anthropic (external)
│   ├── google.generativeai (external)
│   └── openai (external)
├── utils.py
│   ├── biopython (external)
│   └── token_config.json
└── transformers (external)

test_local.py
├── utils.py
└── llm_providers.py
```

## Key Design Decisions

### 1. Multi-Provider LLM Support
- **Why**: Flexibility for users who may have access to different APIs
- **Implementation**: Abstract provider interface with automatic fallback
- **Benefit**: App works with any of the three major LLM providers

### 2. Fallback Annotation
- **Why**: plasmid-kit may not be available or may fail
- **Implementation**: Pattern-based annotation as backup
- **Benefit**: App remains functional even without external dependencies

### 3. Modular Architecture
- **Why**: Easy to test, maintain, and extend
- **Implementation**: Separate files for LLM, utils, and main app
- **Benefit**: Can test components independently

### 4. Token Configuration File
- **Why**: Easy to update tokens without modifying code
- **Implementation**: JSON file loaded at runtime
- **Benefit**: Non-programmers can customize tokens

### 5. Comprehensive Error Handling
- **Why**: Graceful degradation for production use
- **Implementation**: Try/except blocks with meaningful error messages
- **Benefit**: App doesn't crash on edge cases

## Extending the Application

### Adding a New LLM Provider
1. Create a new class in `llm_providers.py` inheriting from `LLMProvider`
2. Implement `is_available()` and `convert_to_tokens()`
3. Add to `LLMProviderManager.providers` list

### Adding New Metrics
1. Create function in `utils.py`
2. Call from `full_pipeline()` in `app.py`
3. Update metrics display string

### Customizing Visualization
1. Modify `create_plasmid_visualization()` in `app.py`
2. Adjust Plotly figure parameters (colors, sizes, layout)
3. Add new annotation types with different visual styles

### Adding New Features to Detect
1. Add patterns to `find_common_features()` in `utils.py`
2. Or implement new detection function
3. Call from `annotate_plasmid()` in `app.py`

## Performance Considerations

- **Model Loading**: Models are lazy-loaded and cached
- **LLM Caching**: Provider instances are reused
- **ORF Limiting**: Only first 10 ORFs shown to avoid clutter
- **Token Scanning**: Limited to first 50k tokens when scanning tokenizer

## Security Notes

- API keys must be stored as environment variables or HuggingFace secrets
- Never commit `.env` file (it's in `.gitignore`)
- Use HuggingFace Spaces secrets feature for production deployment
