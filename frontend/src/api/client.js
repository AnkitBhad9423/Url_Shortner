// src/api/client.js
import axios from "axios";

console.log("Backend URL:", import.meta.env.BACKEND_URL);
const client = axios.create({
  baseURL: import.meta.env.BACKEND_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// attach token to every request automatically
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// handle 401 globally — token expired or invalid
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export default client;
