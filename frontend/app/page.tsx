"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import dynamic from "next/dynamic";
import { toast } from "sonner";
import { Header } from "@/components/header";
import { ControlsRow } from "@/components/controls-row";
import { ReferenceUpload } from "@/components/reference-upload";
import { PromptSection } from "@/components/prompt-section";
import { Button } from "@/components/ui/button";
import { ApiError, getGenerateJobStatus, getPrompts, submitGenerateJob } from "@/lib/api";
import type {
  AspectRatio,
  GenerateJobStatusResponse,
  GenerationJobStatus,
  GenerationResult,
  ImageResolution,
  ModelMode,
  PromptType,
  PromptsResponse,
} from "@/lib/types";

const ResultSection = dynamic(
  () => import("@/components/result-section").then((mod) => mod.ResultSection)
);

export default function Home() {
  const [modelMode, setModelMode] = useState<ModelMode>("Flash");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("16:9");
  const [resolution, setResolution] = useState<ImageResolution>("1K");
  const [temperature, setTemperature] = useState(1.0);
  const [promptType, setPromptType] = useState<PromptType>("custom");
  const [prompt, setPrompt] = useState("");
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const [results, setResults] = useState<Record<string, GenerationResult> | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobStatus, setJobStatus] = useState<GenerationJobStatus | null>(null);
  const [defaultPrompts, setDefaultPrompts] = useState<PromptsResponse | null>(null);
  const [isPromptsLoading, setIsPromptsLoading] = useState(false);
  const [retryCountdown, setRetryCountdown] = useState<number | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const promptsRequestRef = useRef<Promise<PromptsResponse | null> | null>(null);
  const generationRunRef = useRef(0);

  // Sync prompt when defaultPrompts arrive if currently empty
  useEffect(() => {
    if (defaultPrompts && prompt === "") {
      if (promptType !== "custom") {
        setPrompt(defaultPrompts[promptType]);
      }
    }
  }, [defaultPrompts, promptType, prompt]);

  const ensurePromptsLoaded = useCallback(async () => {
    if (defaultPrompts) {
      return defaultPrompts;
    }

    if (promptsRequestRef.current) {
      return promptsRequestRef.current;
    }

    setIsPromptsLoading(true);
    promptsRequestRef.current = getPrompts()
      .then((prompts) => {
        setDefaultPrompts(prompts);
        return prompts;
      })
      .catch((err) => {
        console.error("Failed to load prompts:", err);
        toast.error("Не вдалося завантажити шаблони промптів");
        return null;
      })
      .finally(() => {
        promptsRequestRef.current = null;
        setIsPromptsLoading(false);
      });

    return promptsRequestRef.current;
  }, [defaultPrompts]);

  const handlePromptTypeChange = useCallback(
    async (type: PromptType) => {
      if (type === "custom") {
        setPromptType(type);
        setPrompt("");
        return;
      }

      const prompts = defaultPrompts ?? (await ensurePromptsLoaded());
      if (prompts) {
        setPromptType(type);
        setPrompt(prompts[type]);
      }
    },
    [defaultPrompts, ensurePromptsLoaded]
  );

  const stopRetryTimer = useCallback(() => {
    if (retryTimerRef.current) {
      clearInterval(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    setRetryCountdown(null);
  }, []);

  const startRetryTimer = useCallback(() => {
    stopRetryTimer();
    setRetryCountdown(30);
    retryTimerRef.current = setInterval(() => {
      setRetryCountdown((prev) => {
        if (prev === null || prev <= 1) {
          stopRetryTimer();
          return null;
        }
        return prev - 1;
      });
    }, 1000);
  }, [stopRetryTimer]);

  // Auto-retry when countdown reaches 0
  const pendingRetryRef = useRef(false);
  useEffect(() => {
    if (retryCountdown === null && pendingRetryRef.current) {
      pendingRetryRef.current = false;
      handleGenerate();
    }
  });

  const pollGenerationJob = useCallback(
    async (jobId: string, runId: number): Promise<GenerateJobStatusResponse> => {
      while (generationRunRef.current === runId) {
        const response = await getGenerateJobStatus(jobId);

        if (generationRunRef.current !== runId) {
          throw new Error("Generation was cancelled.");
        }

        setJobStatus(response.status);
        if (response.status === "completed" || response.status === "failed") {
          return response;
        }

        await new Promise((resolve) => window.setTimeout(resolve, 1500));
      }

      throw new Error("Generation was cancelled.");
    },
    []
  );

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Будь ласка, введіть промпт!");
      return;
    }

    stopRetryTimer();
    generationRunRef.current += 1;
    const runId = generationRunRef.current;
    setIsGenerating(true);
    setJobStatus("queued");
    setResults(null);

    try {
      const submission = await submitGenerateJob({
        prompt,
        modelMode,
        aspectRatio,
        resolution,
        temperature,
        promptType,
        referenceImages: referenceFiles,
      });
      setJobStatus(submission.status);

      const response = await pollGenerationJob(submission.job_id, runId);
      if (response.status === "failed") {
        throw new Error(response.error || "Генерація завершилася з помилкою.");
      }

      const responseResults = response.results ?? {};

      // Check if all results are errors (no images)
      const hasAnyImage = Object.values(responseResults).some(
        (r) => r.image_base64 !== null
      );

      if (!hasAnyImage) {
        // All models failed — start retry countdown
        setResults(responseResults);
        toast.error("Всі моделі повернули помилку. Автоповтор через 30 сек...");
        pendingRetryRef.current = true;
        startRetryTimer();
      } else {
        setResults(responseResults);
        if (response.fallback_used) {
          toast.success("Основна модель недоступна — використано резервну.");
        } else {
          toast.success("Зображення згенеровано!");
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        console.error("Image generation API error:", {
          message: err.message,
          status: err.status,
          detail: err.detail,
        });
      } else {
        console.error("Image generation failed:", err);
      }

      const message = err instanceof Error ? err.message : "Unknown error";
      toast.error(message);
      pendingRetryRef.current = true;
      startRetryTimer();
    } finally {
      if (generationRunRef.current === runId) {
        setIsGenerating(false);
      }
    }
  };

  const handleClear = () => {
    setResults(null);
  };

  const buttonLabel =
    modelMode === "Both"
      ? "🚀 Згенерувати зображення (паралельно)"
      : "🚀 Згенерувати зображення";

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <Header />

      <div className="space-y-6">
        <ControlsRow
          modelMode={modelMode}
          aspectRatio={aspectRatio}
          resolution={resolution}
          temperature={temperature}
          onModelModeChange={setModelMode}
          onAspectRatioChange={setAspectRatio}
          onResolutionChange={setResolution}
          onTemperatureChange={setTemperature}
        />

        <ReferenceUpload files={referenceFiles} onFilesChange={setReferenceFiles} />

        <PromptSection
          promptType={promptType}
          prompt={prompt}
          defaultPrompts={defaultPrompts}
          isLoadingPrompts={isPromptsLoading}
          onPromptTypeChange={handlePromptTypeChange}
          onPromptChange={setPrompt}
        />

        <div className="flex gap-3">
          <Button
            size="lg"
            className="flex-1"
            onClick={() => { stopRetryTimer(); pendingRetryRef.current = false; handleGenerate(); }}
            disabled={isGenerating}
          >
            {isGenerating
              ? jobStatus === "queued"
                ? "⏳ Ставимо задачу в чергу..."
                : "✨ Генеруємо..."
              : retryCountdown !== null
                ? `🔄 Автоповтор через ${retryCountdown}с (натисніть для повтору)`
                : buttonLabel}
          </Button>
          {retryCountdown !== null && (
            <Button size="lg" variant="outline" onClick={() => { stopRetryTimer(); pendingRetryRef.current = false; }}>
              Скасувати
            </Button>
          )}
          {results && retryCountdown === null && (
            <Button size="lg" variant="outline" onClick={handleClear}>
              🧹 Очистити
            </Button>
          )}
        </div>

        <ResultSection results={results} isGenerating={isGenerating} jobStatus={jobStatus} />
      </div>
    </main>
  );
}
