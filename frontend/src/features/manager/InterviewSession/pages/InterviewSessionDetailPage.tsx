import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageIntro } from "../../../../common/components/PageIntro";
import { getErrorMessage } from "../../../../utils/getErrorMessage";
import { getJobPositionLabel } from "../../common/candidateJobPosition";
import { InterviewSessionAssembledPayloadView } from "../components/InterviewSessionAssembledPayloadView";
import { fetchInterviewSessionDetail } from "../services/interviewSessionService";
import type { InterviewSessionDetailResponse } from "../types";

interface InterviewSessionDetailPageProps {
  sessionId?: number;
}

function formatDateTime(value: string) {
  return value.replace("T", " ").slice(0, 16);
}

export default function InterviewSessionDetailPage({
  sessionId,
}: InterviewSessionDetailPageProps) {
  const navigate = useNavigate();
  const [detail, setDetail] = useState<InterviewSessionDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let active = true;

    const run = async () => {
      if (!sessionId || Number.isNaN(sessionId)) {
        setErrorMessage("유효한 면접 세션 ID가 필요합니다.");
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setErrorMessage("");
        const response = await fetchInterviewSessionDetail(sessionId);
        if (!active) {
          return;
        }
        setDetail(response);
      } catch (error) {
        if (!active) {
          return;
        }
        setErrorMessage(
          getErrorMessage(error, "면접 세션 상세 정보를 불러오지 못했습니다."),
        );
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    void run();

    return () => {
      active = false;
    };
  }, [sessionId]);

  return (
    <div className="space-y-6">
      <PageIntro
        eyebrow="interview session detail"
        title={detail ? `${detail.candidateName} 세션 상세` : "면접 세션 상세"}
        description="세션 생성 직후 조립된 request payload를 상세 화면에서 바로 확인할 수 있습니다."
        actions={
          <button
            type="button"
            className="inline-flex h-10 items-center justify-center rounded-xl border border-[var(--line)] bg-[var(--panel-strong)] px-4 text-sm font-semibold text-[var(--text)] transition hover:bg-white/80"
            onClick={() => navigate("/manager/interview-sessions")}
          >
            목록으로
          </button>
        }
      />

      {errorMessage ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      ) : null}

      {isLoading ? (
        <section className="rounded-[32px] border border-white/70 bg-[var(--panel)] p-7 text-sm text-[var(--muted)] shadow-[var(--shadow)]">
          상세 데이터를 불러오는 중입니다...
        </section>
      ) : null}

      {detail ? (
        <>
          <section className="grid gap-4 lg:grid-cols-4">
            <div className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-6 shadow-[var(--shadow)]">
              <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                Session ID
              </div>
              <div className="mt-3 text-lg font-bold text-[var(--text)]">{detail.id}</div>
            </div>
            <div className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-6 shadow-[var(--shadow)]">
              <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                목표 직무
              </div>
              <div className="mt-3 text-lg font-bold text-[var(--text)]">
                {getJobPositionLabel(detail.targetJob)}
              </div>
            </div>
            <div className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-6 shadow-[var(--shadow)]">
              <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                난이도
              </div>
              <div className="mt-3 text-lg font-bold text-[var(--text)]">
                {detail.difficultyLevel ?? "-"}
              </div>
            </div>
            <div className="rounded-[28px] border border-white/70 bg-[var(--panel)] p-6 shadow-[var(--shadow)]">
              <div className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--muted)]">
                생성 시각
              </div>
              <div className="mt-3 text-lg font-bold text-[var(--text)]">
                {formatDateTime(detail.createdAt)}
              </div>
            </div>
          </section>

          <InterviewSessionAssembledPayloadView detail={detail} />
        </>
      ) : null}
    </div>
  );
}
