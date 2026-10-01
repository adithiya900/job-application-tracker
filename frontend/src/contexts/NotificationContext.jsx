import { createContext, useContext, useEffect, useState } from "react";
import toast from "react-hot-toast";
import {
  connectToNotificationStream,
  isLocalStatusChange,
} from "../services/notificationService";
import { useAuth } from "./AuthContext";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const [notifications, setNotifications] = useState([]);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    let cancelled = false;

    const handleNotification = (notification) => {
      if (cancelled) {
        return;
      }

      setNotifications((current) => {
        const existing = current.find(
          (n) => n.id === notification.id
        );

        if (existing) {
          return current;
        }

        return [
          {
            ...notification,
            id:
              notification.id ||
              `${Date.now()}-${Math.random()}`,
            read: false,
          },
          ...current,
        ];
      });

      const appId = notification.data?.application_id;
      const newStatus = notification.data?.new_status;

      if (appId && newStatus && isLocalStatusChange(appId, newStatus)) {
        return;
      }

      toast.success(notification.message);
    };

    const controller = connectToNotificationStream(
      handleNotification,
      (error) => {
        if (cancelled) {
          return;
        }
        console.error(
          "Notification connection failed:",
          error
        );
      }
    );

    return () => {
      cancelled = true;

      if (controller) {
        controller.abort();
      }
    };
  }, [isAuthenticated]);

  const unreadCount = notifications.filter(
    (notification) => !notification.read
  ).length;

  const markAllRead = () => {
    setNotifications((current) =>
      current.map((notification) => ({
        ...notification,
        read: true,
      }))
    );
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        markAllRead,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error(
      "useNotifications must be used inside NotificationProvider"
    );
  }

  return context;
}
