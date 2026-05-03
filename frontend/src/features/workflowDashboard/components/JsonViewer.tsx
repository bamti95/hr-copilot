interface JsonViewerProps {
  value: unknown;
  maxHeightClassName?: string;
}

export function JsonViewer({
  value,
  maxHeightClassName = "max-h-[460px]",
}: JsonViewerProps) {
  if (value === null || value === undefined) {
    return (
      <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        표시할 JSON 데이터가 없습니다.
      </div>
    );
  }

  return (
    <pre
      className={[
        maxHeightClassName,
        "overflow-y-auto overflow-x-hidden whitespace-pre-wrap break-words rounded-lg border border-slate-200 bg-slate-950 p-4 text-xs leading-relaxed text-slate-100",
      ].join(" ")}
    >
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}
