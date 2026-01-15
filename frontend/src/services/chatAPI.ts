import axios from "axios";

export async function sendMessageToBackend(message: string) {
  const res = await axios.post(
    "http://127.0.0.1:8000/chat",
    { message },
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  return res.data;
}
