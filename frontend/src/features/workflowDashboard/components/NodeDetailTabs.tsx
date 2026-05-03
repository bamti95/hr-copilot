import type { DetailTab } from "../types/workflowDashboard.types";

const tabs: Array<{ key: DetailTab; label: string }> = [
  { key: "feedback", label: "피드백" },
  { key: "input", label: "입력" },
  { key: "output", label: "출력" },
  { key: "state", label: "상태" },
  { key: "router", label: "라우터" },
  { key: "meta", label: "메타" },
];

interface NodeDetailTabsProps {
  activeTab: DetailTab;
  onChange: (tab: DetailTab) => void;
}

export function NodeDetailTabs({ activeTab, onChange }: NodeDetailTabsProps) {
  return (
    <div className="mb-3 flex flex-wrap gap-2">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className={`h-9 rounded-lg border px-3 text-xs font-semibold transition ${
            activeTab === tab.key
              ? "border-[#315fbc] bg-[#315fbc] text-white"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

