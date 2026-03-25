import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="fixed inset-0 bg-bg flex items-center justify-center">
        <div className="anim-spin-cw w-10 h-10 rounded-full border-2"
          style={{ borderColor: "transparent", borderTopColor: "#00D4FF" }} />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  return children;
}
