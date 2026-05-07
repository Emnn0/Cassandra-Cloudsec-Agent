"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, File, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

type Stage = "idle" | "requesting" | "uploading" | "starting" | "done" | "error";

interface Props {
  onComplete: (analysisId: number) => void;
}

export function FileUploader({ onComplete }: Props) {
  const [stage, setStage] = useState<Stage>("idle");
  const [progress, setProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [filename, setFilename] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setFilename(file.name);
    setErrorMsg("");
    setProgress(0);

    try {
      // Backend'e doğrudan multipart upload — CORS ve AWS credentials gerektirmez
      setStage("uploading");
      const { data: upload } = await api.uploadDirect(file, setProgress);

      setStage("starting");
      const { data: analysis } = await api.createAnalysis(upload.log_file_id);

      setStage("done");
      setTimeout(() => onComplete(analysis.id), 600);
    } catch (err: unknown) {
      setStage("error");
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            "Yükleme başarısız"
          : "Yükleme başarısız";
      setErrorMsg(msg);
    }
  }, [onComplete]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  if (stage === "done") {
    return (
      <div className="flex flex-col items-center gap-3 py-16">
        <CheckCircle2 size={48} className="text-emerald-400" />
        <p className="text-lg font-semibold text-[#E2E8F0]">Analiz başlatıldı!</p>
        <p className="text-sm text-[#64748B] font-mono">Sonuçlara yönlendiriliyorsunuz…</p>
      </div>
    );
  }

  const isLoading = stage === "requesting" || stage === "uploading" || stage === "starting";

  const STAGE_LABEL: Record<Stage, string> = {
    idle:       "",
    requesting: "Hazırlanıyor…",
    uploading:  `${filename} yükleniyor… ${progress}%`,
    starting:   "Analiz başlatılıyor…",
    done:       "Tamamlandı!",
    error:      errorMsg,
  };

  return (
    <div className="space-y-4">
      <div
        onClick={() => !isLoading && inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer
          ${dragOver
            ? "border-[#00D4FF] bg-[#00D4FF]/5 shadow-glow"
            : "border-[#1E3A5F] hover:border-[#00D4FF]/40 bg-[#0D1B2E] hover:bg-[#132238]"}
          ${isLoading ? "pointer-events-none opacity-70" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".ndjson,.json,.log,.txt,.csv"
          className="hidden"
          onChange={onInputChange}
          disabled={isLoading}
        />

        <div className="flex flex-col items-center gap-4">
          {isLoading ? (
            <Loader2 size={48} className="text-[#00D4FF] animate-spin" />
          ) : (
            <div className="w-16 h-16 bg-[#132238] rounded-2xl flex items-center justify-center border border-[#1E3A5F]">
              <Upload size={28} className="text-[#00D4FF]" />
            </div>
          )}

          {!isLoading ? (
            <>
              <div>
                <p className="text-base font-semibold text-[#E2E8F0]">Log dosyanızı buraya sürükleyin</p>
                <p className="text-sm text-[#64748B] mt-1 font-mono">
                  veya tıklayarak seçin · NDJSON, JSON, CSV, TXT · maks. 500MB
                </p>
              </div>
              <span className="btn-secondary text-sm">Dosya Seç</span>
            </>
          ) : (
            <div className="space-y-3 w-full max-w-xs">
              <p className="text-sm font-medium text-[#E2E8F0] font-mono">{STAGE_LABEL[stage]}</p>
              {stage === "uploading" && (
                <div className="w-full bg-[#132238] rounded-full h-2 border border-[#1E3A5F]">
                  <div
                    className="bg-[#00D4FF] h-2 rounded-full transition-all duration-300 shadow-glow"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {stage === "error" && (
        <div className="flex items-center gap-3 bg-[#EF2B2D]/10 border border-[#EF2B2D]/30 rounded-xl px-4 py-3">
          <XCircle size={18} className="text-[#EF2B2D] flex-shrink-0" />
          <p className="text-sm text-[#EF2B2D]">{errorMsg}</p>
          <button
            onClick={() => { setStage("idle"); setProgress(0); }}
            className="ml-auto text-xs text-[#EF2B2D] hover:text-red-300 font-semibold"
          >
            Tekrar Dene
          </button>
        </div>
      )}

      {filename && stage !== "idle" && stage !== "error" && (
        <div className="flex items-center gap-3 bg-[#0D1B2E] border border-[#1E3A5F] rounded-xl px-4 py-3">
          <File size={16} className="text-[#00D4FF] flex-shrink-0" />
          <p className="text-sm text-[#E2E8F0] truncate font-mono">{filename}</p>
        </div>
      )}
    </div>
  );
}