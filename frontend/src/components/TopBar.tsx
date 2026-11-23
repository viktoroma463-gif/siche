import type { Session } from "../types";

export default function TopBar({
  session,
  onExport,
  exporting,
  onNew,
}: {
  session: Session;
  onExport: () => void;
  exporting?: boolean;
  onNew: () => void;
}) {
  const configured = session.runtime.configured;

  return (
    <header className="topbar-shell sticky top-0 z-20 flex flex-wrap items-center justify-between gap-4 border-b border-black/10 bg-[#f7f1e6]/95 px-5 py-3 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="seal grid h-11 w-11 place-items-center text-sm font-bold">思拆</div>
        <div>
          <div className="font-serif text-xl leading-none">思拆</div>
          <div className="mt-1 max-w-md truncate text-xs text-ink-soft">
            {session.topic || "未命名写作任务"}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className={`flex items-center gap-2 ${configured ? "text-ink-soft" : "text-cinnabar"}`}>
          <span className={`inline-block h-2 w-2 rounded-full ${configured ? "bg-moss" : "bg-cinnabar"}`} />
          {configured ? `DeepSeek · ${session.runtime.model}` : "未配置密钥"}
        </span>
        <button
          className="border border-black/15 bg-white px-3 py-1.5 hover:border-cinnabar hover:text-cinnabar"
          onClick={onExport}
          disabled={exporting}
        >
          {exporting ? "导出中…" : "导出会话档案"}
        </button>
        <button
          className="border border-black/15 px-3 py-1.5 text-ink-soft hover:border-cinnabar hover:text-cinnabar"
          onClick={() => {
            if (window.confirm("开始新任务？当前会话会保存在本地数据库，界面将切换到新会话。")) onNew();
          }}
        >
          新任务
        </button>
      </div>
    </header>
  );
}
