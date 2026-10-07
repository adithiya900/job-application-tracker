import axios from "axios";
import toast from "react-hot-toast";

const api = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback);
};

const onRefreshed = (newToken) => {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
};

const clearAuthAndRedirect = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");

  window.location.href = "/login";
};

const AUTH_ENDPOINTS = ["/login", "/register", "/refresh"];

const isAuthEndpoint = (url) =>
  AUTH_ENDPOINTS.some((endpoint) => endpoint === url);

const showGlobalError = (error) => {
  if (axios.isCancel(error) || error?.code === "ERR_CANCELED") {
    return;
  }

  const status = error?.response?.status;

  if (!error.response) {
    toast.error("Unable to connect to the server. Please check your connection.", {
      id: "api-network-error",
    });
    return;
  }

  if (status === 403) {
    toast.error("You don't have permission to perform this action.", {
      id: "api-forbidden",
    });
    return;
  }

  if (status === 404) {
    toast.error("The requested resource was not found.", {
      id: "api-not-found",
    });
    return;
  }

  if (status >= 500) {
    toast.error("Something went wrong on the server. Please try again later.", {
      id: "api-server-error",
    });
  }
};

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {};
    const status = error.response?.status;

    if (
      status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== "/refresh" &&
      originalRequest.url !== "/login" &&
      originalRequest.url !== "/register"
    ) {
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        toast.error("Your session has expired. Please log in again.", {
          id: "api-session-expired",
        });
        clearAuthAndRedirect();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken) => {
            if (!newToken) {
              reject(error);
              return;
            }

            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshResponse = await axios.post(
          "http://127.0.0.1:5000/refresh",
          {},
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          }
        );

        const newAccessToken = refreshResponse.data.access_token;
        localStorage.setItem("access_token", newAccessToken);
        isRefreshing = false;
        onRefreshed(newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        onRefreshed(null);
        toast.error("Your session has expired. Please log in again.", {
          id: "api-session-expired",
        });
        clearAuthAndRedirect();
        return Promise.reject(refreshError);
      }
    }

    if (!originalRequest.skipErrorHandler && !isAuthEndpoint(originalRequest.url)) {
      showGlobalError(error);
    }

    return Promise.reject(error);
  }
);

export default api;