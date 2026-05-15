import {
  Navigate,
  RouterProvider,
  createBrowserRouter,
  useParams,
} from "react-router-dom";
import { ProtectedRoute } from "../../components/common/ProtectedRoute";
import { ManagerLayout } from "../../common/layout/ManagerLayout";
import ManagerLoginPage from "../../features/auth/ManagerLoginPage";
import CandidatePage from "../../features/manager/Candidate";
import CandidateDetailPage from "../../features/manager/Candidate/pages/CandidateDetailPage";
import CandidateDocumentPage from "../../features/manager/Candidate/pages/CandidateDocumentPage";
import DashboardPage from "../../features/manager/Dashboard";
import DocumentPage from "../../features/manager/Document";
import InterviewQuestionPage from "../../features/manager/InterviewQuestion";
import InterviewSessionPage from "../../features/manager/InterviewSession";
import InterviewSessionDetailPage from "../../features/manager/InterviewSession/pages/InterviewSessionDetailPage";
import JobPostingPage, {
  JobPostingDetailPage,
  JobPostingExperimentDetailPage,
  JobPostingExperimentListPage,
  JobPostingKnowledgePage,
  JobPostingNewPage,
  JobPostingReportPage,
} from "../../features/manager/JobPosting";
import LlmUsageDashboardPage from "../../features/manager/LlmUsageDashboard";
import ManagerPage from "../../features/manager/Manager";
import PromptProfilePage from "../../features/manager/PromptProfile";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/login" replace />,
  },
  {
    path: "/login",
    element: <ManagerLoginPage />,
  },
  {
    path: "/auth/login",
    element: <Navigate to="/login" replace />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: "/manager",
        element: <ManagerLayout />,
        children: [
          { index: true, element: <Navigate to="/manager/dashboard" replace /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "managers", element: <ManagerPage /> },
          { path: "candidates", element: <CandidatePage /> },
          { path: "candidates/new", element: <CandidateDetailPage mode="create" /> },
          { path: "candidates/:candidateId", element: <CandidateRouteDetailPage /> },
          {
            path: "candidates/:candidateId/documents/:documentId",
            element: <CandidateRouteDocumentPage />,
          },
          { path: "documents", element: <DocumentPage /> },
          { path: "prompt-profiles", element: <PromptProfilePage /> },
          { path: "interview-sessions", element: <InterviewSessionPage /> },
          {
            path: "interview-sessions/:sessionId",
            element: <InterviewSessionRouteDetailPage />,
          },
          { path: "interview-questions", element: <InterviewQuestionPage /> },
          { path: "job-postings", element: <JobPostingPage /> },
          { path: "job-posting-experiments", element: <JobPostingExperimentListPage /> },
          {
            path: "job-posting-experiments/:runId",
            element: <JobPostingExperimentDetailPage />,
          },
          { path: "job-postings/new", element: <JobPostingNewPage /> },
          {
            path: "job-postings/knowledge-sources",
            element: <JobPostingKnowledgePage />,
          },
          { path: "job-postings/:postingId", element: <JobPostingDetailPage /> },
          {
            path: "job-postings/:postingId/report",
            element: <JobPostingReportPage />,
          },
          { path: "llm-usage", element: <LlmUsageDashboardPage /> },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/login" replace />,
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}

function CandidateRouteDetailPage() {
  const { candidateId: candidateIdParam } = useParams();
  const candidateId = candidateIdParam ? Number(candidateIdParam) : undefined;
  return <CandidateDetailPage mode="detail" candidateId={candidateId} />;
}

function CandidateRouteDocumentPage() {
  const { candidateId: candidateIdParam, documentId: documentIdParam } = useParams();
  const candidateId = candidateIdParam ? Number(candidateIdParam) : undefined;
  const documentId = documentIdParam ? Number(documentIdParam) : undefined;

  return (
    <CandidateDocumentPage candidateId={candidateId} documentId={documentId} />
  );
}

function InterviewSessionRouteDetailPage() {
  const { sessionId: sessionIdParam } = useParams();
  const sessionId = sessionIdParam ? Number(sessionIdParam) : undefined;
  return <InterviewSessionDetailPage sessionId={sessionId} />;
}
