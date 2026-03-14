"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { PromptType } from "@/lib/types";

interface PromptSectionProps {
  promptType: PromptType;
  prompt: string;
  defaultPrompts: Record<PromptType, string> | null;
  onPromptTypeChange: (type: PromptType) => void;
  onPromptChange: (prompt: string) => void;
}

const PROMPT_TYPES: { value: PromptType; label: string }[] = [
  { value: "custom", label: "З нуля" },
  { value: "women", label: "Жінки" },
  { value: "men", label: "Чоловіки" },
  { value: "darnytsia", label: "Darnytsia" },
];

export function PromptSection({
  promptType,
  prompt,
  defaultPrompts,
  onPromptTypeChange,
  onPromptChange,
}: PromptSectionProps) {
  const handleReset = () => {
    if (defaultPrompts) {
      if (promptType === "custom") {
        onPromptChange("");
      } else {
        onPromptChange(defaultPrompts[promptType]);
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">✍️ Крок 2: Промпт</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {PROMPT_TYPES.map(({ value, label }) => (
            <Button
              key={value}
              variant={promptType === value ? "default" : "outline"}
              size="sm"
              onClick={() => onPromptTypeChange(value)}
              disabled={!defaultPrompts && value !== "custom"}
            >
              {label}
            </Button>
          ))}
          {!defaultPrompts && <span className="text-xs text-muted-foreground animate-pulse ml-2">Завантаження шаблонів...</span>}
        </div>

        {promptType !== "custom" && (
          <Collapsible>
            <CollapsibleTrigger className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
              📋 Системна конфігурація {promptType === "darnytsia" ? "(Darnytsia Corporate Identity)" : `(${PROMPT_TYPES.find(p => p.value === promptType)?.label})`}
            </CollapsibleTrigger>
            <CollapsibleContent>
              <Alert className="mt-2">
                <AlertDescription className="text-xs">
                  {promptType === "darnytsia" 
                    ? "Ця інструкція зашита в систему і застосовується до ваших даних автоматично."
                    : "Цей шаблон використовується як основа для генерації."}
                </AlertDescription>
              </Alert>
              {defaultPrompts?.[promptType] && (
                <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-auto max-h-60 whitespace-pre-wrap">
                  {defaultPrompts[promptType]}
                </pre>
              )}
            </CollapsibleContent>
          </Collapsible>
        )}

        <Textarea
          value={prompt}
          onChange={(e) => onPromptChange(e.target.value)}
          placeholder={
            promptType === "darnytsia"
              ? "Введіть ваші дані замість {{user_input}}..."
              : defaultPrompts?.custom || "Опишіть що згенерувати..."
          }
          rows={6}
        />

        <Button variant="outline" size="sm" onClick={handleReset}>
          ↩️ {promptType === "darnytsia" ? "Очистити дані" : "Скинути промпт"}
        </Button>
      </CardContent>
    </Card>
  );
}
