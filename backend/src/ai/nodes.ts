import type { ChatState } from "./graph.js";
import { llm } from "./llm.js";

export async function chatbotNode(state: ChatState) {
  const res = await llm.invoke(state.messages);
  return {
    messages: [{ role: "assistant", content: res.content as string }],
  };
}
