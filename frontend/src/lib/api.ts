import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Clerk session token — Clerk kurulu değilse sessizce atla
apiClient.interceptors.request.use(async (config) => {
  if (typeof window !== "undefined") {
    try {
      const clerk = (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string | null> } } }).Clerk;
      const token = await clerk?.session?.getToken();
      if (token) config.headers.Authorization = `Bearer ${token}`;
    } catch {
      // Oturum yok — kimliksiz istek
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  (err: unknown) => {
    if (axios.isAxiosError(err)) {
      console.error("[API]", err.response?.status, err.response?.data ?? err.message);
    }
    return Promise.reject(err);
  }
);

// ─── Tip tanımları ────────────────────────────────────────────────────────────

import type {
  AnalysisListResponse,
  AnalysisRead,
  LogFile,
  PresignedUploadResponse,
} from "@/types";

export interface DirectUploadResponse {
  log_file_id: number;
  filename: string;
  size_bytes: number;
  s3_key: string;
  storage: "s3" | "local";
}

export const api = {
  // Sağlık
  health: () => apiClient.get<{ status: string }>("/health"),

  // ── Yükleme ─────────────────────────────────────────────────────────────────
  // Presigned S3 URL (AWS credentials gerektirir)
  createUpload: (filename: string, sizeBytes: number) =>
    apiClient.post<PresignedUploadResponse>(
      `/uploads?filename=${encodeURIComponent(filename)}&size_bytes=${sizeBytes}`
    ),

  listUploads: (page = 1) =>
    apiClient.get<LogFile[]>(`/uploads?page=${page}`),

  // S3'e doğrudan PUT (createUpload'dan dönen presigned URL ile)
  uploadToS3: (url: string, file: File, onProgress?: (pct: number) => void) =>
    axios.put(url, file, {
      headers: { "Content-Type": file.type || "application/octet-stream" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      },
    }),

  // Backend'e doğrudan multipart upload — AWS credentials olmadan da çalışır
  uploadDirect: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return apiClient.post<DirectUploadResponse>("/uploads/direct", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
      },
    });
  },

  // ── Analizler ────────────────────────────────────────────────────────────────
  createAnalysis: (logFileId: number) =>
    apiClient.post<AnalysisRead>("/analyses", { log_file_id: logFileId }),
  listAnalyses: (page = 1, pageSize = 20) =>
    apiClient.get<AnalysisListResponse>(`/analyses?page=${page}&page_size=${pageSize}`),
  getAnalysis: (id: number) =>
    apiClient.get<AnalysisRead>(`/analyses/${id}`),
  getPdfUrl: (id: number) => `${API_URL}/api/v1/analyses/${id}/report.pdf`,
};