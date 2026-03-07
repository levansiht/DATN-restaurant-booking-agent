import api from "./axios.js";

export const admin = {
  getSession: () => api.get("/admin/session/"),
  getDashboardSummary: () => api.get("/admin/dashboard/summary/"),

  getBookings: (params = {}) => api.get("/admin/bookings/", { params }),
  getBookingDetail: (bookingId) => api.get(`/admin/bookings/${bookingId}/`),
  updateBookingStatus: (bookingId, data) =>
    api.patch(`/admin/bookings/${bookingId}/status/`, data),

  getTables: (params = {}) => api.get("/admin/tables/", { params }),
  createTable: (data) => api.post("/admin/tables/", data),
  updateTable: (tableId, data) => api.patch(`/admin/tables/${tableId}/`, data),
  deleteTable: (tableId) => api.delete(`/admin/tables/${tableId}/`),

  getAdminUsers: () => api.get("/admin/users/"),
  createAdminUser: (data) => api.post("/admin/users/", data),
  updateAdminUser: (userId, data) => api.patch(`/admin/users/${userId}/`, data),
  deleteAdminUser: (userId) => api.delete(`/admin/users/${userId}/`),
};

export default admin;
