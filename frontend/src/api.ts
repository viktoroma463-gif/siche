import type {
  CopyRequest,
  ExportResp,
  MicroTestResp,
  ModuleKey,
  Plan,
  PrefillResp,
  Session,
  SessionResp,
} from "./types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

const unwrap = (r: SessionResp) => r.session;

export const api = {
  health: () =>
    req<{ product: string; ok: boolean; configured: boolean; llm: string; model: string }>("/api/health"),
  create: () =>
    req<SessionResp>("/api/sessions", { method: "POST", body: JSON.stringify({}) }).then(unwrap),
  get: (id: string) => req<SessionResp>(`/api/sessions/${id}`).then(unwrap),
  setModule: (id: string, module: ModuleKey) =>
    req<SessionResp>(`/api/sessions/${id}/module`, {
      method: "POST",
      body: JSON.stringify({ module }),
    }).then(unwrap),
  assist: (id: string, message: string, module: ModuleKey) =>
    req<SessionResp>(`/api/sessions/${id}/assist`, {
      method: "POST",
      body: JSON.stringify({ message, module }),
    }).then(unwrap),
  copyRequest: (id: string, messageId: string) =>
    req<CopyRequest>(`/api/sessions/${id}/messages/${messageId}/copy-request`, { method: "POST" }),
  microTest: (
    id: string,
    messageId: string,
    option: "tweak" | "contrary" | "bounds",
    text: string,
    eventId: string,
  ) =>
    req<MicroTestResp>(`/api/sessions/${id}/messages/${messageId}/micro-test`, {
      method: "POST",
      body: JSON.stringify({ option, text, event_id: eventId }),
    }),
  refuseMicroTest: (id: string, messageId: string, eventId: string) =>
    req<MicroTestResp>(
      `/api/sessions/${id}/messages/${messageId}/micro-test/refuse?event_id=${encodeURIComponent(eventId)}`,
      { method: "POST" },
    ),
  savePlan: (id: string, plan: Plan) =>
    req<SessionResp>(`/api/sessions/${id}/plan`, {
      method: "POST",
      body: JSON.stringify(plan),
    }).then(unwrap),
  prefillPlan: (id: string) =>
    req<PrefillResp>(`/api/sessions/${id}/plan/prefill`, { method: "POST" }),
  exportSession: (id: string) => req<ExportResp>(`/api/sessions/${id}/export`),
};

const LS_KEY = "siche.lastSession";

export function cacheSession(session: Session) {
  localStorage.setItem(LS_KEY, JSON.stringify({ id: session.id, draft: session }));
}

export function readCachedSession(): { id: string; draft: Session } | null {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearCachedSession() {
  localStorage.removeItem(LS_KEY);
}

export async function writeClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      return ok;
    } catch {
      return false;
    }
  }
}
