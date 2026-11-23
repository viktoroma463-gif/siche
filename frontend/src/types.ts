export type ModuleKey = "general" | "question" | "literature" | "claim" | "evidence" | "logic";

export type ContentType = "guide" | "scaffold" | "generated_draft" | "user";

export type ModuleMeta = {
  key: Exclude<ModuleKey, "general">;
  label: string;
  hint: string;
};

export type Message = {
  id: string;
  role: "system" | "assistant" | "user";
  kind: string;
  content: string;
  content_type: ContentType;
  copyable: boolean;
  copy_unlocked: boolean;
  substantive: boolean;
  module: ModuleKey;
  stage: number;
  ts: string;
  options?: string[];
};

export type Plan = {
  question: string;
  evidence: string;
  doubts: string;
  next_step: string;
};

export type Session = {
  id: string;
  created_at: string;
  task_type: string;
  topic: string;
  current_module: ModuleKey;
  messages: Message[];
  plan: Plan;
  delegation_stage: number;
  modules: ModuleMeta[];
  runtime: {
    llm: string;
    model: string;
    configured: boolean;
  };
  ui: {
    copy_test_message_id: string;
    copy_test_followup: boolean;
    copy_lock_disclaimer: string;
  };
};

export type SessionResp = { session: Session };

export type CopyRequest = {
  requires_test: boolean;
  event_id: string;
  content_type: ContentType;
  forced?: boolean;
  disclaimer?: string;
  content?: string;
};

export type MicroTestResult = {
  status: "unlock" | "followup" | "locked";
  reason: string;
  followup_question: string;
  unlocked: boolean;
  content?: string;
  event_id: string;
};

export type MicroTestResp = { session: Session; result: MicroTestResult };

export type PrefillResult = {
  fields: Plan;
  has_existing: boolean;
};

export type PrefillResp = { session: Session; prefill: PrefillResult };

export type ExportResp = {
  html: string;
  json: Record<string, unknown>;
};
