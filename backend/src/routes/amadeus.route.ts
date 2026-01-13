import { Router, type Request, type Response } from "express";
import { amadeus } from "@/services/amadeus.service.js";
import fs from "fs";
import path from "path";

const router = Router();

router.get(
  "/flight-offers",
  async (_req: Request, res: Response): Promise<void> => {
    try {
      const response = await amadeus.shopping.flightOffersSearch.get({
        originLocationCode: "HAN",
        destinationLocationCode: "SGN",
        departureDate: "2026-03-01",
        adults: 1
      });

      const outputDir = path.resolve("mock");
      const outputFile = path.join(outputDir, "flight-offers.json");

      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }

      fs.writeFileSync(
        outputFile,
        JSON.stringify(
          {
            success: true,
            fetchedAt: new Date().toISOString(),
            data: response.data
          },
          null,
          2
        ),
        "utf-8"
      );

      res.status(200).json({
        success: true,
        message: "Flight offers fetched and saved to JSON",
        file: "mock/flight-offers.json",
        count: response.data?.length ?? 0
      });
    } catch (error: any) {
      console.error("AMADEUS ERROR:", error);

      res.status(error?.response?.statusCode ?? 500).json({
        success: false,
        message: error.message,
        code: error.code,
        details: error.response?.data
      });
    }
  }
);

export default router;
