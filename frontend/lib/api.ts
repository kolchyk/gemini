import { GenerateResponse, PromptsResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

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

  const res = await fetch(`${API_URL}/api/generate`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function getPrompts(): Promise<PromptsResponse> {
  const res = await fetch(`${API_URL}/api/prompts`);
  if (!res.ok) {
    throw new Error(`Failed to fetch prompts: ${res.status}`);
  }
  return res.json();
}
