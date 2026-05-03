type JsonRecord = Record<string, unknown>;

export interface TraceableLlmCallLog {
  nodeName: string | null;
  modelName: string;
  requestJson: JsonRecord | null;
  outputJson: JsonRecord | null;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  estimatedCost: number;
  elapsedMs: number | null;
  callStatus: string;
  errorMessage: string | null;
  startedAt: string | null;
  endedAt: string | null;
}

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isLlmCall(log: TraceableLlmCallLog): boolean {
  return log.modelName !== "local" && log.modelName !== "unknown";
}

function buildUsageEntry(log: TraceableLlmCallLog): JsonRecord {
  const usage: JsonRecord = {
    call_status: log.callStatus,
    ended_at: log.endedAt,
    model_name: log.modelName,
    node: log.nodeName,
    started_at: log.startedAt,
    elapsed_ms: log.elapsedMs,
    estimated_cost: log.estimatedCost,
    input_tokens: log.inputTokens,
    output_json: log.outputJson,
    output_tokens: log.outputTokens,
    request_json: log.requestJson,
    total_tokens: log.totalTokens,
  };

  if (log.errorMessage) {
    usage.error_message = log.errorMessage;
  }

  return usage;
}

function withUsageState(
  value: JsonRecord | null,
  llmUsages: JsonRecord[],
): JsonRecord {
  const base = value ?? {};
  const previousState = isRecord(base.state) ? base.state : {};

  return {
    ...base,
    llm_usages: llmUsages,
    state: {
      ...previousState,
      llm_usages: llmUsages,
    },
  };
}

export function withLangSmithStyleLlmUsages<T extends TraceableLlmCallLog>(
  logs: T[],
): T[] {
  const accumulatedUsages: JsonRecord[] = [];

  return logs.map((log) => {
    const inputUsages = [...accumulatedUsages];
    const currentUsage = isLlmCall(log) ? buildUsageEntry(log) : null;
    const outputUsages = currentUsage
      ? [...accumulatedUsages, currentUsage]
      : inputUsages;

    if (currentUsage) {
      accumulatedUsages.push(currentUsage);
    }

    return {
      ...log,
      requestJson: withUsageState(log.requestJson, inputUsages),
      outputJson: withUsageState(log.outputJson, outputUsages),
    };
  });
}
