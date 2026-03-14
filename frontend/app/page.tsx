"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";
import { Header } from "@/components/header";
import { ControlsRow } from "@/components/controls-row";
import { ReferenceUpload } from "@/components/reference-upload";
import { PromptSection } from "@/components/prompt-section";
import { ResultSection } from "@/components/result-section";
import { Button } from "@/components/ui/button";
import { generateImage, getPrompts } from "@/lib/api";
import type {
  ModelMode,
  AspectRatio,
  PromptType,
  GenerationResult,
  PromptsResponse,
} from "@/lib/types";

export default function Home() {
  const [modelMode, setModelMode] = useState<ModelMode>("Flash");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("16:9");
  const [temperature, setTemperature] = useState(1.0);
  const [promptType, setPromptType] = useState<PromptType>("custom");
  const [prompt, setPrompt] = useState("");
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const [results, setResults] = useState<Record<string, GenerationResult> | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [defaultPrompts, setDefaultPrompts] = useState<PromptsResponse | null>(null);
  const [retryCountdown, setRetryCountdown] = useState<number | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getPrompts()
      .then((prompts) => {
        setDefaultPrompts(prompts);
      })
      .catch((err) => {
        console.error("Failed to load prompts:", err);
        toast.error("Не вдалося завантажити шаблони промптів");
      });
  }, []);

  // Sync prompt when defaultPrompts arrive if currently empty
  useEffect(() => {
    if (defaultPrompts && prompt === "") {
      if (promptType !== "custom") {
        setPrompt(defaultPrompts[promptType]);
      }
    }
  }, [defaultPrompts, promptType, prompt]);

  const handlePromptTypeChange = useCallback(
    (type: PromptType) => {
      setPromptType(type);
      if (defaultPrompts) {
        if (type === "custom") {
          setPrompt("");
        } else {
          setPrompt(defaultPrompts[type]);
        }
      }
    },
    [defaultPrompts]
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

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error("Будь ласка, введіть промпт!");
      return;
    }

    stopRetryTimer();
    setIsGenerating(true);
    setResults(null);

    try {
      const response = await generateImage({
        prompt,
        modelMode,
        aspectRatio,
        temperature,
        promptType,
        referenceImages: referenceFiles,
      });

      // Check if all results are errors (no images)
      const hasAnyImage = Object.values(response.results).some(
        (r) => r.image_base64 !== null
      );

      if (!hasAnyImage) {
        // All models failed — start retry countdown
        setResults(response.results);
        toast.error("Всі моделі повернули помилку. Автоповтор через 30 сек...");
        pendingRetryRef.current = true;
        startRetryTimer();
      } else {
        setResults(response.results);
        if (response.fallback_used) {
          toast.success("Основна модель недоступна — використано резервну.");
        } else {
          toast.success("Зображення згенеровано!");
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      toast.error(message);
      pendingRetryRef.current = true;
      startRetryTimer();
    } finally {
      setIsGenerating(false);
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
          temperature={temperature}
          onModelModeChange={setModelMode}
          onAspectRatioChange={setAspectRatio}
          onTemperatureChange={setTemperature}
        />

        <ReferenceUpload files={referenceFiles} onFilesChange={setReferenceFiles} />

        <PromptSection
          promptType={promptType}
          prompt={prompt}
          defaultPrompts={defaultPrompts}
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
              ? "✨ Генеруємо..."
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

        <ResultSection results={results} isGenerating={isGenerating} />
      </div>
    </main>
  );
}
