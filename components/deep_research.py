import streamlit as st
from services.research_service import research_service
from config import settings

def render_research_sidebar():
    """Renders the sidebar for deep research."""
    with st.sidebar:
        st.markdown('<div class="model-badge">🔍 deep-research-pro-preview</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section-label">Керування</div>', unsafe_allow_html=True)
        
        if st.button("⚠️ Скинути все дослідження", use_container_width=True, type="secondary"):
            for key in [
                "plan_id", "plan_text", "tasks", "research_id", 
                "research_text", "synthesis_text", "infographic"
            ]:
                st.session_state[key] = [] if key == "tasks" else None
            st.rerun()

        st.markdown('<div class="sidebar-section-label">Документація</div>', unsafe_allow_html=True)
        st.markdown("""
        - [Deep Research Guide](https://ai.google.dev/gemini-api/docs/deep-research)
        
        *Deep Research Agent автономно планує та виконує дослідження.*
        """, unsafe_allow_html=True)

def render_deep_research():
    """Renders the Deep Research Agent UI component."""
    
    # Initialize session state for research planner
    for key in [
        "plan_id",
        "plan_text",
        "tasks",
        "research_id",
        "research_text",
        "synthesis_text",
        "infographic",
    ]:
        if key not in st.session_state:
            st.session_state[key] = [] if key == "tasks" else None

    st.subheader("🔍 Deep Research Agent")

    # Stepper UI
    step1_active = "active" if not st.session_state['plan_id'] else ""
    step2_active = "active" if st.session_state['plan_id'] and not st.session_state['research_id'] else ""
    step3_active = "active" if st.session_state['research_id'] else ""

    st.markdown(f"""
        <div class="stepper-container">
            <div class="step-item">
                <div class="step-circle {step1_active}">1</div>
                <div class="step-label">Планування</div>
            </div>
            <div style="flex: 1; height: 2px; background: var(--ai-studio-border); margin-bottom: 1.5rem;"></div>
            <div class="step-item">
                <div class="step-circle {step2_active}">2</div>
                <div class="step-label">Дослідження</div>
            </div>
            <div style="flex: 1; height: 2px; background: var(--ai-studio-border); margin-bottom: 1.5rem;"></div>
            <div class="step-item">
                <div class="step-circle {step3_active}">3</div>
                <div class="step-label">Звіт та Аналіз</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Step 1: Research Goal & Planning
    with st.expander("📍 Крок 1: Мета дослідження та Планування", expanded=not st.session_state['plan_id']):
        research_goal = st.text_area(
            "Опишіть тему для глибокого дослідження:",
            placeholder="Наприклад: 'Аналіз ринку електромобілів в Україні 2024-2025'...",
            height=100
        )
        
        if st.button("📝 Скласти план дослідження", type="primary", use_container_width=True):
            if not research_goal:
                st.error("Будь ласка, введіть тему дослідження!")
            else:
                with st.spinner("⏳ Gemini розробляє стратегію дослідження..."):
                    try:
                        plan_id, plan_text, tasks = research_service.generate_plan(research_goal)
                        st.session_state['plan_id'] = plan_id
                        st.session_state['plan_text'] = plan_text
                        st.session_state['tasks'] = tasks
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # Step 2: Task Selection & Research Execution
    if st.session_state['plan_text']:
        with st.expander("🕵️ Крок 2: Виконання дослідження", expanded=not st.session_state['research_id']):
            st.markdown("### План дослідження")
            st.info("Оберіть пункти плану для детального вивчення:")
            
            selected_task_indices = []
            for i, task in enumerate(st.session_state['tasks']):
                if st.checkbox(f"{task['num']}. {task['text']}", value=True, key=f"task_{i}"):
                    selected_task_indices.append(i)
            
            if st.button("🚀 Запустити Deep Research", type="primary", use_container_width=True):
                if not selected_task_indices:
                    st.error("Оберіть хоча б одне завдання!")
                else:
                    selected_tasks = [
                        f"{st.session_state['tasks'][i]['num']}. {st.session_state['tasks'][i]['text']}" 
                        for i in selected_task_indices
                    ]
                    with st.spinner("🔍 Deep Research Agent працює... Це може зайняти кілька хвилин."):
                        try:
                            research_id, research_text = research_service.start_deep_research(
                                selected_tasks, 
                                st.session_state['plan_id']
                            )
                            st.session_state['research_id'] = research_id
                            st.session_state['research_text'] = research_text
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

    # Step 3: Synthesis & Reporting
    if st.session_state['research_text']:
        with st.expander("📊 Крок 3: Синтез та Звіт", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✍️ Створити фінальний звіт", type="primary", use_container_width=True):
                    with st.spinner("📝 Формуємо аналітичний звіт..."):
                        try:
                            synthesis = research_service.generate_report(
                                st.session_state['research_text'],
                                st.session_state['research_id']
                            )
                            st.session_state['synthesis_text'] = synthesis
                        except Exception as e:
                            st.error(str(e))
            
            with col_b:
                if st.button("🖼️ Згенерувати інфографіку (TL;DR)", use_container_width=True):
                    content_for_infographic = st.session_state['synthesis_text'] or st.session_state['research_text']
                    with st.spinner("🎨 Малюємо візуальне резюме..."):
                        infographic = research_service.generate_infographic(content_for_infographic)
                        if infographic:
                            st.session_state['infographic'] = infographic
                        else:
                            st.error("Не вдалося згенерувати інфографіку.")

            if st.session_state['synthesis_text']:
                st.markdown("---")
                st.markdown("### 📄 Фінальний звіт")
                st.markdown(st.session_state['synthesis_text'])
                st.download_button(
                    "📥 Завантажити звіт (.md)",
                    st.session_state['synthesis_text'],
                    file_name="research_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            if st.session_state['infographic']:
                st.markdown("---")
                st.markdown("### 🎨 Візуальне резюме (TL;DR)")
                st.image(st.session_state['infographic'], use_container_width=True)
            
            with st.expander("Переглянути сирі дані дослідження"):
                st.markdown(st.session_state['research_text'])

