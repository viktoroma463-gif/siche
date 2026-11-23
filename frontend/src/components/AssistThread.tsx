import { useEffect, useRef, useState } from "react";
import type { Message, ModuleKey, Session } from "../types";

const KIND_LABELS: Record<string, string> = {
  welcome: "开场",
  user: "发言",
  system: "流程",
  analysis: "分析",
  draft: "参考草稿",
  stage4: "引导结束",
};

const TYPE_LABELS: Record<string, string> = {
  guide: "引导",
  scaffold: "支架",
  generated_draft: "AI参考草稿",
};

function copyLabel(message: Message) {
  if (message.content_type === "generated_draft") {
    return message.copy_unlocked ? "复制" : "复制 · 强制审查";
  }
  if (message.content_type === "scaffold") {
    return message.copy_unlocked ? "复制" : "复制 · 需审查";
  }
  return "复制";
}

function Bubble({
  message,
  modules,
  onCopy,
  onStage4,
}: {
  message: Message;
  modules: Session["modules"];
  onCopy: (m: Message) => void;
  onStage4: (option: string) => void;
}) {
  const isUser = message.role === "user";
  const moduleLabel = modules.find((m) => m.key === message.module)?.label || "";
  const isDraft = message.content_type === "generated_draft";

  return (
    <article
      className={`message-bubble border px-4 py-3 ${
        isUser
          ? "ml-8 border-inkblue/30 bg-white"
          : isDraft
            ? "mr-2 border-cinnabar/40 bg-[#fbeee9]"
            : "mr-2 border-black/10 bg-sheet"
      }`}
    >
      <div className="flex items-center gap-3 text-xs text-ink-soft">
        <span>
          {isUser ? "你" : message.role === "system" ? "流程" : "思拆"} ·{" "}
          {KIND_LABELS[message.kind] || message.kind}
          {!isUser && moduleLabel ? <span className="ml-2 text-inkblue">{moduleLabel}</span> : null}
          {!isUser && TYPE_LABELS[message.content_type] ? (
            <span className={`ml-2 ${isDraft ? "text-cinnabar" : ""}`}>
              {TYPE_LABELS[message.content_type]}
            </span>
          ) : null}
        </span>
      </div>

      <div className="mt-2 whitespace-pre-wrap text-[16px] leading-7">{message.content}</div>

      {message.kind === "stage4" && message.options?.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {message.options.map((option) => (
            <button
              key={option}
              className="border border-cinnabar px-4 py-2 text-sm text-cinnabar hover:bg-cinnabar hover:text-white"
              onClick={() => onStage4(option)}
            >
              {option}
            </button>
          ))}
        </div>
      ) : null}

      {!isUser && message.copyable ? (
        <div className="mt-2 flex justify-end">
          <button
            className={
              message.content_type !== "guide" && !message.copy_unlocked
                ? "text-xs text-cinnabar hover:underline"
                : "text-xs text-ink-soft hover:text-ink"
            }
            onClick={() => onCopy(message)}
          >
            {copyLabel(message)}
          </button>
        </div>
      ) : null}
    </article>
  );
}

export default function AssistThread({
  session,
  pending,
  seed,
  onSend,
  onModule,
  onCopy,
  onStage4,
}: {
  session: Session;
  pending: boolean;
  seed: { text: string; id: number };
  onSend: (message: string, module: ModuleKey) => void;
  onModule: (module: ModuleKey) => void;
  onCopy: (m: Message) => void;
  onStage4: (option: string) => void;
}) {
  const [text, setText] = useState("");
  const [lastSeedId, setLastSeedId] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const nearBottom = useRef(true);
  const current = session.modules.find((m) => m.key === session.current_module);

  if (seed.id && seed.id !== lastSeedId) {
    setLastSeedId(seed.id);
    setText(seed.text);
  }

  useEffect(() => {
    if (nearBottom.current) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session.messages.length, pending]);

  const submit = () => {
    if (!text.trim() || pending) return;
    onSend(text.trim(), session.current_module);
    setText("");
  };

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    nearBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  return (
    <section className="paper-card flex h-[calc(100vh-7.5rem)] min-h-[36rem] flex-col">
      <div className="border-b border-black/10 px-5 py-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-serif text-xl">协作区</h2>
          <span className="text-xs text-ink-soft">
            {current ? `当前视角：${current.label}` : "当前视角：通用学术思辨"}
          </span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {session.modules.map((module) => {
            const active = module.key === session.current_module;
            return (
              <button
                type="button"
                key={module.key}
                title={module.hint}
                onClick={() => onModule(active ? "general" : module.key)}
                disabled={pending}
                className={`module-chip border-b-2 px-1 py-1.5 text-xs transition ${
                  active
                    ? "border-cinnabar font-medium text-cinnabar"
                    : "border-transparent text-ink-soft hover:text-cinnabar"
                }`}
              >
                {module.label}
              </button>
            );
          })}
        </div>
        <p className="mt-2 text-xs text-ink-soft">不选模块默认通用学术思辨；再次点击已选模块可取消。</p>
      </div>

      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-4"
        data-testid="message-list"
      >
        {session.messages.map((message) => (
          <Bubble
            key={message.id}
            message={message}
            modules={session.modules}
            onCopy={onCopy}
            onStage4={onStage4}
          />
        ))}
        {pending ? (
          <p className="mr-2 border border-dashed border-black/15 px-4 py-3 text-sm text-ink-soft">
            思拆正在阅读并分析…
          </p>
        ) : null}
        <div ref={endRef} />
      </div>

      <form
        className="border-t border-black/10 p-4"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <textarea
          className="min-h-[96px] w-full resize-y border border-black/15 bg-white px-3 py-2 outline-none focus:border-cinnabar"
          data-testid="assist-input"
          placeholder={
            current
              ? `在「${current.label}」视角下，写下你的草稿、判断或真实困惑…`
              : "写下你的草稿、判断或真实困惑…"
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={!session.runtime.configured || pending}
        />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-ink-soft">
            不选模块也可以，默认通用思辨。AI 只做认知支架，不直接代写完整论文。
          </p>
          <button
            type="submit"
            data-testid="assist-send"
            disabled={pending || !text.trim() || !session.runtime.configured}
            className="bg-cinnabar px-5 py-2 text-white disabled:opacity-50"
          >
            {pending ? "正在分析…" : "发送"}
          </button>
        </div>
      </form>
    </section>
  );
}
