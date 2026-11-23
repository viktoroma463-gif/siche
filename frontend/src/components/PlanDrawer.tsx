import { useState } from "react";
import type { Plan } from "../types";

const FIELDS: Array<{ key: keyof Plan; label: string; placeholder: string }> = [
  { key: "question", label: "我的问题", placeholder: "写下你的核心研究问题" },
  { key: "evidence", label: "当前已有的证据", placeholder: "整理你手上已有的资料、观点、证据" },
  { key: "doubts", label: "尚存疑点 / 待思考", placeholder: "还没想明白、有待辨析的问题" },
  { key: "next_step", label: "下一步打算做什么", placeholder: "接下来计划完成的思考或任务" },
];

export default function PlanDrawer({
  open,
  plan,
  pending,
  onClose,
  onSave,
  onPrefill,
}: {
  open: boolean;
  plan: Plan;
  pending: boolean;
  onClose: () => void;
  onSave: (plan: Plan) => void;
  onPrefill: () => void;
}) {
  const [fields, setFields] = useState<Plan>(plan);
  const planKey = JSON.stringify(plan);
  const [prevPlanKey, setPrevPlanKey] = useState(planKey);
  const [prevOpen, setPrevOpen] = useState(open);

  if (open !== prevOpen || planKey !== prevPlanKey) {
    setPrevOpen(open);
    setPrevPlanKey(planKey);
    setFields(plan);
  }

  if (!open) return null;

  const update = (key: keyof Plan, value: string) => {
    setFields((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div
      data-testid="plan-drawer"
      className="plan-drawer fixed bottom-0 left-0 top-16 z-30 w-[360px] overflow-y-auto border-r border-black/15 bg-sheet p-5 shadow-2xl"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h2 className="font-serif text-2xl">研究规划单</h2>
          <p className="mt-1 text-xs leading-5 text-ink-soft">
            可以手动编辑修改，预填充仅为辅助参考。
          </p>
        </div>
        <button
          className="grid h-8 w-8 place-items-center border border-black/15 text-lg hover:border-cinnabar hover:text-cinnabar"
          onClick={onClose}
          aria-label="关闭研究规划单"
        >
          ×
        </button>
      </div>

      <button
        className="mt-4 w-full border border-cinnabar px-3 py-2 text-sm text-cinnabar hover:bg-cinnabar hover:text-white disabled:opacity-50"
        onClick={onPrefill}
        disabled={pending}
      >
        从对话提取思考预填充
      </button>

      <div className="mt-5 space-y-4">
        {FIELDS.map((field) => (
          <label key={field.key} className="block text-sm">
            <span className="font-medium">{field.label}</span>
            <textarea
              className="mt-1 min-h-[92px] w-full resize-y border border-black/15 bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-cinnabar"
              value={fields[field.key]}
              placeholder={field.placeholder}
              onChange={(e) => update(field.key, e.target.value)}
              onBlur={() => onSave(fields)}
            />
          </label>
        ))}
      </div>

      <button
        className="mt-5 w-full bg-ink px-5 py-2 text-paper disabled:opacity-50"
        onClick={() => onSave(fields)}
        disabled={pending}
      >
        保存
      </button>
      <p className="mt-2 text-xs text-ink-soft">输入框失去焦点会自动保存。</p>
    </div>
  );
}
