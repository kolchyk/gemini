"""Deep Research Agent helper functions."""


def start_research(query, client):
    """Initialize research interaction"""
    try:
        initial_interaction = client.interactions.create(
            input=query,
            agent="deep-research-pro-preview-12-2025",
            background=True,
            store=True
        )
        return initial_interaction.id, "pending"
    except Exception as e:
        raise Exception(f"Помилка при запуску дослідження: {str(e)}")


def check_research_status(interaction_id, client):
    """Poll for status updates"""
    try:
        interaction = client.interactions.get(interaction_id)
        status = interaction.status
        
        result = None
        error = None
        
        if status == "completed" and hasattr(interaction, 'outputs') and interaction.outputs:
            result = interaction.outputs[-1].text if hasattr(interaction.outputs[-1], 'text') else str(interaction.outputs[-1])
        elif status == "failed":
            # Extract error message as shown in documentation
            if hasattr(interaction, 'error'):
                error = str(interaction.error)
            else:
                error = "Дослідження завершилося з помилкою (деталі недоступні)"
        
        return status, result, error
    except Exception as e:
        raise Exception(f"Помилка при перевірці статусу: {str(e)}")

