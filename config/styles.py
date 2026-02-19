"""Custom CSS for modern UI - Google AI Studio style."""

CUSTOM_CSS = """
    <style>
        /* Google AI Studio inspired color scheme - Theme Aware */
        :root {
            --ai-studio-panel-bg: rgba(128, 128, 128, 0.05);
            --ai-studio-border: rgba(128, 128, 128, 0.2);
            --ai-studio-primary: #1a73e8;
            --ai-studio-primary-hover: #1557b0;
        }
        
        /* Settings panel styling */
        .settings-panel {
            padding: 1rem;
        }
        
        /* Sidebar styling improvements */
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--ai-studio-border);
        }

        /* Card-like containers - respect theme */
        div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlock"] > .stElementContainer {
            /* padding: 0.5rem 0; */
        }
        
        /* Better containers */
        .stContainer {
            border: 1px solid var(--ai-studio-border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Button styling - Material Design inspired */
        .stButton > button {
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s ease;
            padding: 0.5rem 1rem;
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
        .status-completed { color: #34a853; font-weight: 500; }
        .status-failed { color: #ea4335; font-weight: 500; }
        
        /* Chat layout styling */
        .stChatMessage {
            margin-bottom: 1rem;
        }
        
        /* Create scrollable container for chat messages */
        .chat-messages-scrollable {
            max-height: calc(100vh - 350px);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1rem 0;
            margin-bottom: 1rem;
            scroll-behavior: smooth;
        }
        
        /* Custom scrollbar - Theme Aware */
        .chat-messages-scrollable::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-messages-scrollable::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .chat-messages-scrollable::-webkit-scrollbar-thumb {
            background: rgba(128, 128, 128, 0.3);
            border-radius: 10px;
        }
        
        .chat-messages-scrollable::-webkit-scrollbar-thumb:hover {
            background: rgba(128, 128, 128, 0.5);
        }

        /* Empty state styling */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            opacity: 0.6;
        }

        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        /* Model badge styling */
        .model-badge {
            background-color: var(--ai-studio-primary);
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 1rem;
        }
        
        .sidebar-section-label {
            font-size: 0.75rem;
            color: gray;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 1.5rem 0 0.5rem 0;
            font-weight: 600;
        }

        /* Stepper UI */
        .stepper-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--ai-studio-panel-bg);
            border-radius: 8px;
            border: 1px solid var(--ai-studio-border);
        }

        .step-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
        }

        .step-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: var(--ai-studio-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 0.5rem;
            z-index: 2;
        }

        .step-circle.active {
            background: var(--ai-studio-primary);
            color: white;
        }

        .step-label {
            font-size: 0.8rem;
            text-align: center;
        }
    </style>
"""
