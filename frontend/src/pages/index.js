export { default as RestaurantBooking } from "./RestaurantBooking.jsx";
export { default as BookingSearch } from "./BookingSearch.jsx";
export { default as AdminLogin } from "./AdminLogin.jsx";
// AdminPortal is intentionally not re-exported here so it can be lazy-loaded
// as its own chunk (see App.jsx). Import it directly from ./pages/AdminPortal.jsx.
