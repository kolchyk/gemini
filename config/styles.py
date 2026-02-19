"""Custom CSS for modern UI - Google AI Studio style."""

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
        
        /* Settings panel styling */
        .settings-panel {
            padding: 1rem;
            height: 100%;
            position: sticky;
            top: 0;
        }
        
        .settings-panel h3 {
            font-size: 0.875rem;
            font-weight: 500;
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
        
        /* Card-like containers - respect theme */
        .stContainer > div {
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
            padding: 0.625rem 1rem;
            font-size: 0.875rem;
        }
        
        .stButton > button:hover {
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        
        /* Primary button - Google blue */
        button[kind="primary"] {
            background-color: var(--ai-studio-primary) !important;
            color: white !important;
            border: none !important;
        }
        
        button[kind="primary"]:hover {
            background-color: var(--ai-studio-primary-hover) !important;
            box-shadow: 0 2px 4px rgba(26, 115, 232, 0.3) !important;
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
        
        /* Ensure chat input container stays at bottom - theme aware */
        div[data-testid="stChatInputContainer"],
        div[data-testid="stChatInputContainer"] > div {
            position: sticky !important;
            bottom: 0 !important;
            z-index: 100 !important;
            padding-top: 1rem !important;
            border-top: 1px solid var(--ai-studio-border) !important;
            margin-top: auto !important;
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
        /* Model badge styling */
        .model-badge {
            background-color: var(--ai-studio-primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(26, 115, 232, 0.2);
        }
        
        .model-container {
            margin-bottom: 1.5rem;
            padding: 0.5rem;
            border-bottom: 1px solid var(--ai-studio-border);
        }
        
        .model-label {
            font-size: 0.75rem;
            color: var(--ai-studio-text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.25rem;
        }
    </style>
"""
