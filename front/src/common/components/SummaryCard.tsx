interface SummaryCardProps {
  icon: string;
  label: string;
  value: string;
  hint: string;
}

export function SummaryCard({ icon, label, value, hint }: SummaryCardProps) {
  return (
    <article className="summary-card">
      <div className="summary-card__icon" aria-hidden="true">
        {icon}
      </div>
      <div>
        <p className="summary-card__label">{label}</p>
        <strong>{value}</strong>
        <span>{hint}</span>
      </div>
    </article>
  );
}
