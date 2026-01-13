import express from "express";
import cors from "cors";
import amadeusRoute from "./routes/amadeus.route.js";

const app = express();

app.use(cors());
app.use(express.json());
app.use("/api/amadeus", amadeusRoute);

export default app;
