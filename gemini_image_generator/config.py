"""Configuration constants and styles for Darnytsia Gemini Hub."""

# Custom CSS for modern UI - Google AI Studio style
CUSTOM_CSS = """
    <style>
        /* Google AI Studio inspired color scheme */
        :root {
            --ai-studio-bg: #fafafa;
            --ai-studio-panel-bg: #ffffff;
            --ai-studio-border: #e0e0e0;
            --ai-studio-text: #202124;
            --ai-studio-text-secondary: #5f6368;
            --ai-studio-primary: #1a73e8;
            --ai-studio-primary-hover: #1557b0;
        }
        
        /* Settings panel styling - Google AI Studio style */
        .settings-panel {
            background-color: var(--ai-studio-panel-bg);
            border-left: 1px solid var(--ai-studio-border);
            padding: 1.5rem;
            height: 100%;
            position: sticky;
            top: 0;
        }
        
        .settings-panel h3 {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--ai-studio-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 1rem;
            margin-top: 0;
        }
        
        .settings-panel .stSelectbox,
        .settings-panel .stSlider,
        .settings-panel .stButton {
            margin-bottom: 1.5rem;
        }
        
        /* Card-like containers */
        .stContainer > div {
            background-color: var(--ai-studio-panel-bg);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--ai-studio-border);
            margin-bottom: 1.5rem;
        }
        
        /* Button styling - Material Design inspired */
        .stButton > button {
            width: 100%;
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s ease;
            border: 1px solid var(--ai-studio-border);
            padding: 0.625rem 1rem;
            background-color: var(--ai-studio-panel-bg);
            color: var(--ai-studio-text);
            font-size: 0.875rem;
        }
        
        .stButton > button:hover {
            background-color: #f8f9fa;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        
        /* Primary button - Google blue */
        button[kind="primary"] {
            background-color: var(--ai-studio-primary);
            color: white;
            border: none;
        }
        
        button[kind="primary"]:hover {
            background-color: var(--ai-studio-primary-hover);
            box-shadow: 0 2px 4px rgba(26, 115, 232, 0.3);
        }
        
        /* Status indicators */
        .status-pending {
            color: #ff9800;
            font-weight: 500;
        }
        
        .status-processing {
            color: var(--ai-studio-primary);
            font-weight: 500;
        }
        
        .status-completed {
            color: #34a853;
            font-weight: 500;
        }
        
        .status-failed {
            color: #ea4335;
            font-weight: 500;
        }
        
        /* Improve spacing */
        .element-container {
            margin-bottom: 1rem;
        }
        
        /* Better text area - Material Design */
        .stTextArea > div > div > textarea {
            border-radius: 4px;
            border: 1px solid var(--ai-studio-border);
            font-size: 0.875rem;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: var(--ai-studio-primary);
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.1);
            outline: none;
        }
        
        /* Selectbox styling */
        .stSelectbox > div > div > select {
            border-radius: 4px;
            border: 1px solid var(--ai-studio-border);
            font-size: 0.875rem;
        }
        
        .stSelectbox > div > div > select:focus {
            border-color: var(--ai-studio-primary);
            box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.1);
        }
        
        /* Slider styling */
        .stSlider > div > div {
            color: var(--ai-studio-primary);
        }
        
        /* File uploader styling */
        .uploadedFile {
            border-radius: 4px;
            padding: 0.5rem;
            margin: 0.5rem 0;
            border: 1px solid var(--ai-studio-border);
        }
        
        /* Progress bar styling */
        .stProgress > div > div > div > div {
            background-color: var(--ai-studio-primary);
        }
        
        /* Remove extra spacing from markdown breaks */
        br {
            display: none;
        }
        
        /* Chat layout styling */
        .stChatMessage {
            margin-bottom: 1rem;
        }
        
        /* Create scrollable container for chat messages */
        .chat-messages-scrollable {
            max-height: calc(100vh - 400px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1rem 0;
            margin-bottom: 1rem;
            scroll-behavior: smooth;
        }
        
        /* Ensure chat input container stays at bottom */
        div[data-testid="stChatInputContainer"],
        div[data-testid="stChatInputContainer"] > div {
            position: sticky !important;
            bottom: 0 !important;
            background-color: white !important;
            z-index: 100 !important;
            padding-top: 1rem !important;
            border-top: 1px solid var(--ai-studio-border) !important;
            margin-top: auto !important;
        }
        
        /* Dark mode support for chat input */
        [data-theme="dark"] div[data-testid="stChatInputContainer"],
        [data-theme="dark"] div[data-testid="stChatInputContainer"] > div {
            background-color: #0e1117 !important;
        }
        
        /* Custom scrollbar for chat messages */
        .chat-messages-scrollable::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-messages-scrollable::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .chat-messages-scrollable::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }
        
        .chat-messages-scrollable::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        
        /* Main content area */
        .main-content {
            padding-right: 1rem;
        }
        
        /* Divider styling */
        hr {
            border: none;
            border-top: 1px solid var(--ai-studio-border);
            margin: 1.5rem 0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 500;
            color: var(--ai-studio-text);
        }
    </style>
"""

# Prompt templates
PROMPT_WOMEN = """Keep the facial features of the person in the uploaded image exactly consistent. Dress her in a professional, **fitted black business suit (blazer) with a crisp white blouse**. Background: Place the subject against a clean, solid dark gray studio photography backdrop. The background should have a subtle gradient, slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style: Shot on a Sony A7III with an 85mm f/1.4 lens, creating a flattering portrait compression. Lighting: Use a classic three-point lighting setup. The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details: Render natural skin texture with visible pores, not an airbrushed look. Add natural catchlights to the eyes. The fabric of the suit should show a subtle wool texture. Final image should be an ultra-realistic, 8k professional headshot."""

PROMPT_MEN = """Keep the facial features of the person in the uploaded image exactly consistent . Dress them in a professional  black business suit  with a white shirt  and a tie, similar to the reference image. Background : Place the subject against a clean, solid dark gray studio photography backdrop . The background should have a subtle gradient , slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style : Shot on a Sony A7III with an 85mm f/1.4 lens , creating a flattering portrait compression. Lighting : Use a classic three-point lighting setup . The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details : Render natural skin texture with visible pores , not an airbrushed look. Add natural catchlights to the eyes . The fabric of the suit should show a subtle wool texture.Final image should be an ultra-realistic, 8k professional headshot."""

