"use client";

import { useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ReferenceUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

export function ReferenceUpload({ files, onFilesChange }: ReferenceUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles) return;
      const accepted = Array.from(newFiles).filter((f) =>
        /\.(jpe?g|png|bmp|gif)$/i.test(f.name)
      );
      onFilesChange([...files, ...accepted]);
    },
    [files, onFilesChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">📤 Крок 1: Референсні зображення</CardTitle>
      </CardHeader>
      <CardContent>
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors hover:border-primary hover:bg-accent/50"
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.bmp,.gif"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <p className="text-muted-foreground">
            Перетягніть зображення сюди або натисніть для вибору
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            JPG, PNG, BMP, GIF
          </p>
        </div>

        {files.length > 0 && (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3 mt-4">
            {files.map((file, idx) => (
              <div key={idx} className="relative group">
                <img
                  src={URL.createObjectURL(file)}
                  alt={`Реф. ${idx + 1}`}
                  className="w-full aspect-square object-cover rounded-md border"
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full w-5 h-5 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  ×
                </button>
                <p className="text-[10px] text-muted-foreground text-center mt-1 truncate">
                  Реф. {idx + 1}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
