import time
import re
import streamlit as st
from services.gemini_client import get_gemini_client
from config import settings

class ResearchService:
    def __init__(self):
        self.client = get_gemini_client()

    def get_text(self, outputs):
        return "\n".join(
            output.text for output in (outputs or []) if hasattr(output, 'text') and output.text
        ) or ""

    def parse_tasks(self, text):
        return [
            {"num": match.group(1), "text": match.group(2).strip().replace('\n', ' ')}
            for match in re.finditer(
                r'^(\d+)[\.\)\-]\s*(.+?)(?=\n\d+[\.\)\-]|\n\n|\Z)',
                text,
                re.MULTILINE | re.DOTALL
            )
        ]

    def wait_for_completion(self, interaction_id, timeout=300):
        progress, status, elapsed = st.progress(0), st.empty(), 0
        while elapsed < timeout:
            interaction = self.client.interactions.get(interaction_id)
            if interaction.status != "in_progress":
                progress.progress(100)
                return interaction
            elapsed += 3
            progress.progress(min(90, int(elapsed / timeout * 100)))
            status.text(f"⏳ {elapsed}s...")
            time.sleep(3)
        return self.client.interactions.get(interaction_id)

    def generate_plan(self, research_goal):
        try:
            interaction = self.client.interactions.create(
                model="gemini-3-flash-preview",
                input=(
                    f"Create a numbered research plan for: {research_goal}\n\n"
                    "Format: 1. [Task] - [Details]\n\nInclude 5-8 specific tasks."
                ),
                tools=[{"type": "google_search"}],
                store=True,
            )
            plan_text = self.get_text(interaction.outputs)
            tasks = self.parse_tasks(plan_text)
            return interaction.id, plan_text, tasks
        except Exception as e:
            raise Exception(f"Помилка при створенні плану: {str(e)}")

    def start_deep_research(self, selected_tasks, plan_id):
        try:
            interaction = self.client.interactions.create(
                agent="deep-research-pro-preview-12-2025",
                input=(
                    "Research these tasks thoroughly with sources:\n\n"
                    + "\n\n".join(selected_tasks)
                ),
                previous_interaction_id=plan_id,
                background=True,
                store=True,
            )
            interaction = self.wait_for_completion(interaction.id)
            research_text = self.get_text(interaction.outputs) or f"Status: {interaction.status}"
            return interaction.id, research_text
        except Exception as e:
            raise Exception(f"Помилка при запуску глибокого дослідження: {str(e)}")

    def check_research_status(self, interaction_id):
        """Poll for status updates (similar to research_agent.py)"""
        try:
            interaction = self.client.interactions.get(interaction_id)
            status = interaction.status
            
            result = None
            error = None
            
            if status == "completed":
                result = self.get_text(interaction.outputs)
            elif status == "failed":
                if hasattr(interaction, 'error'):
                    error = str(interaction.error)
                else:
                    error = "Дослідження завершилося з помилкою (деталі недоступні)"
            
            return status, result, error
        except Exception as e:
            raise Exception(f"Помилка при перевірці статусу: {str(e)}")

    def generate_report(self, research_text, research_id):
        try:
            interaction = self.client.interactions.create(
                model="gemini-3.1-pro-preview",
                input=(
                    "Create executive report with Summary, Findings, "
                    "Recommendations, Risks:\n\n"
                    f"{research_text}"
                ),
                previous_interaction_id=research_id,
                store=True,
            )
            return self.get_text(interaction.outputs)
        except Exception as e:
            raise Exception(f"Помилка при створенні звіту: {str(e)}")

    def generate_infographic(self, report_text):
        try:
            response = self.client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=(
                    "Create a whiteboard summary infographic for the following: "
                    f"{report_text}"
                ),
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return part.inline_data.data
            return None
        except Exception as e:
            print(f"Infographic error: {e}")
            return None

research_service = ResearchService()
