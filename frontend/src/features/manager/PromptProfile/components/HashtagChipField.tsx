import { useId, useState, type ReactNode } from "react";

const fieldClassName =
  "min-h-11 w-full rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-2 text-[var(--text)] outline-none transition focus:border-[var(--primary)]";

function normalizeTag(raw: string): string {
  return raw.replace(/^#+/, "").trim();
}

function displayTag(label: string) {
  const t = normalizeTag(label);
  return t ? `#${t}` : "";
}

interface HashtagChipFieldProps {
  label: ReactNode;
  suggestions: string[];
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
  maxTagLength?: number;
}

export function HashtagChipField({
  label,
  suggestions,
  value,
  onChange,
  disabled = false,
  maxTagLength = 40,
}: HashtagChipFieldProps) {
  const id = useId();
  const [draft, setDraft] = useState("");
  const [adding, setAdding] = useState(false);

  const lowerSet = new Set(value.map((t) => normalizeTag(t).toLowerCase()));

  const addTag = (raw: string) => {
    const tag = normalizeTag(raw);
    if (!tag || tag.length > maxTagLength) {
      return;
    }
    if (lowerSet.has(tag.toLowerCase())) {
      setDraft("");
      setAdding(false);
      return;
    }
    onChange([...value, tag]);
    setDraft("");
    setAdding(false);
  };

  const removeAt = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const availableSuggestions = suggestions.filter(
    (s) => !lowerSet.has(normalizeTag(s).toLowerCase()),
  );

  return (
    <div className="text-sm font-medium text-[var(--text)]">
      <div className="flex flex-wrap items-center gap-2">{label}</div>
      <div className="mt-2 flex min-h-11 flex-wrap items-center gap-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-strong)] px-3 py-2">
        {value.map((tag, index) => (
          <span
            key={`${tag}-${index}`}
            className="inline-flex items-center gap-1 rounded-full border border-sky-200 bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-800"
          >
            {displayTag(tag)}
            <button
              type="button"
              className="rounded-full px-0.5 text-sky-600 hover:bg-sky-100 hover:text-sky-900 disabled:opacity-40"
              onClick={() => removeAt(index)}
              disabled={disabled}
              aria-label={`${tag} 제거`}
            >
              ×
            </button>
          </span>
        ))}
        {availableSuggestions.map((s) => (
          <button
            key={s}
            type="button"
            className="rounded-full border border-dashed border-[var(--line)] px-2.5 py-1 text-xs font-medium text-[var(--muted)] hover:border-[var(--primary)] hover:text-[var(--primary)] disabled:opacity-40"
            onClick={() => addTag(s)}
            disabled={disabled}
          >
            {displayTag(s)}
          </button>
        ))}
        {adding ? (
          <input
            id={id}
            className={`${fieldClassName} min-h-9 max-w-[200px] flex-1 border-dashed py-1 text-xs`}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addTag(draft);
              }
              if (e.key === "Escape") {
                setDraft("");
                setAdding(false);
              }
            }}
            onBlur={() => {
              if (draft.trim()) {
                addTag(draft);
              } else {
                setAdding(false);
              }
            }}
            placeholder="직접 입력"
            disabled={disabled}
            maxLength={maxTagLength + 4}
            autoFocus
          />
        ) : (
          <button
            type="button"
            className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--line)] text-lg font-medium text-[var(--muted)] hover:border-[var(--primary)] hover:text-[var(--primary)] disabled:opacity-40"
            onClick={() => setAdding(true)}
            disabled={disabled}
            aria-label="태그 직접 추가"
          >
            +
          </button>
        )}
      </div>
    </div>
  );
}
