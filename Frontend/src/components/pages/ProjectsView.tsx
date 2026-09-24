import React, { useState } from 'react';
import { 
  FolderKanban, 
  Search, 
  Filter, 
  ArrowRight, 
  FileText, 
  Layers, 
  Plus, 
  Calendar,
  Sparkles,
  Linkedin,
  Twitter,
  ShieldAlert,
  BarChart3,
  Presentation,
  Video,
  FileCheck,
  Cloud,
  Trash2
} from 'lucide-react';
import { ProjectRecord, ViewState } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface ProjectsViewProps {
  projects: ProjectRecord[];
  onSelectProject: (project: ProjectRecord) => void;
  onNewTransformation: () => void;
  onDeleteProject?: (projectId: string) => void;
}

export const ProjectsView: React.FC<ProjectsViewProps> = ({
  projects,
  onSelectProject,
  onNewTransformation,
  onDeleteProject
}) => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const filteredProjects = projects.filter(p => {
    const matchesSearch = (p.title || '').toLowerCase().includes(search.toLowerCase()) ||
                          (p.description || '').toLowerCase().includes(search.toLowerCase()) ||
                          (p.source?.name || '').toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === 'all' || p.source.type.toLowerCase() === typeFilter.toLowerCase();
    return matchesSearch && matchesType;
  });

  const getOutputIcon = (type: string) => {
    switch (type) {
      case 'linkedin': return <Linkedin className="w-3 h-3 text-blue-400" />;
      case 'twitter': return <Twitter className="w-3 h-3 text-sky-400" />;
      case 'advisory': return <ShieldAlert className="w-3 h-3 text-rose-400" />;
      case 'infographic': return <BarChart3 className="w-3 h-3 text-amber-400" />;
      case 'executive_summary': return <FileCheck className="w-3 h-3 text-emerald-400" />;
      case 'presentation': return <Presentation className="w-3 h-3 text-indigo-400" />;
      case 'video': return <Video className="w-3 h-3 text-purple-400" />;
      default: return <Sparkles className="w-3 h-3 text-purple-400" />;
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">
            <FolderKanban className="w-4 h-4" />
            <span>Project Repository</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Transformation Projects
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse and manage all previous source transformations and their active deliverable suites.
          </p>
        </div>

        <button
          onClick={onNewTransformation}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/25 transition-all cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Transformation</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search projects, sources, or deliverables..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl bg-slate-900 border border-slate-800 p-2.5 pl-9 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-purple-500"
          />
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3 pointer-events-none" />
        </div>

        {/* Source Type Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {['all', 'PDF', 'DOCX', 'TEXT', 'IMAGE', 'VIDEO'].map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                typeFilter === t
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {t === 'all' ? 'All Sources' : t}
            </button>
          ))}
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredProjects.map((project) => (
          <div
            key={project.id}
            onClick={() => onSelectProject(project)}
            className="rounded-2xl border border-slate-800 bg-[#0d121f] p-5 hover:border-purple-500/50 hover:bg-slate-900/40 transition-all cursor-pointer group flex flex-col justify-between shadow-lg"
          >
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] uppercase font-bold bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                    {project.source?.type || 'TEXT'}
                  </span>
                  <StatusBadge status={project.status || 'ready'} size="xs" />
                  {(project as any).userId && (
                    <span className="flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 font-medium">
                      <Cloud className="w-2.5 h-2.5" />
                      <span>Firestore</span>
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-[11px]">
                    <Calendar className="w-3 h-3" /> {project.updatedAt}
                  </span>
                  {onDeleteProject && (project as any).userId && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteProject(project.id);
                      }}
                      className="p-1 text-slate-500 hover:text-rose-400 rounded hover:bg-slate-800 transition-colors"
                      title="Delete from Firestore"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              <h3 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors line-clamp-1">
                {project.title}
              </h3>

              <p className="text-xs text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                {project.description}
              </p>

              <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2">
                <div className="text-[11px] font-semibold text-slate-400">
                  Deliverables Generated:
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(project.selectedOutputs || []).map((out: string) => (
                    <span
                      key={out}
                      className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300"
                    >
                      {getOutputIcon(out)}
                      <span className="capitalize">{out.replace('_', ' ')}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-5 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-mono text-[11px]">
                Source: {(project.source?.name || project.title || 'Untitled').slice(0, 22)}...
              </span>
              <span className="text-purple-400 font-semibold group-hover:translate-x-1 transition-transform flex items-center gap-1">
                <span>Open Studio</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
