import { useMemo, useState } from "react";
import type { Message } from "../types";

export function CopyTestModal({
  message,
  disclaimer,
  reason,
  followup,
  pending,
  onSubmit,
  onRefuse,
}: {
  message: Message | null;
  disclaimer: string;
  reason: string;
  followup: string;
  pending: boolean;
  onSubmit: (option: "tweak" | "contrary" | "bounds", text: string) => void;
  onRefuse: () => void;
}) {
  const [option, setOption] = useState<"tweak" | "contrary" | "bounds">("tweak");
  const [text, setText] = useState("");
  const [activeId, setActiveId] = useState(message?.id ?? "");
  const count = useMemo(() => text.replace(/\s/g, "").length, [text]);

  if ((message?.id ?? "") !== activeId) {
    setActiveId(message?.id ?? "");
    setOption("tweak");
    setText("");
  }

  if (!message) return null;

  const options = [
    { id: "tweak" as const, label: "接受并微调", hint: "指出一处结合自身研究需要修改的地方" },
    { id: "contrary" as const, label: "补充对立思考", hint: "写出一条不同角度或反例" },
    { id: "bounds" as const, label: "指出适用边界", hint: "说明这套说法何时成立、何时可能不成立" },
  ];

  return (
    <div className="modal-backdrop fixed inset-0 z-40 grid place-items-center p-4">
      <div className="paper-card max-h-[92vh] w-full max-w-2xl overflow-auto p-8">
        <p className="text-xs tracking-[0.16em] text-cinnabar">复制前审查 · 仅此一次</p>
        <h2 className="mt-2 font-serif text-3xl">先审查，再复制</h2>

        <div className="mt-4 border border-cinnabar/25 bg-white p-4 text-sm leading-6 text-ink-soft">
          {disclaimer || "本内容为认知辅助支架，不可以直接粘贴进作业/论文；截图无法规避该机制，本设计目的唤起自主反思。"}
        </div>

        {message.content_type === "generated_draft" ? (
          <p className="mt-3 border border-cinnabar/30 bg-[#fbeee9] px-3 py-2 text-sm text-cinnabar">
            本条为 AI 参考草稿，必须完成微测试后才能复制。
          </p>
        ) : null}

        {followup ? (
          <div className="mt-4 border border-inkblue/30 bg-white p-4 text-sm leading-6">
            <span className="font-medium text-inkblue">再具体一点：</span>
            {followup}
          </div>
        ) : null}

        <p className="mt-4 text-sm text-ink-soft">
          请选择一项，用 80–300 字写下你的辨析。通过后本条回复的一键复制才会解锁；拒绝则保持锁定，文本仍可阅读。
        </p>

        <div className="mt-4 space-y-2">
          {options.map((item) => (
            <label
              key={item.id}
              className={`block cursor-pointer border px-4 py-3 ${
                option === item.id ? "border-cinnabar bg-white" : "border-black/10"
              }`}
            >
              <input
                type="radio"
                className="mr-2"
                checked={option === item.id}
                onChange={() => setOption(item.id)}
              />
              <span className="font-medium">{item.label}</span>
              <span className="ml-2 text-sm text-ink-soft">{item.hint}</span>
            </label>
          ))}
        </div>

        <textarea
          className="mt-4 min-h-[160px] w-full border border-black/15 bg-white px-3 py-2 outline-none focus:border-cinnabar"
          value={text}
          onChange={(e) => setText(e.target.value)}
          data-testid="micro-text"
          placeholder="写下具体的修改点、对立看法或适用条件…"
        />
        <p className={`mt-2 text-sm ${count < 80 || count > 300 ? "text-cinnabar" : "text-moss"}`}>
          当前 {count} 字 · 要求 80–300 字
        </p>
        <p className="mt-1 text-xs leading-5 text-ink-soft">
          你的本次测试作答将会保存在会话记录中，导出会话时会一并输出，可用于课程作业提交。
        </p>

        {reason ? (
          <p className="mt-2 border border-cinnabar/30 bg-white px-3 py-2 text-sm text-cinnabar">{reason}</p>
        ) : null}

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="bg-ink px-5 py-2 text-paper disabled:opacity-50"
            disabled={pending}
            data-testid="micro-submit"
            onClick={() => onSubmit(option, text)}
          >
            {pending ? "提交中…" : "提交辨析并申请解锁"}
          </button>
          <button className="border border-black/20 px-5 py-2" disabled={pending} onClick={onRefuse}>
            暂不测试，保持锁定
          </button>
        </div>
      </div>
    </div>
  );
}
