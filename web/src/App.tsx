import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import About from "./pages/About";
import Home from "./pages/Home";
import ReportPage from "./pages/Report";
import SessionPage from "./pages/Session";
import VerifyPage from "./pages/Verify";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="session/:id" element={<SessionPage />} />
          <Route path="report/:id" element={<ReportPage />} />
          <Route path="verify/:id" element={<VerifyPage />} />
          <Route path="about" element={<About />} />
          <Route path="*" element={<Home />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
