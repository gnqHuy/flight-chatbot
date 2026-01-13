import { StateGraph } from "@langchain/langgraph";
import { chatbotNode } from "./nodes.js";

export type ChatState = {
  messages: { role: "user" | "assistant"; content: string }[];
};

const workflow = new StateGraph<ChatState>({
  channels: {
    messages: {
      value: (x, y) => x.concat(y),
      default: () => [],
    },
  },
});

workflow.addNode("chatbot", chatbotNode);
workflow.setEntryPoint("chatbot");
workflow.setFinishPoint("chatbot");

export const chatGraph = workflow.compile();
