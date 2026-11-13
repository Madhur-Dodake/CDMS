import React, { useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  Calendar,
  ExternalLink,
  FileText,
  LayoutDashboard,
  LogOut,
  MapPin,
  Menu,
  PlayCircle,
  Shield,
  Table,
  Trophy,
  UserCheck,
  Users,
  X,
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';
import { useAuthStore } from '../store/authStore';

export default function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, role, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/admin/tournaments', label: 'Tournaments', icon: Trophy },
    { to: '/admin/teams', label: 'Teams', icon: Shield },
    { to: '/admin/players', label: 'Players', icon: Users },
    { to: '/admin/venues', label: 'Venues', icon: MapPin },
    { to: '/admin/matches', label: 'Matches', icon: Calendar },
    { to: '/admin/scoring', label: 'Live Scoring', icon: PlayCircle },
    { to: '/admin/points-table', label: 'Points Table', icon: Table },
    { to: '/admin/stats', label: 'Statistics', icon: BarChart3 },
    { to: '/admin/users', label: 'Users', icon: UserCheck },
    { to: '/admin/reports', label: 'Reports', icon: FileText },
  ];

  return (
    <div className="min-h-screen flex bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      {/* Sidebar Overlay for Mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Dark Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 text-slate-100 flex flex-col transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Sidebar Header */}
        <div className="h-16 px-5 border-b border-slate-800 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-white shadow shadow-emerald-500/20">
              <Trophy className="w-4 h-4" />
            </div>
            <div>
              <span className="font-extrabold text-lg tracking-tight text-white">CDMS</span>
              <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest ml-1.5 px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800">
                Admin
              </span>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Sidebar Navigation */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Management Modules
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition ${
                  isActive
                    ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-500/20'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`
              }
            >
              <item.icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>

        {/* Sidebar Footer User Info & Controls */}
        <div className="p-3 border-t border-slate-800 space-y-2 bg-slate-900/80">
          <div className="flex items-center justify-between px-2 py-1">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-emerald-400 transition"
              title="Return to Public View"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Public Site</span>
            </Link>
            <ThemeToggle className="text-slate-400 hover:text-white" />
          </div>

          <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
            <div className="min-w-0 pr-2">
              <p className="text-xs font-semibold text-white truncate">
                {user?.name || user?.email || 'Admin'}
              </p>
              <span className="text-[9px] uppercase font-bold text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-800">
                {role}
              </span>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-slate-700/60 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        {/* Top Navbar */}
        <header className="h-16 sticky top-0 z-30 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-100 capitalize">
              {location.pathname.replace('/admin/', '').replace('-', ' ') || 'Dashboard'}
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/"
              className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-emerald-500 transition px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>View Public Portal</span>
            </Link>
            <ThemeToggle />
          </div>
        </header>

        {/* Content Outlet */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

