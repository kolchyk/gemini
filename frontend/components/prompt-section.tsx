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
      if (promptType === "darnytsia" || promptType === "custom") {
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
            >
              {label}
            </Button>
          ))}
        </div>

        {promptType === "darnytsia" && (
          <Collapsible>
            <CollapsibleTrigger className="text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
              📋 Системна конфігурація (Darnytsia Corporate Identity)
            </CollapsibleTrigger>
            <CollapsibleContent>
              <Alert className="mt-2">
                <AlertDescription className="text-xs">
                  Ця інструкція зашита в систему і застосовується до ваших даних
                  автоматично.
                </AlertDescription>
              </Alert>
              {defaultPrompts?.darnytsia && (
                <pre className="mt-2 p-3 bg-muted rounded-md text-xs overflow-auto max-h-60">
                  {defaultPrompts.darnytsia}
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
              ? "Введіть ваші дані для слайду..."
              : "Опишіть що згенерувати..."
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
