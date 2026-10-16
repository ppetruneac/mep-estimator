import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ProjectPicker } from "./pages/ProjectPicker";
import { ProjectView } from "./pages/ProjectView";
import { DrawingReview } from "./pages/DrawingReview";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<ProjectPicker />} />
          <Route path="/projects/:projectId" element={<ProjectView />} />
          <Route
            path="/projects/:projectId/drawings/:drawingId"
            element={<DrawingReview />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  </React.StrictMode>
);
