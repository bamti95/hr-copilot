// src/router/index.jsx
import { createBrowserRouter } from "react-router-dom";
import Layout from "../../layouts/Layout";
import NotFound from "../NotFound";
import ErrorPage from "../ErrorPage";
import Home from "../Home";
import LoginPage from "../../components/auth/LoginPage";
import SignupPage from "../../components/auth/SignupPage";
import ProtectedRoute from "../../components/ProtectedRoute";
import MyPage from "../../components/auth/MyPage";
import PostList from "../../components/post/PostList";
import PostWrite from "../../components/post/PostWrite";
import PostDetail from "../../components/post/PostDetail"
import Chat from "../../components/chat_prac/Chat";
import ChatHistory from "../../components/chat_prac/ChatHistory";
import AiChatPage from "../../components/chat_prac/AiChatPage";

// src/router/index.jsx
const router = createBrowserRouter([
  {
    path: "/", 
    element: <Layout />,
    errorElement: <ErrorPage />, 
    children: [
      { index: true, element: <Home /> },
      {
        path: "auth", 
        children: [
          { path: "login", element: <LoginPage /> },   // /auth/login
          { path: "signup", element: <SignupPage /> },  // /auth/signup
        ],
      },
      {
        path: "board",
        children: [
          { path: "posts", element: <PostList /> }, // /board/posts/new
          { path: "posts/:id", element: <PostDetail /> },
          {
            element: <ProtectedRoute />, 
            children: [
              { path: "posts/new", element: <PostWrite /> }, // /board/posts/new
            ],
          },
        ],
      },
      {
        path: "chat",
        children: [
          { path: "stream", element: <Chat /> },
          { path: "stream-history", element: <ChatHistory />},
          { path: "ai", element: <AiChatPage /> },
        ]
      },
      {
        element: <ProtectedRoute />,
        children: [
          { path: "mypage", element: <MyPage /> },      // /mypage
        ],
      },
    ],
  },
  {
    path: "*", 
    element: <NotFound />,
  }
]);

export default router;
