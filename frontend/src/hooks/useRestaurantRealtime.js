import { useEffect, useRef, useState } from "react";


const RESTAURANT_REALTIME_CHANNEL = "restaurant_booking_updates";
const RESTAURANT_REALTIME_STORAGE_KEY = "restaurant_booking_updates_event";
const MAX_RECONNECT_DELAY_MS = 30000;
const MIN_RECONNECT_DELAY_MS = 2000;


function resolveApiBaseUrl() {
  const realtimeUrl = import.meta.env.VITE_REALTIME_WS_URL;
  if (realtimeUrl) {
    return new URL(realtimeUrl, window.location.origin);
  }

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
  return new URL(apiBaseUrl, window.location.origin);
}


function buildRealtimeUrl() {
  const url = resolveApiBaseUrl();
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/restaurant-booking/updates/";
  url.search = "";
  return url.toString();
}


function normalizeRealtimeEvent(event, transport = "local") {
  return {
    domain: event?.domain || "restaurant_booking",
    type: event?.type || "booking.changed",
    transport,
    event_id:
      event?.event_id ||
      (window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`),
    emitted_at: event?.emitted_at || new Date().toISOString(),
    ...event,
  };
}


export function publishRestaurantRealtimeEvent(event) {
  const payload = normalizeRealtimeEvent(event, "local");

  if (typeof BroadcastChannel !== "undefined") {
    const channel = new BroadcastChannel(RESTAURANT_REALTIME_CHANNEL);
    channel.postMessage(payload);
    channel.close();
  }

  try {
    window.localStorage.setItem(RESTAURANT_REALTIME_STORAGE_KEY, JSON.stringify(payload));
    window.localStorage.removeItem(RESTAURANT_REALTIME_STORAGE_KEY);
  } catch (error) {
    console.error("Failed to persist realtime fallback event:", error);
  }

  return payload;
}


export function useRestaurantRealtime({ enabled = true, onEvent }) {
  const onEventRef = useRef(onEvent);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!enabled) {
      setIsConnected(false);
      return undefined;
    }

    let socket = null;
    let reconnectTimer = null;
    let heartbeatTimer = null;
    let broadcastChannel = null;
    let isDisposed = false;
    let connectionActive = false;
    let reconnectAttempts = 0;

    const handleRealtimeEvent = (payload) => {
      if (!payload) {
        return;
      }
      onEventRef.current?.(payload);
    };

    const handleStorage = (event) => {
      if (event.key !== RESTAURANT_REALTIME_STORAGE_KEY || !event.newValue) {
        return;
      }

      try {
        handleRealtimeEvent(JSON.parse(event.newValue));
      } catch (error) {
        console.error("Failed to parse storage realtime payload:", error);
      }
    };

    const clearTimers = () => {
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      if (heartbeatTimer) {
        window.clearInterval(heartbeatTimer);
      }
    };

    const scheduleReconnect = () => {
      clearTimers();
      connectionActive = false;
      setIsConnected(false);
      if (!isDisposed) {
        reconnectAttempts += 1;
        const reconnectDelay = Math.min(
          MAX_RECONNECT_DELAY_MS,
          MIN_RECONNECT_DELAY_MS * (2 ** (reconnectAttempts - 1))
        );
        reconnectTimer = window.setTimeout(() => {
          if (document.visibilityState === "hidden") {
            scheduleReconnect();
            return;
          }

          connect();
        }, reconnectDelay);
      }
    };

    const connect = () => {
      try {
        socket = new WebSocket(buildRealtimeUrl());
      } catch (error) {
        console.error("Failed to initialize realtime websocket:", error);
        scheduleReconnect();
        return;
      }

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          handleRealtimeEvent(payload);
        } catch (error) {
          console.error("Failed to parse realtime payload:", error);
        }
      };

      socket.onopen = () => {
        reconnectAttempts = 0;
        connectionActive = true;
        setIsConnected(true);
        heartbeatTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send("ping");
          }
        }, 25000);
      };

      socket.onerror = () => {
        socket?.close();
      };

      socket.onclose = () => {
        connectionActive = false;
        scheduleReconnect();
      };
    };

    const handleVisibilityChange = () => {
      if (
        document.visibilityState === "visible" &&
        !isDisposed &&
        !connectionActive &&
        !reconnectTimer &&
        (!socket || socket.readyState === WebSocket.CLOSED)
      ) {
        connect();
      }
    };

    if (typeof BroadcastChannel !== "undefined") {
      broadcastChannel = new BroadcastChannel(RESTAURANT_REALTIME_CHANNEL);
      broadcastChannel.onmessage = (event) => handleRealtimeEvent(event.data);
    }

    window.addEventListener("storage", handleStorage);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    connect();

    return () => {
      isDisposed = true;
      setIsConnected(false);
      clearTimers();
      window.removeEventListener("storage", handleStorage);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      broadcastChannel?.close();
      socket?.close();
    };
  }, [enabled]);

  return { isConnected };
}


export default useRestaurantRealtime;
