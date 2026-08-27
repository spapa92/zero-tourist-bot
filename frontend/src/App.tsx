import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import LeadsListPage from "./pages/LeadsListPage";
import LeadDetailPage from "./pages/LeadDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <header className="app-header">
        <h1>FluxAssist — Lead</h1>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<LeadsListPage />} />
          <Route path="/leads/:phone" element={<LeadDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
