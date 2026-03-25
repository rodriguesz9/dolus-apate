import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Home        from "./pages/Home";
import Dashboard   from "./pages/Dashboard";
import ReportPage  from "./pages/ReportPage";
import HistoryPage from "./pages/HistoryPage";
import PricingPage from "./pages/PricingPage";
import LoginPage   from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-bg">
        <Navbar/>
        <Routes>
          {/* Public */}
          <Route path="/login"    element={<LoginPage/>}/>
          <Route path="/register" element={<RegisterPage/>}/>

          {/* Protected */}
          <Route path="/" element={<ProtectedRoute><Home/></ProtectedRoute>}/>
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard/></ProtectedRoute>}/>
          <Route path="/history"   element={<ProtectedRoute><HistoryPage/></ProtectedRoute>}/>
          <Route path="/report"    element={<ProtectedRoute><ReportPage/></ProtectedRoute>}/>
          <Route path="/report/:id" element={<ProtectedRoute><ReportPage/></ProtectedRoute>}/>
          <Route path="/plans"     element={<ProtectedRoute><PricingPage/></ProtectedRoute>}/>
        </Routes>
      </div>
    </AuthProvider>
  );
}
