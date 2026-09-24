import React, { useState } from 'react';
import { 
  Menu, 
  Sparkles, 
  FolderKanban,
  LogIn,
  LogOut,
  Cloud,
  User as UserIcon,
  ChevronDown,
  Loader2,
  UserPlus
} from 'lucide-react';
import { ViewState } from '../../types';
import { useFirebase } from '../../context/FirebaseContext';
import { StatusBadge } from '../common/StatusBadge';

interface TopBarProps {
  currentView: ViewState;
  onNavigate: (view: ViewState) => void;
  onOpenMobileSidebar: () => void;
  onOpenAuthModal?: (mode: 'signin' | 'signup') => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentView,
  onNavigate,
  onOpenMobileSidebar,
  onOpenAuthModal
}) => {
  const { user, authLoading, signOutUser } = useFirebase();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const handleSignOut = async () => {
    try {
      setIsUserMenuOpen(false);
      await signOutUser();
    } catch (err) {
      console.error('Sign out error:', err);
    }
  };

  const getBreadcrumbs = () => {
    switch (currentView) {
      case 'dashboard':
        return { section: 'Overview', page: 'Transformation Dashboard' };
      case 'new_transformation':
        return { section: 'Workspace', page: 'New Transformation Studio' };
      case 'generation_pipeline':
        return { section: 'Transformation', page: 'AI Processing Pipeline' };
      case 'results':
        return { section: 'Deliverables', page: 'Generated Deliverables' };
      case 'projects':
        return { section: 'Repository', page: 'Projects & Artifacts' };
      case 'outputs':
        return { section: 'Repository', page: 'Output Library' };
      case 'agents':
        return { section: 'Intelligence', page: 'AI Multi-Agent System' };
      case 'mcp':
        return { section: 'Integrations', page: 'Model Context Protocol (MCP)' };
      case 'settings':
        return { section: 'System', page: 'Workspace Preferences' };
      default:
        return { section: 'Platform', page: 'Workspace' };
    }
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="sticky top-0 z-30 h-16 bg-[#0b0f17]/80 backdrop-blur-md border-b border-slate-800/80 px-4 lg:px-8 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Clean Breadcrumb */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium hidden sm:inline">{breadcrumbs.section}</span>
          <span className="text-slate-600 hidden sm:inline">/</span>
          <span className="text-slate-100 font-semibold">{breadcrumbs.page}</span>
        </div>
      </div>

      <div className="flex items-center gap-2.5">
        {currentView !== 'projects' && (
          <button
            onClick={() => onNavigate('projects')}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
          >
            <FolderKanban className="w-3.5 h-3.5 text-slate-400" />
            <span>Projects</span>
          </button>
        )}

        {currentView !== 'new_transformation' && (
          <button
            onClick={() => onNavigate('new_transformation')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New Transform</span>
          </button>
        )}

        <div className="h-5 w-px bg-slate-800 mx-0.5" />

        {/* Firebase Authentication & Cloud Sync */}
        {authLoading ? (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/60 text-slate-400 text-xs">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
            <span className="hidden sm:inline">Firebase...</span>
          </div>
        ) : user ? (
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 text-xs text-white transition-all cursor-pointer"
              title={user.email || user.displayName || 'Firebase Account'}
            >
              {user.photoURL ? (
                <img
                  src={user.photoURL}
                  alt={user.displayName || 'User'}
                  className="w-5 h-5 rounded-full ring-1 ring-purple-500/50 object-cover"
                />
              ) : (
                <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-[10px] font-bold text-white">
                  {(user.displayName || user.email || 'U')[0].toUpperCase()}
                </div>
              )}
              <span className="max-w-[120px] truncate hidden md:inline font-medium">
                {user.displayName || user.email?.split('@')[0]}
              </span>
              <div className="flex items-center gap-1 text-[10px] text-amber-400 font-mono bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                <Cloud className="w-2.5 h-2.5" />
                <span className="hidden lg:inline">Firebase + DB</span>
              </div>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl py-2 z-50 text-xs">
                <div className="px-3 py-2 border-b border-slate-800">
                  <div className="font-semibold text-white truncate">{user.displayName || 'Firebase User'}</div>
                  <div className="text-[11px] text-slate-400 truncate mt-0.5">{user.email}</div>
                  <div className="mt-2 flex items-center gap-1.5">
                    <StatusBadge status="active" label="Logged In" size="xs" />
                    <span className="text-[10px] text-slate-500 font-mono">
                      {user.providerData?.[0]?.providerId === 'google.com' ? 'Google Account' : 'Email Account'}
                    </span>
                  </div>
                </div>

                <div className="p-1.5">
                  <button
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      onNavigate('projects');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors text-left"
                  >
                    <FolderKanban className="w-4 h-4 text-purple-400" />
                    <span>Cloud Projects</span>
                  </button>
                  <button
                    onClick={handleSignOut}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors text-left mt-1"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => onOpenAuthModal ? onOpenAuthModal('signin') : null}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 border border-slate-700 text-xs font-medium text-slate-200 hover:text-white shadow-sm transition-all cursor-pointer"
            >
              <LogIn className="w-3.5 h-3.5 text-purple-400" />
              <span>Sign In</span>
            </button>
            <button
              onClick={() => onOpenAuthModal ? onOpenAuthModal('signup') : null}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-xs font-medium text-purple-200 hover:text-white transition-all cursor-pointer"
            >
              <UserPlus className="w-3.5 h-3.5 text-purple-400" />
              <span>Sign Up</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
