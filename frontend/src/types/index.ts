// ─── API Response Types ───────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  status_code?: number;
}

// ─── Upload / LogFile ─────────────────────────────────────────────────────────

export interface PresignedUploadResponse {
  upload_url: string;
  s3_key: string;
  log_file_id: number;
  expires_in_seconds: number;
}

export interface LogFile {
  id: number;
  filename: string;
  s3_key: string;
  size_bytes: number;
  source_type: string;
  uploaded_at: string;
}

// ─── Analysis ─────────────────────────────────────────────────────────────────

export type AnalysisStatus = "pending" | "processing" | "completed" | "failed";

export interface AnalysisRead {
  id: number;
  log_file_id: number;
  status: AnalysisStatus;
  progress_step: number;
  started_at: string | null;
  completed_at: string | null;
  heuristic_report: HeuristicReport | null;
  threat_report: ThreatReport | null;
  error_message: string | null;
}

export interface AnalysisListResponse {
  items: AnalysisRead[];
  total: number;
  page: number;
  page_size: number;
}

// ─── Heuristic Report ─────────────────────────────────────────────────────────

export interface TopIpItem {
  ip: string;
  count: number;
  percentage: number;
}

export interface TopItem {
  value: string;
  count: number;
}

export interface TopRuleItem {
  rule_id: string;
  rule_message: string | null;
  count: number;
}

export interface TimePoint {
  minute: string;
  count: number;
}

export interface Anomaly {
  type: string;
  severity: number;
  description: string;
  affected_entity: string;
  supporting_data: Record<string, unknown>;
}

export interface HeuristicReport {
  total_events: number;
  time_range: [string, string];
  top_source_ips: TopIpItem[];
  top_uris: TopItem[];
  top_countries: TopItem[];
  top_user_agents: TopItem[];
  top_rules_triggered: TopRuleItem[];
  action_distribution: Record<string, number>;
  requests_per_minute: TimePoint[];
  anomalies: Anomaly[];
}

// ─── Threat Report ────────────────────────────────────────────────────────────

export type ThreatLevel = "low" | "medium" | "high" | "critical";

export interface IdentifiedThreat {
  threat_type: string;
  description: string;
  affected_assets: string[];
  evidence: string;
  recommended_action: string;
}

export interface InvestigationItem {
  entity: string;
  reason: string;
}

export interface ThreatReport {
  executive_summary: string;
  threat_level: ThreatLevel;
  confidence_score: number;
  identified_threats: IdentifiedThreat[];
  false_positive_warnings: string[];
  suggested_waf_rules: string[];
  investigation_priority: InvestigationItem[];
}
