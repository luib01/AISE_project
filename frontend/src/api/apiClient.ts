import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000", // Matches backend URL
  timeout: 150000, // 150 seconds to allow for AI generation
  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
