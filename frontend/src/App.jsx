import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import {
  AdminLogin,
  AdminPortal,
  BookingSearch,
  RestaurantBooking,
} from "./pages";
import { isAdminAuthenticated } from "./api";
import {
  ADMIN_LOGIN_PATH,
  ADMIN_PORTAL_PATH,
  BOOKING_SEARCH_PATH,
  GUEST_HOME_PATH,
} from "./constants/routes.js";
import "./App.css";
import "./styles/style.css";

function ProtectedAdminRoute({ children }) {
  return isAdminAuthenticated() ? children : <Navigate to={ADMIN_LOGIN_PATH} replace />;
}

function AdminLoginRoute() {
  return isAdminAuthenticated() ? <Navigate to={ADMIN_PORTAL_PATH} replace /> : <AdminLogin />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RestaurantBooking />} />
        <Route path={GUEST_HOME_PATH} element={<RestaurantBooking />} />
        <Route path={BOOKING_SEARCH_PATH} element={<BookingSearch />} />
        <Route path={ADMIN_LOGIN_PATH} element={<AdminLoginRoute />} />
        <Route
          path={ADMIN_PORTAL_PATH}
          element={
            <ProtectedAdminRoute>
              <AdminPortal />
            </ProtectedAdminRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
