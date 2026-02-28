import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { RestaurantBooking, BookingSearch } from "./pages";
import "./App.css";
import "./styles/style.css";

function App() {
  return (
    <Router>
      <Routes>
        {/* Restaurant Booking Routes */}
        <Route path="/" element={<RestaurantBooking />} />
        <Route path="/restaurant-booking" element={<RestaurantBooking />} />
        <Route path="/restaurant-booking/search" element={<BookingSearch />} />
        {/* Catch all route - redirect to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
