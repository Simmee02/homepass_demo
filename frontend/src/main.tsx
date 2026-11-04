import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import Intro from './pages/Intro';
import When from './pages/When';
import Where from './pages/Where';
import Money from './pages/Money';
import Result from './pages/Result';
import LoanDetail from './pages/LoanDetail';
import Split from './pages/Split';
import './styles.css';

function ScrollTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ScrollTop />
      <Routes>
        <Route path="/" element={<Intro />} />
        <Route path="/when" element={<When />} />
        <Route path="/where" element={<Where />} />
        <Route path="/money" element={<Money />} />
        <Route path="/result" element={<Result />} />
        <Route path="/loan/:productId" element={<LoanDetail />} />
        <Route path="/split" element={<Split />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
