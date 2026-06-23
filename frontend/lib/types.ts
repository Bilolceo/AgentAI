export interface MessageResponse {
  reply: string;
  action: "allow" | "transfer" | "emergency";
  category: string;
  transferred: boolean;
  language: string;
}

export interface StartCallResponse {
  call_id: number;
  greeting?: string;
  language?: string;
}

export interface ChatTurn {
  role: "user" | "assistant";
  text: string;
  action?: MessageResponse["action"];
  transferred?: boolean;
}

export interface AdminCall {
  id: number;
  twilio_call_sid: string;
  from_number: string;
  to_number: string;
  language: string | null;
  status: string;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
}

export interface AdminStats {
  total_calls: number;
  ai_resolved: number;
  operator_transfers: number;
  callbacks_required: number;
  kb_items: number;
  recent_calls: AdminCall[];
}

export interface TranscriptItem {
  id: number;
  role: string;
  text: string;
  created_at: string | null;
}

export interface TransferInfo {
  reason: string | null;
  priority: string | null;
  status: string | null;
}

export interface CallbackTask {
  id: number;
  call_session_id: number;
  patient_phone: string | null;
  reason: string;
  priority: string;
  status: string;
  due_at: string | null;
  notes: string | null;
  assigned_to_user_id: number | null;
  resolution_notes: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  rescheduled_at: string | null;
  last_status_changed_at: string | null;
  created_at: string | null;
}

export interface KbSource {
  id: number;
  title: string;
}

export interface AdminCallDetail extends AdminCall {
  transcripts: TranscriptItem[];
  transfer: TransferInfo | null;
  callback: CallbackTask | null;
  sources: KbSource[];
  reason_codes: string[];
  audit_events: { event: string; data: Record<string, unknown> | null; created_at: string | null }[];
}

export interface AuditLogEntry {
  id: number;
  event_type: string;
  actor_user_id: number | null;
  target_type: string | null;
  target_id: number | null;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string | null;
}

export interface KnowledgeItem {
  id: number;
  category: string;
  title: string;
  content_uz: string;
  content_ru: string;
  tags: string[] | null;
  is_active: boolean;
}

export interface KnowledgeItemInput {
  category: string;
  title: string;
  content_uz: string;
  content_ru: string;
  tags: string[];
  is_active: boolean;
}

export interface AudioRecording {
  id: number;
  call_session_id: number;
  call_message_id: number | null;
  direction: string;
  kind: string;
  storage_provider: string;
  storage_key: string;
  content_type: string;
  size_bytes: number;
  duration_ms: number | null;
  checksum_sha256: string;
  transcript_text: string | null;
  transcript_language: string | null;
  transcript_confidence: number | null;
  tts_voice: string | null;
  tts_text: string | null;
  is_deleted: boolean;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AudioRecordingDetail extends AudioRecording {
  // Placeholder signed URL from mock storage; null when not resolvable.
  signed_url: string | null;
}

export interface AudioRecordingFilters {
  call_id?: number;
  direction?: string;
  kind?: string;
  include_deleted?: boolean;
  limit?: number;
  offset?: number;
}

export interface TelephonyCall {
  id: number;
  provider: string;
  provider_call_id: string | null;
  call_session_id: number | null;
  from_number: string | null;
  to_number: string | null;
  status: string;
  direction: string;
  raw_metadata: Record<string, unknown> | null;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TelephonyCallFilters {
  provider?: string;
  status?: string;
  direction?: string;
  call_session_id?: number;
  limit?: number;
  offset?: number;
}

export type Role = "super_admin" | "admin" | "operator";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  two_factor_enabled: boolean;
  force_password_change: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface ManagedUser {
  id: number;
  email: string;
  full_name: string | null;
  role: Role;
  is_active: boolean;
  two_factor_enabled: boolean;
  last_login_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}
