import type { ReactNode } from "react";

interface PageIntroProps {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}

export function PageIntro({
  eyebrow,
  title,
  description,
  actions,
}: PageIntroProps) {
  return (
    <section className="flex flex-col gap-6 rounded-[32px] border border-white/70 bg-[var(--panel)] px-8 py-7 shadow-[var(--shadow)] backdrop-blur-[14px] md:flex-row md:items-end md:justify-between">
      <div>
        <p className="mb-2 text-[0.78rem] uppercase tracking-[0.12em] text-[var(--muted)]">
          {eyebrow}
        </p>
        <h1 className="m-0 text-[clamp(1.5rem,2.4vw,2rem)] font-bold text-[var(--text)]">
          {title}
        </h1>
        <p className="mt-3 max-w-[68ch] text-sm leading-6 text-[var(--muted)]">
          {description}
        </p>
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
    </section>
  );
}
