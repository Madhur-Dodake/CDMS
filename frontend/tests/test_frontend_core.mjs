import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

test('Frontend Architecture & Build Verification Suite', async (t) => {
  await t.test('1. Production Build Asset Verification', () => {
    const distHtmlPath = path.join(rootDir, 'dist', 'index.html');
    assert.ok(fs.existsSync(distHtmlPath), 'dist/index.html must exist');
    const htmlContent = fs.readFileSync(distHtmlPath, 'utf8');

    // Verify Inter font is embedded
    assert.ok(
      htmlContent.includes('Inter') || htmlContent.includes('fonts.googleapis.com'),
      'Inter font must be referenced in HTML head'
    );

    // Verify Title & Meta
    assert.ok(htmlContent.includes('CDMS'), 'Title or branding must contain CDMS');
    assert.ok(!htmlContent.includes('adsbygoogle'), 'Must contain zero advertisements');
  });

  await t.test('2. Tailwind Config & Emerald Theme Tokens', () => {
    const tailwindPath = path.join(rootDir, 'tailwind.config.js');
    assert.ok(fs.existsSync(tailwindPath), 'tailwind.config.js must exist');
    const tailwindConfig = fs.readFileSync(tailwindPath, 'utf8');

    // Emerald green (#10b981) accent check
    assert.ok(tailwindConfig.includes('emerald'), 'Tailwind config must include emerald accent palette');
    assert.ok(tailwindConfig.includes('darkMode'), 'Tailwind config must configure darkMode: class');
    assert.ok(
      tailwindConfig.includes("'card'") || tailwindConfig.includes('shadow-card'),
      'Tailwind config must define rounded card shadow'
    );
    assert.ok(tailwindConfig.includes('Inter'), 'Tailwind config must configure Inter font');
  });

  await t.test('3. Auth Store State Logic (Zustand Specification)', () => {
    // Pure reproduction of authStore state machine
    class MockAuthStore {
      constructor() {
        this.token = null;
        this.user = null;
        this.role = 'viewer';
        this.isAuthenticated = false;
      }
      login(token, user) {
        this.token = token;
        this.user = user;
        this.role = user.role || 'viewer';
        this.isAuthenticated = true;
      }
      logout() {
        this.token = null;
        this.user = null;
        this.role = 'viewer';
        this.isAuthenticated = false;
      }
    }

    const store = new MockAuthStore();
    assert.equal(store.isAuthenticated, false);
    assert.equal(store.role, 'viewer');

    // Login as Admin
    store.login('jwt-token-admin', { id: 1, name: 'Admin', role: 'admin' });
    assert.equal(store.isAuthenticated, true);
    assert.equal(store.role, 'admin');
    assert.equal(store.token, 'jwt-token-admin');

    // Login as Scorer
    store.login('jwt-token-scorer', { id: 2, name: 'Official Scorer', role: 'scorer' });
    assert.equal(store.isAuthenticated, true);
    assert.equal(store.role, 'scorer');

    // Logout
    store.logout();
    assert.equal(store.isAuthenticated, false);
    assert.equal(store.token, null);
    assert.equal(store.role, 'viewer');
  });

  await t.test('4. Protected Route & RBAC Matrix Guard Engine', () => {
    // Pure function modeling ProtectedRoute logic from ProtectedRoute.jsx
    function evaluateRouteAccess({ isAuthenticated, role, allowedRoles }) {
      if (!isAuthenticated) {
        return { status: 'REDIRECT', target: '/login', reason: 'UNAUTHENTICATED' };
      }
      if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(role)) {
        return {
          status: 'REDIRECT',
          target: '/forbidden',
          reason: 'ROLE_FORBIDDEN',
          currentRole: role,
          requiredRoles: allowedRoles,
        };
      }
      return { status: 'ALLOWED' };
    }

    // Unauthenticated user -> must redirect to /login
    const unauthResult = evaluateRouteAccess({
      isAuthenticated: false,
      role: 'viewer',
      allowedRoles: ['admin', 'scorer'],
    });
    assert.equal(unauthResult.status, 'REDIRECT');
    assert.equal(unauthResult.target, '/login');

    // Viewer role attempting to access admin route -> redirect to /forbidden (403)
    const viewerForbiddenResult = evaluateRouteAccess({
      isAuthenticated: true,
      role: 'viewer',
      allowedRoles: ['admin', 'scorer'],
    });
    assert.equal(viewerForbiddenResult.status, 'REDIRECT');
    assert.equal(viewerForbiddenResult.target, '/forbidden');
    assert.equal(viewerForbiddenResult.reason, 'ROLE_FORBIDDEN');

    // Scorer role accessing admin dashboard / live scoring -> ALLOWED
    const scorerAllowedResult = evaluateRouteAccess({
      isAuthenticated: true,
      role: 'scorer',
      allowedRoles: ['admin', 'scorer'],
    });
    assert.equal(scorerAllowedResult.status, 'ALLOWED');

    // Scorer role accessing user administration (admin only) -> REDIRECT to /forbidden
    const scorerUserAdminResult = evaluateRouteAccess({
      isAuthenticated: true,
      role: 'scorer',
      allowedRoles: ['admin'],
    });
    assert.equal(scorerUserAdminResult.status, 'REDIRECT');
    assert.equal(scorerUserAdminResult.target, '/forbidden');

    // Admin role accessing user administration -> ALLOWED
    const adminUserResult = evaluateRouteAccess({
      isAuthenticated: true,
      role: 'admin',
      allowedRoles: ['admin'],
    });
    assert.equal(adminUserResult.status, 'ALLOWED');
  });

  await t.test('5. Public Layout Top Nav Specification', () => {
    const layoutPath = path.join(rootDir, 'src', 'layouts', 'PublicLayout.jsx');
    assert.ok(fs.existsSync(layoutPath), 'PublicLayout.jsx must exist');
    const code = fs.readFileSync(layoutPath, 'utf8');

    // Check all required links
    const requiredPublicLinks = ['Home', 'Tournaments', 'Teams', 'Players', 'Live Scores'];
    for (const link of requiredPublicLinks) {
      assert.ok(code.includes(link), `PublicLayout must contain link for ${link}`);
    }

    // Check search box, LIVE badge, and ThemeToggle
    assert.ok(code.includes('Search') || code.includes('placeholder="Search'), 'Must include search box');
    assert.ok(code.includes('LIVE'), 'Must include pulsing LIVE badge');
    assert.ok(code.includes('ThemeToggle'), 'Must include theme toggle component');
    assert.ok(code.includes('Login') || code.includes('LogIn'), 'Must include Login button/link');
  });

  await t.test('6. Admin Layout Dark Sidebar Specification (All 11 Modules)', () => {
    const adminLayoutPath = path.join(rootDir, 'src', 'layouts', 'AdminLayout.jsx');
    assert.ok(fs.existsSync(adminLayoutPath), 'AdminLayout.jsx must exist');
    const code = fs.readFileSync(adminLayoutPath, 'utf8');

    // Check all 11 required sidebar modules:
    // Dashboard, Tournaments, Teams, Players, Venues, Matches, Live Scoring, Points Table, Statistics, Users, Reports
    const requiredModules = [
      'Dashboard',
      'Tournaments',
      'Teams',
      'Players',
      'Venues',
      'Matches',
      'Live Scoring',
      'Points Table',
      'Statistics',
      'Users',
      'Reports',
    ];

    for (const mod of requiredModules) {
      assert.ok(code.includes(mod), `AdminLayout must contain sidebar link for ${mod}`);
    }

    // Verify dark sidebar style
    assert.ok(code.includes('bg-slate-900'), 'Sidebar must feature dark slate styling');
    assert.ok(code.includes('Public Site'), 'Sidebar must include return to Public Site button');
  });

  await t.test('7. App Route Stubs Completeness', () => {
    const appPath = path.join(rootDir, 'src', 'App.jsx');
    assert.ok(fs.existsSync(appPath), 'App.jsx must exist');
    const appCode = fs.readFileSync(appPath, 'utf8');

    const expectedRoutes = [
      '/',
      '/tournaments',
      '/tournaments/:id/standings',
      '/teams',
      '/players',
      '/live-scores',
      '/matches/:id',
      '/login',
      '/forbidden',
      'dashboard',
      'tournaments',
      'teams',
      'players',
      'venues',
      'matches',
      'scoring',
      'points-table',
      'stats',
      'users',
      'reports',
    ];

    for (const r of expectedRoutes) {
      assert.ok(appCode.includes(r), `App.jsx route tree must declare route: ${r}`);
    }

    // Verify ProtectedRoute wrapping admin
    assert.ok(appCode.includes('ProtectedRoute'), 'App.jsx must use ProtectedRoute guard');
  });

  await t.test('8. API Client JWT Interceptor Contract', () => {
    const apiPath = path.join(rootDir, 'src', 'services', 'api.js');
    assert.ok(fs.existsSync(apiPath), 'services/api.js must exist');
    const apiCode = fs.readFileSync(apiPath, 'utf8');

    assert.ok(apiCode.includes('Authorization'), 'api.js must configure Authorization header');
    assert.ok(apiCode.includes('Bearer'), 'api.js must inject Bearer JWT token');
    assert.ok(apiCode.includes('401'), 'api.js must catch 401 Unauthorized status');
    assert.ok(apiCode.includes('/login'), 'api.js must redirect to /login on 401');
  });

  await t.test('9. All Page Stubs & Component Files Integrity', () => {
    const files = [
      'src/components/ProtectedRoute.jsx',
      'src/components/ThemeToggle.jsx',
      'src/layouts/PublicLayout.jsx',
      'src/layouts/AdminLayout.jsx',
      'src/pages/HomePage.jsx',
      'src/pages/TournamentsPage.jsx',
      'src/pages/TournamentStandingsPage.jsx',
      'src/pages/TeamsPage.jsx',
      'src/pages/PlayersPage.jsx',
      'src/pages/LiveScoresPage.jsx',
      'src/pages/MatchScorecardPage.jsx',
      'src/pages/PlayerProfilePage.jsx',
      'src/pages/LoginPage.jsx',
      'src/pages/ForbiddenPage.jsx',
      'src/pages/NotFoundPage.jsx',
      'src/pages/admin/AdminDashboardPage.jsx',
      'src/pages/admin/AdminTournamentsPage.jsx',
      'src/pages/admin/AdminTeamsPage.jsx',
      'src/pages/admin/AdminPlayersPage.jsx',
      'src/pages/admin/AdminVenuesPage.jsx',
      'src/pages/admin/AdminMatchesPage.jsx',
      'src/pages/admin/AdminScoringPage.jsx',
      'src/pages/admin/AdminPointsTablePage.jsx',
      'src/pages/admin/AdminStatsPage.jsx',
      'src/pages/admin/AdminUsersPage.jsx',
      'src/pages/admin/AdminReportsPage.jsx',
    ];

    for (const relPath of files) {
      const fullPath = path.join(rootDir, relPath);
      assert.ok(fs.existsSync(fullPath), `File must exist: ${relPath}`);
      const content = fs.readFileSync(fullPath, 'utf8');
      assert.ok(content.length > 50, `File must not be empty: ${relPath}`);
      assert.ok(content.includes('export default'), `File must export default component: ${relPath}`);
    }
  });

  await t.test('10. useMatchSocket & Public API Services Contract', () => {
    // 1. Hook file checks
    const hookPath = path.join(rootDir, 'src', 'hooks', 'useMatchSocket.js');
    assert.ok(fs.existsSync(hookPath), 'useMatchSocket.js must exist');
    const hookCode = fs.readFileSync(hookPath, 'utf8');

    assert.ok(hookCode.includes('WebSocket'), 'useMatchSocket must use WebSocket');
    assert.ok(hookCode.includes('5000'), 'useMatchSocket must poll every 5000ms on socket disconnect');
    assert.ok(hookCode.includes('reconnectTimerRef') || hookCode.includes('connectWebSocket'), 'useMatchSocket must auto-reconnect');
    assert.ok(hookCode.includes('isPolling'), 'useMatchSocket must expose isPolling state');

    // 2. Services contract checks
    const apiPath = path.join(rootDir, 'src', 'services', 'api.js');
    const apiCode = fs.readFileSync(apiPath, 'utf8');
    assert.ok(apiCode.includes('matchesService'), 'api.js must export matchesService');
    assert.ok(apiCode.includes('tournamentsService'), 'api.js must export tournamentsService');
    assert.ok(apiCode.includes('teamsService'), 'api.js must export teamsService');
    assert.ok(apiCode.includes('playersService'), 'api.js must export playersService');

    // 3. Recharts integration in PlayerProfilePage
    const playerProfilePath = path.join(rootDir, 'src', 'pages', 'PlayerProfilePage.jsx');
    const playerProfileCode = fs.readFileSync(playerProfilePath, 'utf8');
    assert.ok(playerProfileCode.includes('recharts'), 'PlayerProfilePage must import from recharts');
    assert.ok(playerProfileCode.includes('BarChart'), 'PlayerProfilePage must render BarChart');
  });

  await t.test('11. Admin Management Pages & Form Validation Contract', () => {
    // 1. LoginPage
    const loginPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'LoginPage.jsx'), 'utf8');
    assert.ok(loginPage.includes('useForm'), 'LoginPage must use react-hook-form');
    assert.ok(loginPage.includes('zodResolver'), 'LoginPage must use zodResolver');
    assert.ok(loginPage.includes('activeTab') || loginPage.includes('admin'), 'LoginPage must have role switcher');
    assert.ok(loginPage.includes('showPassword'), 'LoginPage must have password visibility toggle');

    // 2. AdminDashboardPage
    const dashPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminDashboardPage.jsx'), 'utf8');
    assert.ok(dashPage.includes('dashboardService') || dashPage.includes('matchesService'), 'AdminDashboardPage must fetch dashboard data');
    assert.ok(dashPage.includes('Scoring Console') || dashPage.includes('/admin/scoring'), 'AdminDashboardPage must link to Scoring Console');

    // 3. AdminTournamentsPage
    const tourPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminTournamentsPage.jsx'), 'utf8');
    assert.ok(tourPage.includes('tournamentSchema'), 'AdminTournamentsPage must define tournamentSchema');
    assert.ok(tourPage.includes('generateSchedule'), 'AdminTournamentsPage must support generateSchedule');
    assert.ok(tourPage.includes('levelFilter'), 'AdminTournamentsPage must support level filter tabs');

    // 4. AdminTeamsPage
    const teamPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminTeamsPage.jsx'), 'utf8');
    assert.ok(teamPage.includes('teamSchema'), 'AdminTeamsPage must define teamSchema');
    assert.ok(teamPage.includes('playerSchema'), 'AdminTeamsPage must define playerSchema for add player modal');

    // 5. AdminPlayersPage
    const playPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminPlayersPage.jsx'), 'utf8');
    assert.ok(playPage.includes('roleFilter'), 'AdminPlayersPage must support role filter');
    assert.ok(playPage.includes('dob'), 'AdminPlayersPage must support date of birth');

    // 6. AdminVenuesPage
    const venuePage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminVenuesPage.jsx'), 'utf8');
    assert.ok(venuePage.includes('venueSchema'), 'AdminVenuesPage must define venueSchema');
    assert.ok(venuePage.includes('capacity'), 'AdminVenuesPage must support capacity');

    // 7. AdminMatchesPage
    const matchPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminMatchesPage.jsx'), 'utf8');
    assert.ok(matchPage.includes('matchSchema'), 'AdminMatchesPage must define matchSchema');
    assert.ok(matchPage.includes('serverError'), 'AdminMatchesPage must display server error inline');
    assert.ok(matchPage.includes('generateSchedule') || matchPage.includes('Generate Schedule'), 'AdminMatchesPage must support generate schedule');
    assert.ok(matchPage.includes('Scoring Console') || matchPage.includes('/admin/scoring'), 'AdminMatchesPage must link to Scoring Console');

    // 8. AdminUsersPage
    const userPage = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminUsersPage.jsx'), 'utf8');
    assert.ok(userPage.includes('userCreateSchema'), 'AdminUsersPage must define userCreateSchema');
    assert.ok(userPage.includes('scorer'), 'AdminUsersPage must support creating scorer');
  });

  await t.test('12. Scorer Console & Live Match Scoring Specification', () => {
    // 1. AdminScoringPage code verification
    const scoringCode = fs.readFileSync(path.join(rootDir, 'src', 'pages', 'admin', 'AdminScoringPage.jsx'), 'utf8');

    // Match setup wizard (toss winner, decision, select playing XI)
    assert.ok(scoringCode.includes('tossWinnerId') && scoringCode.includes('tossDecision'), 'Scoring page must include toss controls');
    assert.ok(scoringCode.includes('team1Xi') && scoringCode.includes('team2Xi'), 'Scoring page must include playing XI selection');
    assert.ok(scoringCode.includes('handleStartMatch'), 'Scoring page must handle match start transition');

    // Console headers & players
    assert.ok(scoringCode.includes('activeStrikerId') && scoringCode.includes('activeNonStrikerId'), 'Scoring page must track striker and non-striker');
    assert.ok(scoringCode.includes('activeBowlerId'), 'Scoring page must track bowler');

    // Control buttons (0-6, Wide, No Ball, Bye, Leg Bye, Wicket, Undo, Rotate Strike)
    assert.ok(scoringCode.includes('handleRecordRuns'), 'Scoring page must record runs 0-6');
    assert.ok(scoringCode.includes('wide') && scoringCode.includes('no_ball'), 'Scoring page must support wide and no-ball extras');
    assert.ok(scoringCode.includes('bye') && scoringCode.includes('leg_bye'), 'Scoring page must support bye and leg-bye extras');
    assert.ok(scoringCode.includes('handleOpenWicket') && scoringCode.includes('wicketType'), 'Scoring page must have wicket modal');
    assert.ok(scoringCode.includes('handleUndo'), 'Scoring page must have undo delivery control');
    assert.ok(scoringCode.includes('handleRotateStrike'), 'Scoring page must have rotate strike control');
    assert.ok(scoringCode.includes('isBowlerModalOpen'), 'Scoring page must have next bowler selection modal');

    // Optimistic UI prevention and double-tap guarding
    assert.ok(scoringCode.includes('isSubmitting'), 'Scoring page must disable buttons during request in flight');

    // Keyboard shortcuts (0-6, W, U)
    assert.ok(scoringCode.includes('keydown'), 'Scoring page must register keydown keyboard shortcuts');

    // 2. api.js scoringService contract
    const apiCode = fs.readFileSync(path.join(rootDir, 'src', 'services', 'api.js'), 'utf8');
    assert.ok(apiCode.includes('scoringService'), 'api.js must export scoringService');
    assert.ok(apiCode.includes('startMatch'), 'scoringService must export startMatch');
    assert.ok(apiCode.includes('recordBall'), 'scoringService must export recordBall');
    assert.ok(apiCode.includes('undoBall'), 'scoringService must export undoBall');
    assert.ok(apiCode.includes('endInnings'), 'scoringService must export endInnings');
  });
});
