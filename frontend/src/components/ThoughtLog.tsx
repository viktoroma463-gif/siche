import type { Message } from "../types";

function fmt(ts: string) {
  try {
    return new Date(ts).toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function ThoughtLog({ messages }: { messages: Message[] }) {
  const inputs = messages.filter((m) => m.role === "user");

  return (
    <section>
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="font-serif text-xl">个人思想留存区</h2>
        <span className="text-xs text-ink-soft">{inputs.length} 条</span>
      </div>
      <p className="mt-1 text-xs leading-5 text-ink-soft">
        你在协作区的全部发言自动保存，只追加、不覆盖；关闭后重新打开仍会保留。
      </p>
      <div className="mt-3 max-h-56 space-y-2 overflow-y-auto pr-1" data-testid="thought-log">
        {inputs.length ? (
          inputs.map((message) => (
            <article key={message.id} className="border border-black/10 bg-white p-2 text-xs leading-5">
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p className="mt-1 text-ink-soft">{fmt(message.ts)}</p>
            </article>
          ))
        ) : (
          <p className="border border-dashed border-black/15 px-3 py-3 text-xs leading-5 text-ink-soft">
            还没有发言。你在右侧写下的草稿、判断与困惑会自动出现在这里。
          </p>
        )}
      </div>
    </section>
  );
}
