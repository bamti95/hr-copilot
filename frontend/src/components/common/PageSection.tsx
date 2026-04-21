import type { ReactNode } from "react";

interface PageSectionProps {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
}

export function PageSection({ title, description, action, children }: PageSectionProps) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 shadow-[var(--shadow)] backdrop-blur-[14px]">
      <div className="mb-[18px] flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="m-0 text-2xl font-bold text-[var(--text)]">{title}</h2>
          {description ? <p className="mt-2 text-sm text-[var(--muted)]">{description}</p> : null}
        </div>
        {action ? <div>{action}</div> : null}
      </div>
      {children}
    </section>
  );
}
