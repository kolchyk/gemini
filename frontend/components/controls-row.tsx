import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import type { ModelMode, AspectRatio } from "@/lib/types";

const MODE_HINTS: Record<ModelMode, string> = {
  Flash: "⚡ Швидко (~10с). Підходить для ескізів та ітерацій.",
  Pro: "✨ Вища якість (~30с). Підходить для фінальних зображень.",
  Both: "",
};

interface ControlsRowProps {
  modelMode: ModelMode;
  aspectRatio: AspectRatio;
  temperature: number;
  onModelModeChange: (mode: ModelMode) => void;
  onAspectRatioChange: (ratio: AspectRatio) => void;
  onTemperatureChange: (temp: number) => void;
}

export function ControlsRow({
  modelMode,
  aspectRatio,
  temperature,
  onModelModeChange,
  onAspectRatioChange,
  onTemperatureChange,
}: ControlsRowProps) {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_2fr] gap-6">
        <div className="space-y-2">
          <Label>Модель</Label>
          <Select value={modelMode} onValueChange={(v) => onModelModeChange(v as ModelMode)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Flash">⚡ Flash</SelectItem>
              <SelectItem value="Pro">✨ Pro</SelectItem>
              <SelectItem value="Both">🔀 Обидві</SelectItem>
            </SelectContent>
          </Select>
          {MODE_HINTS[modelMode] && (
            <p className="text-xs text-muted-foreground">{MODE_HINTS[modelMode]}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label>Співвідношення</Label>
          <Select value={aspectRatio} onValueChange={(v) => onAspectRatioChange(v as AspectRatio)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2", "4:5", "5:4", "21:9", "1:4", "4:1", "1:8", "8:1"] as AspectRatio[]).map((r) => (
                <SelectItem key={r} value={r}>{r}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <Label>Творчість: {temperature.toFixed(2)}</Label>
          <Slider
            value={[temperature]}
            onValueChange={(value) => onTemperatureChange(Array.isArray(value) ? value[0] : value)}
            min={0}
            max={1}
            step={0.05}
            className="mt-2"
          />
          <p className="text-xs text-muted-foreground flex justify-between">
            <span>Стабільно</span>
            <span>Творчо</span>
          </p>
        </div>
      </div>
      <Separator className="my-6" />
    </>
  );
}
