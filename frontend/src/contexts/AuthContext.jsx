import { createContext, useContext, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");

    try {
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const login = async (email, password) => {
    const response = await api.post("/login", {
      email,
      password,
    });

    const {
      access_token,
      refresh_token,
      user: loggedInUser,
    } = response.data;

    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    localStorage.setItem("user", JSON.stringify(loggedInUser));

    setUser(loggedInUser);

    return loggedInUser;
  };

  const register = async (name, email, password, phone_number) => {
    const response = await api.post("/register", {
      name,
      email,
      password,
      phone_number,
    });

    const {
      access_token,
      refresh_token,
      user: registeredUser,
    } = response.data;

    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    localStorage.setItem("user", JSON.stringify(registeredUser));

    setUser(registeredUser);

    return registeredUser;
  };

  const logout = async () => {
    try {
      const accessToken = localStorage.getItem("access_token");

        if (accessToken) {
          await api.post("/logout", {}, { skipErrorHandler: true });
        }
    } catch (error) {
      console.error("Logout API failed:", error);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");

      setUser(null);
    }
  };

  const getProfile = async () => {
    const response = await api.get("/profile");
    const { user: profileUser } = response.data;
    localStorage.setItem("user", JSON.stringify(profileUser));
    setUser(profileUser);
    return profileUser;
  };

  const updateProfile = async (data) => {
    const response = await api.put("/profile", data, { skipErrorHandler: true });
    const { user: updatedUser } = response.data;
    localStorage.setItem("user", JSON.stringify(updatedUser));
    setUser(updatedUser);
    return updatedUser;
  };

  const changePassword = async (currentPassword, newPassword) => {
    const response = await api.put("/password", {
      current_password: currentPassword,
      new_password: newPassword,
    }, { skipErrorHandler: true });
    return response.data;
  };

  const deleteAccount = async (password) => {
    const response = await api.delete("/account", {
      data: { password },
      skipErrorHandler: true,
    });
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    setUser(null);
    return response.data;
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        getProfile,
        updateProfile,
        changePassword,
        deleteAccount,
        isAuthenticated,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};