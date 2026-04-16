interface SummaryCardProps {
  icon: string;
  label: string;
  value: string;
  hint: string;
}

export function SummaryCard({ icon, label, value, hint }: SummaryCardProps) {
  return (
    <article className="flex items-center gap-4 rounded-[26px] border border-white/70 bg-white/74 p-[22px]">
      <div
        className="grid h-12 w-12 place-items-center rounded-2xl bg-linear-to-br from-[#e9faff] to-[#d9ffe8] font-extrabold text-[#1b5f49]"
        aria-hidden="true"
      >
        {icon}
      </div>
      <div>
        <p className="m-0 text-sm text-[var(--muted)]">{label}</p>
        <strong className="my-1.5 block text-[2rem] leading-none text-[var(--text)]">{value}</strong>
        <span className="text-sm text-[var(--muted)]">{hint}</span>
      </div>
    </article>
  );
}
