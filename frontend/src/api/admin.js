import api from "./axios.js";

export const admin = {
  getSession: () => api.get("/admin/session/"),
  getDashboardSummary: () => api.get("/admin/dashboard/summary/"),

  getBookings: (params = {}) => api.get("/admin/bookings/", { params }),
  getBookingDetail: (bookingId) => api.get(`/admin/bookings/${bookingId}/`),
  updateBookingStatus: (bookingId, data) =>
    api.patch(`/admin/bookings/${bookingId}/status/`, data),

  getRestaurantProfile: () => api.get("/admin/restaurant-profile/"),
  updateRestaurantProfile: (data) => api.patch("/admin/restaurant-profile/", data),

  getTables: (params = {}) => api.get("/admin/tables/", { params }),
  createTable: (data) => api.post("/admin/tables/", data),
  updateTable: (tableId, data) => api.patch(`/admin/tables/${tableId}/`, data),
  releaseTable: (tableId) => api.post(`/admin/tables/${tableId}/release/`),
  deleteTable: (tableId) => api.delete(`/admin/tables/${tableId}/`),

  getMenuCategories: () => api.get("/admin/menu/categories/"),
  createMenuCategory: (data) => api.post("/admin/menu/categories/", data),
  updateMenuCategory: (categoryId, data) =>
    api.patch(`/admin/menu/categories/${categoryId}/`, data),
  deleteMenuCategory: (categoryId) => api.delete(`/admin/menu/categories/${categoryId}/`),

  getMenuItems: (params = {}) => api.get("/admin/menu/items/", { params }),
  createMenuItem: (data) => api.post("/admin/menu/items/", data),
  updateMenuItem: (itemId, data) => api.patch(`/admin/menu/items/${itemId}/`, data),
  deleteMenuItem: (itemId) => api.delete(`/admin/menu/items/${itemId}/`),

  getSessions: (params = {}) => api.get("/admin/sessions/", { params }),
  createSession: (data) => api.post("/admin/sessions/", data),
  updateSession: (sessionId, data) => api.patch(`/admin/sessions/${sessionId}/`, data),
  mergeTableIntoSession: (sessionId, data) =>
    api.post(`/admin/sessions/${sessionId}/merge-table/`, data),
  moveTableInSession: (sessionId, data) =>
    api.post(`/admin/sessions/${sessionId}/move-table/`, data),
  checkoutSession: (sessionId, data) => api.post(`/admin/sessions/${sessionId}/checkout/`, data),

  getOrders: (params = {}) => api.get("/admin/orders/", { params }),
  createOrder: (data) => api.post("/admin/orders/", data),
  updateOrder: (orderId, data) => api.patch(`/admin/orders/${orderId}/`, data),
  sendOrderToKitchen: (orderId) => api.post(`/admin/orders/${orderId}/send-to-kitchen/`),
  addOrderItem: (orderId, data) => api.post(`/admin/orders/${orderId}/items/`, data),
  updateOrderItem: (orderItemId, data) => api.patch(`/admin/order-items/${orderItemId}/`, data),
  deleteOrderItem: (orderItemId) => api.delete(`/admin/order-items/${orderItemId}/`),
  splitOrderItem: (orderId, data) => api.post(`/admin/orders/${orderId}/split-item/`, data),
  mergeOrders: (data) => api.post("/admin/orders/merge/", data),

  getPayments: (params = {}) => api.get("/admin/payments/", { params }),
  getInvoices: () => api.get("/admin/invoices/"),

  getAdminUsers: () => api.get("/admin/users/"),
  createAdminUser: (data) => api.post("/admin/users/", data),
  updateAdminUser: (userId, data) => api.patch(`/admin/users/${userId}/`, data),
  deleteAdminUser: (userId) => api.delete(`/admin/users/${userId}/`),
};

export default admin;
