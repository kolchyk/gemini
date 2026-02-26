# 2026-02-26 - Gemini Model Separator and Parameter Fix Design

## Problem Statement
The application currently throws a `400 INVALID_ARGUMENT` when using `gemini-3.1-flash-image-preview` with the `thinking_level` parameter. This model does not support thinking configurations, while its counterpart `gemini-3-pro-image-preview` does. Users also need a clearer separation between these models in the UI to understand their capabilities.

## Goals
-   Fix the `INVALID_ARGUMENT` error by conditionally passing `thinking_level`.
-   Organize the sidebar to clearly distinguish between "Flash" and "Pro" model families.
-   Dynamically hide parameters (like "Thinking") for models that do not support them.

## Proposed Design

### 1. Data Model & Configuration
The system will recognize two primary models in the "Banana" family:
-   **Nano Banana 2 (Flash)**: `gemini-3.1-flash-image-preview`
    -   *No Thinking support*.
-   **Banana Pro (Pro)**: `gemini-3-pro-image-preview`
    -   *Full Thinking support*.

We will remove any legacy references to `gemini-2.5-flash-image` or `imagen-4.0`.

### 2. UI/UX: Sidebar Reorganization
The sidebar will be reorganized into two sections:
-   **Model Family Selection**: Radio buttons or a clear selectbox to choose between "Flash", "Pro", and "Both (Parallel)".
-   **Contextual Parameters**:
    -   `Aspect Ratio` and `Resolution` will always be visible.
    -   `Thinking Level` will **only** be visible if "Pro" or "Both" is selected.
    -   `Person Generation` will be hidden for these Gemini models (as they use native safety filters).

### 3. Service Layer Logic
The `ImageService.generate_image` method will be updated to:
-   Check the model name before creating `types.ThinkingConfig`.
-   Only attach `ThinkingConfig` if the model name contains "pro" or specifically matches `gemini-3-pro-image-preview`.
-   Ensure that in "Both" mode, two separate config objects are generated for the two model calls.

## Implementation Details

### `components/image_generator.py`
-   Refactor `render_image_sidebar` to:
    -   Use `st.radio` for model mode.
    -   Add conditional `st.selectbox` for `image_thinking_level` based on mode.
-   Update `_render_generate_button` to correctly pass `None` for `thinking_level` if the model doesn't support it.

### `services/image_service.py`
-   Refine `generate_image` to avoid `INVALID_ARGUMENT` by checking model capabilities before adding `thinking_config`.

## Testing Plan
-   Verify that "Flash" mode no longer triggers the `400 INVALID_ARGUMENT` error.
-   Verify that "Pro" mode correctly uses the selected "Thinking" level.
-   Verify that "Both" mode executes two parallel requests with their respective appropriate configurations.
