import { Navigate } from "react-router-dom";

function Home() {
  return <Navigate to="/admin/login" replace />;
}

export default Home;
