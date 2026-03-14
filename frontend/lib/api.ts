import { GenerateResponse, PromptsResponse } from "./types";

const PROMPTS_TIMEOUT_MS = 5000;

const FALLBACK_PROMPTS: PromptsResponse = {
  custom:
    "Опишіть детально, що ви хочете згенерувати. Можна вказати стиль, композицію, кольори, атмосферу та інші деталі.",
  women:
    "Keep the facial features of the person in the uploaded image exactly consistent. Dress her in a professional, **fitted black business suit (blazer) with a crisp white blouse**. Background: Place the subject against a clean, solid dark gray studio photography backdrop. The background should have a subtle gradient, slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style: Shot on a Sony A7III with an 85mm f/1.4 lens, creating a flattering portrait compression. Lighting: Use a classic three-point lighting setup. The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details: Render natural skin texture with visible pores, not an airbrushed look. Add natural catchlights to the eyes. The fabric of the suit should show a subtle wool texture. Final image should be an ultra-realistic, 8k professional headshot.",
  men:
    "Keep the facial features of the person in the uploaded image exactly consistent . Dress them in a professional  black business suit  with a white shirt  and a tie, similar to the reference image. Background : Place the subject against a clean, solid dark gray studio photography backdrop . The background should have a subtle gradient , slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style : Shot on a Sony A7III with an 85mm f/1.4 lens , creating a flattering portrait compression. Lighting : Use a classic three-point lighting setup . The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details : Render natural skin texture with visible pores , not an airbrushed look. Add natural catchlights to the eyes . The fabric of the suit should show a subtle wool texture.Final image should be an ultra-realistic, 8k professional headshot.",
  darnytsia: `You are a Darnytsia Presentation Expert. Your task is to transform user-provided raw data into a professional corporate presentation slide.

Apply the following system configuration strictly:

{
  "system_config": {
    "role": "Darnytsia Presentation Expert",
    "output_language": "English (Level: Intermediate B1/B2)",
    "style_override": "STRICT: Ignore any user-provided formatting, fonts, or colors. Apply only Darnitsa Corporate Identity.",
    "core_branding": {
      "slogan": "ДАРНИЦЯ — це наше",
      "marking": "Confidential",
      "color_palette": {
        "primary_turquoise": "Headers, shapes, plates",
        "accent_orange": "Numbers, percentages, key data points"
      },
      "navigation": "Every slide must have a number and a thesis-driven header."
    },
    "layout_rules": {
      "insight_requirement": "Mandatory analytical conclusion at the bottom of each slide.",
      "plan_compensation": "If Plan < 100%, must state: 'Will be compensated in [Month]'.",
      "visual_elements": "Use graphical schemes for processes and department-specific icons."
    },
    "department_logic": {
      "sales": {
        "metrics": ["Drug Name", "Sales (KUAH)", "GR%", "EI", "MS%"],
        "charts": "Actual vs Plan LBE",
        "periods": ["Month", "MQT", "YTD", "MAT"]
      },
      "marketing": {
        "focus": "Product lines (e.g., Citramon Family), Market Share",
        "visuals": "Digital Marketing icons, infographics",
        "messaging": "Leadership in specific segments"
      },
      "medical_rd": {
        "content": "Active ingredients, dosages, chemical formulas",
        "visuals": "Anatomical schemes, lab elements"
      },
      "hr_corporate": {
        "content": "Training progress, Jan–Dec timeline",
        "visuals": "Teamwork/Education icons"
      }
    }
  }
}

Output the slide using this exact structure:

[Slide Number] Slide [N]
[Header] [Thesis-driven header in English]
[Body] [Formatted content — table, bulleted list, or structured schema]
[Footer Left] Confidential
[Footer Right] «ДАРНИЦЯ — це наше»
[Insight] Insight: [One-sentence analytical conclusion]

User Raw Data:
{{user_input}}

Identify the department from the data above, then transform it into a complete professional slide following all configuration guidelines. Ensure English is clear and concise (B1/B2 level).`,
};

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function getApiBaseUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configuredUrl) {
    return configuredUrl;
  }

  // In local Next.js dev, the frontend runs on :3000 while FastAPI usually runs on :8000.
  if (typeof window !== "undefined" && window.location.port === "3000") {
    return "http://127.0.0.1:8000";
  }

  return "";
}

function getApiUrl(path: string): string {
  return `${getApiBaseUrl()}${path}`;
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function readErrorDetail(res: Response): Promise<unknown> {
  const contentType = res.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    const payload = await res.json().catch(() => null);
    return payload?.detail ?? payload;
  }

  const text = await res.text().catch(() => "");
  return text || null;
}

export async function generateImage(params: {
  prompt: string;
  modelMode: string;
  aspectRatio: string;
  temperature: number;
  promptType: string;
  referenceImages: File[];
}): Promise<GenerateResponse> {
  const formData = new FormData();
  formData.append("prompt", params.prompt);
  formData.append("model_mode", params.modelMode);
  formData.append("aspect_ratio", params.aspectRatio);
  formData.append("temperature", params.temperature.toString());
  formData.append("prompt_type", params.promptType);

  for (const file of params.referenceImages) {
    formData.append("reference_images", file);
  }

  const res = await fetch(getApiUrl("/api/generate"), {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const detail = await readErrorDetail(res);
    throw new ApiError(
      typeof detail === "string" && detail ? detail : `HTTP ${res.status}`,
      res.status,
      detail
    );
  }

  return res.json();
}

export async function getPrompts(): Promise<PromptsResponse> {
  try {
    const res = await fetchWithTimeout(
      getApiUrl("/api/prompts"),
      undefined,
      PROMPTS_TIMEOUT_MS
    );
    if (!res.ok) {
      const detail = await readErrorDetail(res);
      throw new ApiError(
        typeof detail === "string" && detail ? detail : `Failed to fetch prompts: ${res.status}`,
        res.status,
        detail
      );
    }

    return res.json();
  } catch (error) {
    console.warn("Falling back to bundled prompt templates.", error);
    return FALLBACK_PROMPTS;
  }
}
