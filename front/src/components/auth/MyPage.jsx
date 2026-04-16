// src/components/auth_prac/MyPage.jsx
import useAuthStore from "../../store/useAuthStore";

const MyPage = () => {
  const user = useAuthStore((state) => state.user);

  return (
    <div>
      <h1>마이페이지</h1>
      <p>이메일: {user?.email}</p>
    </div>
  );
};

export default MyPage;