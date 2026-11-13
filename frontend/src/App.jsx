import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Layouts & Guard
import PublicLayout from './layouts/PublicLayout';
import AdminLayout from './layouts/AdminLayout';
import ProtectedRoute from './components/ProtectedRoute';

// Public Pages
import HomePage from './pages/HomePage';
import TournamentsPage from './pages/TournamentsPage';
import TournamentStandingsPage from './pages/TournamentStandingsPage';
import TeamsPage from './pages/TeamsPage';
import PlayersPage from './pages/PlayersPage';
import PlayerProfilePage from './pages/PlayerProfilePage';
import LiveScoresPage from './pages/LiveScoresPage';
import MatchScorecardPage from './pages/MatchScorecardPage';
import LoginPage from './pages/LoginPage';
import ForbiddenPage from './pages/ForbiddenPage';
import NotFoundPage from './pages/NotFoundPage';

// Admin Pages
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import AdminTournamentsPage from './pages/admin/AdminTournamentsPage';
import AdminTeamsPage from './pages/admin/AdminTeamsPage';
import AdminPlayersPage from './pages/admin/AdminPlayersPage';
import AdminVenuesPage from './pages/admin/AdminVenuesPage';
import AdminMatchesPage from './pages/admin/AdminMatchesPage';
import AdminScoringPage from './pages/admin/AdminScoringPage';
import AdminPointsTablePage from './pages/admin/AdminPointsTablePage';
import AdminStatsPage from './pages/admin/AdminStatsPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminReportsPage from './pages/admin/AdminReportsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes with Top Nav */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/tournaments" element={<TournamentsPage />} />
          <Route path="/tournaments/:id" element={<TournamentStandingsPage />} />
          <Route path="/tournaments/:id/standings" element={<TournamentStandingsPage />} />
          <Route path="/teams" element={<TeamsPage />} />
          <Route path="/players" element={<PlayersPage />} />
          <Route path="/players/:id" element={<PlayerProfilePage />} />
          <Route path="/live-scores" element={<LiveScoresPage />} />
          <Route path="/live" element={<Navigate to="/live-scores" replace />} />
          <Route path="/matches/:id" element={<MatchScorecardPage />} />
          <Route path="/match/:id" element={<MatchScorecardPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forbidden" element={<ForbiddenPage />} />
        </Route>

        {/* Protected Admin & Scorer Routes with Dark Sidebar */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin', 'scorer']}>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<AdminDashboardPage />} />
          <Route path="tournaments" element={<AdminTournamentsPage />} />
          <Route path="teams" element={<AdminTeamsPage />} />
          <Route path="players" element={<AdminPlayersPage />} />
          <Route path="venues" element={<AdminVenuesPage />} />
          <Route path="matches" element={<AdminMatchesPage />} />
          <Route path="scoring" element={<AdminScoringPage />} />
          <Route path="points-table" element={<AdminPointsTablePage />} />
          <Route path="stats" element={<AdminStatsPage />} />
          <Route
            path="users"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminUsersPage />
              </ProtectedRoute>
            }
          />
          <Route path="reports" element={<AdminReportsPage />} />
        </Route>

        {/* Catch-all 404 Not Found */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
