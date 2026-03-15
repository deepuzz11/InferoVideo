import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Nav from './components/Nav'
import Toasts from './components/Toasts'
import HomePage from './pages/HomePage'
import WorkspacePage from './pages/WorkspacePage'
import JobsPage from './pages/JobsPage'

export default function App() {
  return (
    <BrowserRouter>
      {/* Ambient background blobs */}
      <div className="ambient ambient-1" />
      <div className="ambient ambient-2" />
      <div className="ambient ambient-3" />

      <div className="app-shell">
        <Nav />
        <Routes>
          <Route path="/"                    element={<HomePage />} />
          <Route path="/jobs"                element={<JobsPage />} />
          <Route path="/workspace/:jobId"    element={<WorkspacePage />} />
        </Routes>
      </div>

      <Toasts />
    </BrowserRouter>
  )
}
