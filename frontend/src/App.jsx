import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
        <nav className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link to="/" className="text-xl font-bold tracking-tight text-emerald-400 hover:text-emerald-300">
              CDMS
            </Link>
            <div className="flex items-center space-x-6 text-sm font-medium text-slate-300">
              <Link to="/" className="hover:text-white transition">Home</Link>
              <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                v0.1.0 (Scaffold)
              </span>
            </div>
          </div>
        </nav>

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
          </Routes>
        </main>

        <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
          Cricket Data Management System &copy; 2026. Academic SE Lab Project.
        </footer>
      </div>
    </BrowserRouter>
  );
}

