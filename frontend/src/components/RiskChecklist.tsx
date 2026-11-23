const ITEMS = [
  ["信息真实性", "AI 给出的文献、数据与事实是否已由你核验来源？"],
  ["研究逻辑一致性", "问题、证据与结论是否在回答同一件事？"],
  ["独立理解", "你能否不看生成文本，用自己的话复述当前判断？"],
  ["批判性判断", "你是否写下了对立可能或适用边界？"],
  ["成果归属", "核心观点与结论是否确为你本人的思考？"],
];

export default function RiskChecklist({ flash }: { flash: boolean }) {
  return (
    <section
      id="risk-checklist"
      data-testid="risk-checklist"
      className={`border p-3 transition-colors ${flash ? "risk-flash" : "border-black/10 bg-white"}`}
    >
      <h2 className="font-serif text-xl">风险审查清单</h2>
      <p className="mt-1 text-xs leading-5 text-ink-soft">纯自我反思，无需勾选或提交。</p>
      <ul className="mt-3 space-y-2 text-xs leading-5">
        {ITEMS.map(([title, hint]) => (
          <li key={title}>
            <span className="font-medium">{title}</span>
            <p className="text-ink-soft">{hint}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
