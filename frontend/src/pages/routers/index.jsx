import { createBrowserRouter, Navigate } from "react-router-dom";
import ProtectedRoute from "../../components/ProtectedRoute";
import AdminLoginPage from "../../features/auth/AdminLogin";
import { ManagerLayout } from "../../common/layout/ManagerLayout";
import DashboardPage from "../../features/manager/Dashboard";
import ManagerPage from "../../features/manager/Manager";
import CandidatePage from "../../features/manager/Candidate";
import DocumentPage from "../../features/manager/Document";
import PromptProfilePage from "../../features/manager/PromptProfile";
import InterviewSessionPage from "../../features/manager/InterviewSession";
import InterviewQuestionPage from "../../features/manager/InterviewQuestion";
import OpsLogPage from "../../features/manager/OpsLog";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/admin/login" replace />,
  },
  {
    path: "/admin/login",
    element: <AdminLoginPage />,
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
          { path: "documents", element: <DocumentPage /> },
          { path: "prompt-profiles", element: <PromptProfilePage /> },
          { path: "interview-sessions", element: <InterviewSessionPage /> },
          { path: "interview-questions", element: <InterviewQuestionPage /> },
          { path: "ops-logs", element: <OpsLogPage /> },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/admin/login" replace />,
  },
]);

export default router;
