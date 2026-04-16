// src/pages/ErrorPage.jsx
import { useRouteError, Link } from "react-router-dom";

const ErrorPage = () => {
  const error = useRouteError();

  return (
    <div>
      <h1>오류가 발생했습니다</h1>
      <p>{error.statusText || error.message}</p>
      <Link to="/">홈으로 돌아가기</Link>
    </div>
  );
};

export default ErrorPage;