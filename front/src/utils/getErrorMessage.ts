function toReadableMessage(detail: unknown): string | undefined {
  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => toReadableMessage(item))
      .filter((message): message is string => Boolean(message));

    return messages.length > 0 ? messages.join(", ") : undefined;
  }

  if (detail && typeof detail === "object") {
    const record = detail as Record<string, unknown>;
    const loc = Array.isArray(record.loc)
      ? record
          .loc
          .filter((value) => typeof value === "string" || typeof value === "number")
          .join(".")
      : undefined;
    const msg = typeof record.msg === "string" ? record.msg : undefined;

    if (loc && msg) {
      return `${loc}: ${msg}`;
    }

    if (msg) {
      return msg;
    }
  }

  return undefined;
}

export function getErrorMessage(error: any, fallback: string) {
  const detail = error?.response?.data?.detail;
  return toReadableMessage(detail) ?? fallback;
}
