"""Configuration constants and styles for NanaBanana for Darnytsia."""

# Custom CSS for modern UI
CUSTOM_CSS = """
    <style>
        /* Main title styling */
        .main-title {
            text-align: center;
            padding: 1rem 0;
            margin-bottom: 1rem;
        }
        
        /* Subtitle styling */
        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        
        /* Card-like containers */
        .stContainer > div {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin-bottom: 1.5rem;
        }
        
        /* Button styling */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
            padding: 0.75rem 1.5rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Primary button */
        button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        button[kind="primary"]:hover {
            background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            padding-top: 2rem;
        }
        
        /* Status indicators */
        .status-pending {
            color: #ff9800;
            font-weight: 600;
        }
        
        .status-processing {
            color: #2196f3;
            font-weight: 600;
        }
        
        .status-completed {
            color: #4caf50;
            font-weight: 600;
        }
        
        .status-failed {
            color: #f44336;
            font-weight: 600;
        }
        
        /* Improve spacing */
        .element-container {
            margin-bottom: 1rem;
        }
        
        /* Better text area */
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 2px solid #e0e0e0;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* File uploader styling */
        .uploadedFile {
            border-radius: 8px;
            padding: 0.5rem;
            margin: 0.5rem 0;
        }
        
        /* Progress bar styling */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Remove extra spacing from markdown breaks */
        br {
            display: none;
        }
        
        /* Chat layout styling */
        /* Style chat messages */
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
            border-top: 1px solid #e0e0e0 !important;
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
    </style>
"""

# Prompt templates
PROMPT_WOMEN = """Keep the facial features of the person in the uploaded image exactly consistent. Dress her in a professional, **fitted black business suit (blazer) with a crisp white blouse**. Background: Place the subject against a clean, solid dark gray studio photography backdrop. The background should have a subtle gradient, slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style: Shot on a Sony A7III with an 85mm f/1.4 lens, creating a flattering portrait compression. Lighting: Use a classic three-point lighting setup. The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details: Render natural skin texture with visible pores, not an airbrushed look. Add natural catchlights to the eyes. The fabric of the suit should show a subtle wool texture. Final image should be an ultra-realistic, 8k professional headshot."""

PROMPT_MEN = """Keep the facial features of the person in the uploaded image exactly consistent . Dress them in a professional  black business suit  with a white shirt  and a tie, similar to the reference image. Background : Place the subject against a clean, solid dark gray studio photography backdrop . The background should have a subtle gradient , slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style : Shot on a Sony A7III with an 85mm f/1.4 lens , creating a flattering portrait compression. Lighting : Use a classic three-point lighting setup . The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details : Render natural skin texture with visible pores , not an airbrushed look. Add natural catchlights to the eyes . The fabric of the suit should show a subtle wool texture.Final image should be an ultra-realistic, 8k professional headshot."""

