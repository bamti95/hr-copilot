import { Link } from "react-router-dom";

function NotFound() {
  return (
    <div className="simple-page">
      <div className="simple-page__panel">
        <p className="eyebrow">404</p>
        <h1>페이지를 찾을 수 없습니다.</h1>
        <p>입력한 주소가 변경되었거나 존재하지 않습니다.</p>
        <Link to="/admin/dashboard" className="button-primary">
          관리자 대시보드로 이동
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
