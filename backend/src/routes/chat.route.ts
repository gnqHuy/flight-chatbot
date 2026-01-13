import { Router } from "express";
import type { ChatRequest, ChatResponse } from "@/types/chat.js";
import { chatGraph } from "@/ai/graph.js";

const router = Router();

router.post("/", async (req, res) => {
  const body = req.body as ChatRequest;

  const result = await chatGraph.invoke({
    messages: [{ role: "user", content: body.message }],
  });

  const reply = result.messages.at(-1)?.content ?? "";

  const response: ChatResponse = { reply };
  res.json(response);
});

export default router;
