import axios from "axios";

export async function sendMessageToBackend(message: string) {
  try {
    const res = await axios.post("http://localhost:4000/api/chat", { message });
    return res.data;
  } catch (error) {
    console.error("API error:", error);
    throw error;
  }
}
