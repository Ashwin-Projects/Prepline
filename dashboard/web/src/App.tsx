import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { TargetProvider } from "./lib/target";
import Benchmark from "./pages/Benchmark";
import Compare from "./pages/Compare";
import Confidence from "./pages/Confidence";
import Methodology from "./pages/Methodology";
import Overview from "./pages/Overview";
import Topics from "./pages/Topics";

export default function App() {
  return (
    <TargetProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="compare" element={<Compare />} />
            <Route path="topics" element={<Topics />} />
            <Route path="confidence" element={<Confidence />} />
            <Route path="benchmark" element={<Benchmark />} />
            <Route path="methodology" element={<Methodology />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TargetProvider>
  );
}
