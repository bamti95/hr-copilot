import { Navigate, RouterProvider, createBrowserRouter } from "react-router-dom";
import { ManagerLayout } from "../../common/layout/ManagerLayout";
import CandidatePage from "../../features/manager/Candidate";
import DashboardPage from "../../features/manager/Dashboard";
import DocumentPage from "../../features/manager/Document";
import InterviewQuestionPage from "../../features/manager/InterviewQuestion";
import InterviewSessionPage from "../../features/manager/InterviewSession";
import ManagerPage from "../../features/manager/Manager";
import OpsLogPage from "../../features/manager/OpsLog";
import PromptProfilePage from "../../features/manager/PromptProfile";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/manager/dashboard" replace />,
  },
  {
    path: "/manager",
    element: <ManagerLayout />,
    children: [
      { index: true, element: <Navigate to="/manager/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "managers", element: <ManagerPage /> },
      { path: "candidates", element: <CandidatePage /> },
      { path: "documents", element: <DocumentPage /> },
      { path: "prompt-profiles", element: <PromptProfilePage /> },
      { path: "interview-sessions", element: <InterviewSessionPage /> },
      { path: "interview-questions", element: <InterviewQuestionPage /> },
      { path: "ops-logs", element: <OpsLogPage /> },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/manager/dashboard" replace />,
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
