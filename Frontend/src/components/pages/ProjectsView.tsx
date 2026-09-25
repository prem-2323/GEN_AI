import React, { useState } from 'react';
import { 
  FolderKanban, 
  Search, 
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
  Database,
  Trash2,
  ArrowRight,
  X,
  Loader2
} from 'lucide-react';
import { ProjectRecord } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface ProjectsViewProps {
  projects: ProjectRecord[];
  onSelectProject: (project: ProjectRecord) => void;
  onNewTransformation: () => void;
  onDeleteProject?: (projectId: string) => void;
  onCreateProject?: (name: string, description?: string) => Promise<ProjectRecord | void>;
}

export const ProjectsView: React.FC<ProjectsViewProps> = ({
  projects,
  onSelectProject,
  onNewTransformation,
  onDeleteProject,
  onCreateProject
}) => {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const filteredProjects = projects.filter(p => {
    const title = p.title || p.name || p.projectName || '';
    const desc = p.description || '';
    const srcName = p.source?.name || '';
    const matchesSearch = title.toLowerCase().includes(search.toLowerCase()) ||
                          desc.toLowerCase().includes(search.toLowerCase()) ||
                          srcName.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === 'all' || (p.source?.type || 'TEXT').toLowerCase() === typeFilter.toLowerCase();
    return matchesSearch && matchesType;
  });

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim()) return;
    setIsCreating(true);
    try {
      if (onCreateProject) {
        const created = await onCreateProject(projectName.trim(), projectDesc.trim());
        if (created) {
          onSelectProject(created);
        }
      }
      setIsModalOpen(false);
      setProjectName('');
      setProjectDesc('');
    } catch (err) {
      console.error('Project creation failed:', err);
    } finally {
      setIsCreating(false);
    }
  };

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
            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 font-mono">
              <Database className="w-3 h-3" />
              <span>FastAPI & MongoDB Atlas</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Transformation Projects
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse and manage all previous source transformations and their active deliverable suites.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/25 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>+ New Project</span>
          </button>
          <button
            onClick={onNewTransformation}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 hover:text-white text-xs font-semibold transition-all cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>Open Studio</span>
          </button>
        </div>
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

      {/* Empty State */}
      {filteredProjects.length === 0 ? (
        <div className="p-12 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 text-center space-y-4 max-w-lg mx-auto my-6">
          <div className="w-12 h-12 rounded-2xl bg-purple-500/10 border border-purple-500/25 flex items-center justify-center text-purple-400 mx-auto">
            <FolderKanban className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-white">No projects yet</h3>
            <p className="text-xs text-slate-400">
              Create your first transformation project to start turning documents into multi-channel enterprise deliverables.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-lg shadow-purple-600/25 transition-all cursor-pointer"
            >
              + Create Project
            </button>
            <button
              onClick={onNewTransformation}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
            >
              Quick Upload
            </button>
          </div>
        </div>
      ) : (
        /* Projects Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredProjects.map((project) => {
            const pid = project.id || (project as any).projectId || '';
            const title = project.title || project.name || (project as any).projectName || 'Untitled Project';
            const srcType = project.source?.type || 'TEXT';

            return (
              <div
                key={pid}
                onClick={() => onSelectProject(project)}
                className="rounded-2xl border border-slate-800 bg-[#0d121f] p-5 hover:border-purple-500/50 hover:bg-slate-900/40 transition-all cursor-pointer group flex flex-col justify-between shadow-lg"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase font-bold bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                        {srcType}
                      </span>
                      <StatusBadge status={project.status || 'ready'} size="xs" />
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1 text-[11px]">
                        <Calendar className="w-3 h-3" /> {(project.updatedAt || project.createdAt || '').slice(0, 10)}
                      </span>
                      {onDeleteProject && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteProject(pid);
                          }}
                          className="p-1 text-slate-500 hover:text-rose-400 rounded hover:bg-slate-800 transition-colors cursor-pointer"
                          title="Delete Project"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors line-clamp-1">
                    {title}
                  </h3>

                  <p className="text-xs text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                    {project.description || 'Enterprise transformation workspace.'}
                  </p>

                  <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2">
                    <div className="text-[11px] font-semibold text-slate-400">
                      Deliverables Generated:
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {(project.selectedOutputs || ['linkedin', 'executive_summary', 'advisory']).map((out: string) => (
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
                    Source: {(project.source?.name || title).slice(0, 22)}...
                  </span>
                  <span className="text-purple-400 font-semibold group-hover:translate-x-1 transition-transform flex items-center gap-1">
                    <span>Open Studio</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0e1422] border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FolderKanban className="w-4 h-4 text-purple-400" />
                <h3 className="text-base font-bold text-white">Create New Project</h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Project Name <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Cyber Threat Intelligence 2026"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-xs text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Description / Objective
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Ingest weekly threat report and synthesize executive briefs and LinkedIn posts."
                  value={projectDesc}
                  onChange={(e) => setProjectDesc(e.target.value)}
                  className="w-full rounded-xl bg-slate-900 border border-slate-800 p-3 text-xs text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!projectName.trim() || isCreating}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-purple-600/25 cursor-pointer"
                >
                  {isCreating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>{isCreating ? 'Creating in MongoDB...' : 'Create Project'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
