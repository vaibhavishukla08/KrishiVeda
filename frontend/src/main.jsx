import { StrictMode, lazy } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import { AppProvider } from "./hooks/AppContext";
import Layout from "./components/Layout";

// Each page is loaded on demand to keep the first download small on slow mobile networks
const Dashboard = lazy(() => import("./pages/Dashboard"));
const DiseaseDetection = lazy(() => import("./pages/DiseaseDetection"));
const Weather = lazy(() => import("./pages/Weather"));
const CropRecommendation = lazy(() => import("./pages/CropRecommendation"));
const MarketPrices = lazy(() => import("./pages/MarketPrices"));
const Advisory = lazy(() => import("./pages/Advisory"));
const AskExpert = lazy(() => import("./pages/AskExpert"));
const ExpertPanel = lazy(() => import("./pages/ExpertPanel"));
const Profile = lazy(() => import("./pages/Profile"));
const Schemes = lazy(() => import("./pages/Schemes"));
const Stubble = lazy(() => import("./pages/Stubble"));
const Analytics = lazy(() => import("./pages/Analytics"));
const NotFound = lazy(() => import("./pages/NotFound"));

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="disease" element={<DiseaseDetection />} />
            <Route path="weather" element={<Weather />} />
            <Route path="crops" element={<CropRecommendation />} />
            <Route path="market" element={<MarketPrices />} />
            <Route path="advisory" element={<Advisory />} />
            <Route path="expert" element={<AskExpert />} />
            <Route path="expert/panel" element={<ExpertPanel />} />
            <Route path="profile" element={<Profile />} />
            <Route path="schemes" element={<Schemes />} />
            <Route path="stubble" element={<Stubble />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  </StrictMode>
);
