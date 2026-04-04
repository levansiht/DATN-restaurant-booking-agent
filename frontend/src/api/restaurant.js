import api from './axios.js';

// Restaurant booking API endpoints
export const restaurant = {
  getRestaurantProfile: () => api.get('/restaurant-booking/restaurant-profile/'),
  getMenu: (params = {}) => api.get('/restaurant-booking/menu/', { params }),
  getTables: (params = {}) => api.get('/restaurant-booking/tables/', { params }),
  searchTables: (searchData) => api.post('/restaurant-booking/tables/search/', searchData),
  createBooking: (bookingData) => api.post('/restaurant-booking/bookings/create/', bookingData),
  searchBookingByCode: (code) => api.get('/restaurant-booking/bookings/search/', { params: { code: code } }),
  sendMessage: async (messageData) => {
    const controller = new AbortController();

    try {
      const baseURL = api.defaults?.baseURL || '';
      const response = await fetch(
        `${baseURL}/restaurant-booking/chat/stream/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(messageData),
          signal: controller.signal,
        }
      );

      if (!response.ok) {
        controller.abort();
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Stream reader for SSE
      const reader = response.body.getReader();
      return { reader, controller };
    } catch (error) {
      controller.abort();
      console.error('[Streaming Error]:', error);
      throw error;
    }
  },
};

export default restaurant;
