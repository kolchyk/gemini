"""Custom CSS for modern UI — Nano Banana 2 style."""

CUSTOM_CSS = """
    <style>
        /* Theme Aware color scheme */
        :root {
            --ai-studio-panel-bg: rgba(128, 128, 128, 0.05);
            --ai-studio-border: rgba(128, 128, 128, 0.2);
            --ai-studio-primary: #1a73e8;
            --ai-studio-primary-hover: #1557b0;
        }

        /* ── App Header ── */
        .app-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0 1.5rem 0;
            border-bottom: 1px solid var(--ai-studio-border);
            margin-bottom: 1.5rem;
        }

        .app-logo {
            font-size: 2rem;
        }

        .app-title {
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .app-subtitle {
            font-size: 0.8rem;
            color: gray;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-left: auto;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--ai-studio-border);
        }

        .sidebar-section-label {
            font-size: 0.7rem;
            color: gray;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 1.5rem 0 0.75rem 0;
            font-weight: 700;
            padding-bottom: 0.25rem;
            border-bottom: 1px solid var(--ai-studio-border);
        }

        /* ── Model Badge ── */
        .model-badge {
            background: linear-gradient(135deg, var(--ai-studio-primary), #4285f4);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 10px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(26, 115, 232, 0.2);
            letter-spacing: 0.3px;
        }

        /* ── Section Cards ── */
        .section-card {
            background: var(--ai-studio-panel-bg);
            border: 1px solid var(--ai-studio-border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* ── Buttons ── */
        .stButton > button {
            border-radius: 4px;
            font-weight: 500;
            transition: all 0.2s ease;
            padding: 0.5rem 1rem;
        }

        button[kind="primary"] {
            background-color: var(--ai-studio-primary) !important;
            color: white !important;
            border: none !important;
        }

        button[kind="primary"]:hover {
            background-color: var(--ai-studio-primary-hover) !important;
            box-shadow: 0 2px 4px rgba(26, 115, 232, 0.3) !important;
        }

        /* ── Empty State ── */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            background: linear-gradient(135deg, var(--ai-studio-panel-bg) 0%, transparent 100%);
            border: 1px dashed var(--ai-studio-border);
            border-radius: 16px;
            margin: 2rem 0;
        }

        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            display: block;
            animation: float 3s ease-in-out infinite;
        }

        .empty-state h3 {
            margin-bottom: 0.5rem;
            font-weight: 600;
        }

        .empty-state p {
            opacity: 0.6;
            max-width: 400px;
            margin: 0 auto;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }

        /* ── Spacing ── */
        .spacer-lg { margin-bottom: 2rem; }
    </style>
"""
