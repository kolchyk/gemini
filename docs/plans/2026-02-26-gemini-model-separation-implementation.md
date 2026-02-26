# Gemini Model Separation and Thinking Parameter Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the `INVALID_ARGUMENT` error for Flash models and reorganize the sidebar to clearly separate Flash and Pro model families.

**Architecture:** Use conditional rendering in Streamlit to show/hide parameters based on model family and update the service layer to avoid sending unsupported configurations to specific models.

**Tech Stack:** Streamlit, Google GenAI SDK, Python.

---

### Task 1: Update Configuration
Remove unneeded models and simplify the model list to focus on Nano Banana 2 and Banana Pro.

**Files:**
- Modify: `config/settings.py:12-16`

**Step 1: Write the minimal implementation**

```python
# config/settings.py

# ... existing code ...
# Imagen models use generate_images() API; Gemini image models use generate_content_stream()
IMAGEN_MODELS = ()  # Standard Imagen 3/4 models
GEMINI_IMAGE_MODELS = ("gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview")
IMAGE_MODELS = GEMINI_IMAGE_MODELS
IMAGE_MODEL = "gemini-3-pro-image-preview"  # Banana Pro
# ... existing code ...
```

**Step 2: Commit**

```bash
git add config/settings.py
git commit -m "config: simplify image models to flash and pro only"
```

---

### Task 2: Fix ImageService Thinking Logic
Update `ImageService` to only include `ThinkingConfig` for models that support it.

**Files:**
- Modify: `services/image_service.py:102-118`
- Test: `tests/unit/test_image_service.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_image_service.py
# (Assume basic test structure exists)
def test_generate_image_no_thinking_for_flash(image_service, mocker):
    mock_generate = mocker.patch.object(image_service.client.models, 'generate_content_stream')
    image_service.generate_image(
        prompt="test",
        model="gemini-3.1-flash-image-preview",
        thinking_level="HIGH"
    )
    # Check that thinking_config is NOT in the call
    args, kwargs = mock_generate.call_args
    assert kwargs['config'].thinking_config is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_image_service.py -v`
Expected: FAIL (currently it always adds thinking_config if "gemini-3" is in name)

**Step 3: Write minimal implementation**

```python
# services/image_service.py

# ...
        # Determine thinking config based on model generation
        thinking_config = None
        # Only Pro models support thinking_level
        if "pro" in model_name.lower() and "gemini-3" in model_name.lower():
            thinking_config = types.ThinkingConfig(thinking_level=thinking_level)

        # Config following Google reference code pattern
        generate_content_config = types.GenerateContentConfig(
            thinking_config=thinking_config,
# ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_image_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add services/image_service.py
git commit -m "fix: only send thinking_config to pro models"
```

---

### Task 3: Reorganize Sidebar and Dynamic Parameters
Update the sidebar to group models and show/hide the "Thinking" parameter.

**Files:**
- Modify: `components/image_generator.py:9-92`

**Step 1: Write minimal implementation for sidebar reorganization**

```python
# components/image_generator.py

def render_image_sidebar():
    """Renders the sidebar for image generator."""
    with st.sidebar:
        # Dynamic badge based on selected mode
        mode = st.session_state.get('image_generation_mode', 'Pro')
        badge_text = f"🍌 Banana {mode}" if mode != "Обидві" else "🍌 Banana (Dual)"
        st.markdown(f'<div class="model-badge">{badge_text}</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-label">Модель</div>', unsafe_allow_html=True)
        image_generation_mode = st.radio(
            "Оберіть серію:",
            options=["Flash", "Pro", "Обидві"],
            index=["Flash", "Pro", "Обидві"].index(mode),
            key="image_generation_mode_selector"
        )
        st.session_state['image_generation_mode'] = image_generation_mode

        # Update underlying image_model
        if image_generation_mode == "Flash":
            st.session_state['image_model'] = "gemini-3.1-flash-image-preview"
        elif image_generation_mode == "Pro":
            st.session_state['image_model'] = "gemini-3-pro-image-preview"

        st.markdown('<div class="sidebar-section-label">Параметри</div>', unsafe_allow_html=True)

        # ... (aspect_ratio and resolution selectboxes) ...
        # [Keep existing aspect_ratio and resolution code]

        # Conditional Thinking Level
        if image_generation_mode in ["Pro", "Обидві"]:
            st.markdown('<div class="sidebar-section-label">Розширені (Pro)</div>', unsafe_allow_html=True)
            thinking_level = st.selectbox(
                "Thinking:",
                options=["MINIMAL", "LOW", "MEDIUM", "HIGH"],
                index=["MINIMAL", "LOW", "MEDIUM", "HIGH"].index(
                    st.session_state.get('image_thinking_level', settings.IMAGE_DEFAULT_THINKING_LEVEL)
                ),
                key="image_thinking_level_selector"
            )
            st.session_state['image_thinking_level'] = thinking_level
        else:
            # Set to default for non-pro if needed, though service will ignore it
            st.session_state['image_thinking_level'] = "MINIMAL"

        # ... (rest of sidebar: reset button, documentation) ...
```

**Step 2: Commit**

```bash
git add components/image_generator.py
git commit -m "feat: reorganize sidebar and add dynamic thinking parameter"
```

---

### Task 4: Final Verification
Run the application and verify parallel generation.

**Step 1: Verify parallel generation logic**

Ensure `_render_generate_button` in `components/image_generator.py` correctly handles the models:

```python
# components/image_generator.py

# ... in _render_generate_button ...
                    flash_model = "gemini-3.1-flash-image-preview"
                    pro_model = "gemini-3-pro-image-preview"
                    
                    if mode == "Flash":
                        target_models = [flash_model]
                    elif mode == "Pro":
                        target_models = [pro_model]
                    else:  # "Обидві"
                        target_models = [flash_model, pro_model]
# ...
```

**Step 2: Commit**

```bash
git add components/image_generator.py
git commit -m "feat: ensure correct model naming in generation button"
```
