import { useEffect, useRef, useState } from "react";
import { gsap, useGSAP } from "../gsap";
import { api, cacheSession, writeClipboard } from "../api";
import AssistThread from "../components/AssistThread";
import { CopyTestModal } from "../components/Modals";
import PlanDrawer from "../components/PlanDrawer";
import RiskChecklist from "../components/RiskChecklist";
import ThoughtLog from "../components/ThoughtLog";
import TopBar from "../components/TopBar";
import type { Message, ModuleKey, Plan, Session } from "../types";

function download(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function joinPlan(existing: string, incoming: string) {
  return [existing.trim(), incoming.trim()].filter(Boolean).join("\n\n");
}

export default function Workspace({
  session,
  setSession,
  onNew,
  error,
  setError,
}: {
  session: Session;
  setSession: (s: Session) => void;
  onNew: () => void;
  error: string;
  setError: (s: string) => void;
}) {
  const [pending, setPending] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [planOpen, setPlanOpen] = useState(false);
  const [copyTarget, setCopyTarget] = useState<Message | null>(null);
  const [copyEventId, setCopyEventId] = useState("");
  const [copyDisclaimer, setCopyDisclaimer] = useState("");
  const [copyReason, setCopyReason] = useState("");
  const [copyFollowup, setCopyFollowup] = useState("");
  const [toast, setToast] = useState("");
  const [seed, setSeed] = useState<{ text: string; id: number }>({ text: "", id: 0 });
  const [riskFlash, setRiskFlash] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const lastDraftId = useRef("");
  const riskInit = useRef(true);

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
      tl.from(".topbar-shell", { y: -18, opacity: 0, duration: 0.38 })
        .from(".sidebar-panel", { x: -26, opacity: 0, duration: 0.48 }, "-=0.16")
        .from(".assist-panel", { y: 26, opacity: 0, duration: 0.52 }, "-=0.34")
        .from(".module-chip", { y: 9, opacity: 0, duration: 0.3, stagger: 0.035 }, "-=0.24")
        .from(".message-bubble", { y: 10, opacity: 0, duration: 0.3, stagger: 0.04 }, "-=0.28");
    },
    { scope: root },
  );

  // 兜底：rAF 被节流时清除入场动画内联样式
  useEffect(() => {
    const timer = window.setTimeout(() => {
      const el = root.current;
      if (!el) return;
      gsap.set(
        el.querySelectorAll(
          ".topbar-shell, .sidebar-panel, .assist-panel, .module-chip, .message-bubble",
        ),
        { clearProps: "opacity,transform" },
      );
    }, 1600);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 2400);
    return () => clearTimeout(timer);
  }, [toast]);

  const drafts = session.messages.filter((m) => m.content_type === "generated_draft");
  const latestDraftId = drafts.length ? drafts[drafts.length - 1].id : "";

  useEffect(() => {
    if (!latestDraftId) return;
    if (riskInit.current) {
      riskInit.current = false;
      lastDraftId.current = latestDraftId;
      return;
    }
    if (lastDraftId.current === latestDraftId) return;
    lastDraftId.current = latestDraftId;
    setRiskFlash(true);
    const timer = setTimeout(() => setRiskFlash(false), 2000);
    return () => clearTimeout(timer);
  }, [latestDraftId]);

  const adopt = (next: Session) => {
    setSession(next);
    cacheSession(next);
  };

  const run = async (fn: () => Promise<Session>) => {
    setPending(true);
    setError("");
    try {
      adopt(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败");
    } finally {
      setPending(false);
    }
  };

  const send = async (message: string, module: ModuleKey) => {
    setPending(true);
    setError("");
    try {
      adopt(await api.assist(session.id, message, module));
    } catch (e) {
      setError(e instanceof Error ? e.message : "请求失败，请重试");
      try {
        adopt(await api.get(session.id));
      } catch {
        /* 保持当前界面 */
      }
    } finally {
      setPending(false);
    }
  };

  const copy = async (message: Message) => {
    setError("");
    try {
      const request = await api.copyRequest(session.id, message.id);
      if (!request.requires_test) {
        const ok = await writeClipboard(request.content || message.content);
        setToast(ok ? "已复制" : "复制失败，请手动选择文本");
        return;
      }
      setCopyTarget(message);
      setCopyEventId(request.event_id);
      setCopyDisclaimer(request.disclaimer || session.ui.copy_lock_disclaimer);
      setCopyReason("");
      setCopyFollowup("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "复制请求失败");
    }
  };

  const submitMicroTest = async (option: "tweak" | "contrary" | "bounds", text: string) => {
    if (!copyTarget) return;
    setPending(true);
    setError("");
    try {
      const response = await api.microTest(session.id, copyTarget.id, option, text, copyEventId);
      adopt(response.session);
      if (response.result.status === "unlock") {
        const ok = await writeClipboard(response.result.content || copyTarget.content);
        setToast(ok ? "审查完成，已复制" : "审查完成，请手动选择文本复制");
        setCopyTarget(null);
      } else {
        setCopyReason(response.result.reason);
        setCopyFollowup(response.result.followup_question);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "微测试提交失败");
    } finally {
      setPending(false);
    }
  };

  const refuseMicroTest = async () => {
    if (!copyTarget) return;
    try {
      const response = await api.refuseMicroTest(session.id, copyTarget.id, copyEventId);
      adopt(response.session);
    } catch {
      /* 拒绝失败也保持本地锁定 */
    }
    setCopyTarget(null);
    setToast("已保持锁定，可以继续对话");
  };

  const savePlan = async (plan: Plan) => {
    setPending(true);
    setError("");
    try {
      adopt(await api.savePlan(session.id, plan));
      setToast("规划单已保存");
    } catch (e) {
      setError(e instanceof Error ? e.message : "规划单保存失败");
    } finally {
      setPending(false);
    }
  };

  const prefillPlan = async () => {
    setPending(true);
    setError("");
    try {
      const response = await api.prefillPlan(session.id);
      adopt(response.session);
      const fields = response.prefill.fields;
      if (!Object.values(fields).some((value) => value.trim())) {
        setToast("没有从你的发言中提取到可预填充内容");
        return;
      }
      const current = response.session.plan;
      const hasContent = (Object.keys(current) as Array<keyof Plan>).some((key) =>
        current[key].trim(),
      );
      if (
        hasContent &&
        !window.confirm("规划单已有内容，预填充将会追加到现有内容末尾，是否继续？")
      ) {
        return;
      }
      const merged: Plan = {
        question: joinPlan(current.question, fields.question),
        evidence: joinPlan(current.evidence, fields.evidence),
        doubts: joinPlan(current.doubts, fields.doubts),
        next_step: joinPlan(current.next_step, fields.next_step),
      };
      adopt(await api.savePlan(session.id, merged));
      setToast("已根据你的发言预填充，可继续修改");
    } catch (e) {
      setError(e instanceof Error ? e.message : "预填充失败");
    } finally {
      setPending(false);
    }
  };

  const exportArchive = async () => {
    setExporting(true);
    setError("");
    try {
      const data = await api.exportSession(session.id);
      download(`siche-${session.id}.html`, data.html, "text/html;charset=utf-8");
      download(
        `siche-${session.id}.json`,
        JSON.stringify(data.json, null, 2),
        "application/json;charset=utf-8",
      );
      setToast("已导出 HTML 与 JSON 两份文件");
    } catch (e) {
      setError(e instanceof Error ? e.message : "导出失败");
    } finally {
      setExporting(false);
    }
  };

  const stage4Choice = (option: string) => {
    if (option.startsWith("缩小")) {
      setSeed({ text: "我想把问题缩小到：", id: Date.now() });
      setToast("已把起点填入输入框，接着写下去即可");
    } else {
      setToast("进度已保存，稍后可以带着自己的想法再来");
    }
  };

  return (
    <div ref={root} className="min-h-screen">
      <TopBar
        session={session}
        onExport={exportArchive}
        exporting={exporting}
        onNew={onNew}
      />

      {!session.runtime.configured ? (
        <div className="border-b border-cinnabar/30 bg-cinnabar/10 px-5 py-2 text-center text-sm text-cinnabar">
          未配置 DeepSeek 密钥：请在项目根目录的 .env 中填写 SICHE_DEEPSEEK_API_KEY，然后重启服务。
        </div>
      ) : null}

      {error ? (
        <div className="mx-auto mt-3 max-w-6xl px-4">
          <p className="border border-cinnabar/30 bg-white px-4 py-2 text-sm text-cinnabar">{error}</p>
        </div>
      ) : null}

      <div className="mx-auto grid max-w-[1520px] gap-5 p-4 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="h-fit">
          <div className="sidebar-panel paper-card space-y-6 p-5 lg:sticky lg:top-20">
            <ThoughtLog messages={session.messages} />

            <section>
              <button
                data-testid="open-plan"
                className="flex w-full items-center justify-between gap-2 border border-black/10 bg-white px-3 py-3 text-left hover:border-cinnabar"
                onClick={() => setPlanOpen(true)}
              >
                <span>
                  <span className="font-serif text-lg">研究规划单</span>
                  <span className="ml-2 text-xs text-ink-soft">点击打开抽屉</span>
                </span>
                <span className="text-sm text-cinnabar">打开 ›</span>
              </button>
              <p className="mt-1 text-xs leading-5 text-ink-soft">
                我的问题、已有证据、尚存疑点、下一步计划。
              </p>
            </section>

            <RiskChecklist flash={riskFlash} />
          </div>
        </aside>

        <main className="assist-panel min-w-0">
          <AssistThread
            session={session}
            pending={pending}
            seed={seed}
            onSend={send}
            onModule={(module) => run(() => api.setModule(session.id, module))}
            onCopy={copy}
            onStage4={stage4Choice}
          />
        </main>
      </div>

      <PlanDrawer
        open={planOpen}
        plan={session.plan}
        pending={pending}
        onClose={() => setPlanOpen(false)}
        onSave={savePlan}
        onPrefill={prefillPlan}
      />

      <CopyTestModal
        message={copyTarget}
        disclaimer={copyDisclaimer}
        reason={copyReason}
        followup={copyFollowup}
        pending={pending}
        onSubmit={submitMicroTest}
        onRefuse={refuseMicroTest}
      />

      {toast ? (
        <div className="toast fixed bottom-6 left-1/2 z-50 -translate-x-1/2 bg-ink px-5 py-2 text-sm text-paper shadow-lg">
          {toast}
        </div>
      ) : null}
    </div>
  );
}
