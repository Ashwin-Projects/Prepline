import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Loading } from "./components/ui";
import { TargetProvider } from "./lib/target";

// Pages load on demand: Recharts and KaTeX stay out of the first bundle.
const Overview = lazy(() => import("./pages/Overview"));
const Compare = lazy(() => import("./pages/Compare"));
const Topics = lazy(() => import("./pages/Topics"));
const Confidence = lazy(() => import("./pages/Confidence"));
const Benchmark = lazy(() => import("./pages/Benchmark"));
const Methodology = lazy(() => import("./pages/Methodology"));

const page = (Component: React.ComponentType) => (
  <Suspense fallback={<Loading />}>
    <Component />
  </Suspense>
);

export default function App() {
  return (
    <TargetProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={page(Overview)} />
            <Route path="compare" element={page(Compare)} />
            <Route path="topics" element={page(Topics)} />
            <Route path="confidence" element={page(Confidence)} />
            <Route path="benchmark" element={page(Benchmark)} />
            <Route path="methodology" element={page(Methodology)} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TargetProvider>
  );
}
