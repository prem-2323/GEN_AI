/**
 * Presentation theme palettes — mirrors Backend/app/services/presentation/pptx_generator.py THEME_PALETTES.
 * Used for live slide previews in the frontend and sent as `theme` on PPTX export.
 */

export interface PresentationTheme {
  id: string;
  label: string;
  colors: {
    dark_bg: string;
    title_dark: string;
    subtitle_dark: string;
    light_bg: string;
    header: string;
    accent: string;
    text_body: string;
    muted: string;
    box_bg: string;
    card_border: string;
  };
  isDarkTheme: boolean;
}

export const PRESENTATION_THEMES: PresentationTheme[] = [
  {
    id: 'spotify_emerald',
    label: 'Spotify Emerald',
    colors: {
      dark_bg: '#121212',
      title_dark: '#ffffff',
      subtitle_dark: '#b3b3b3',
      light_bg: '#181818',
      header: '#ffffff',
      accent: '#1ed760',
      text_body: '#dcdcdc',
      muted: '#8c8c8c',
      box_bg: '#202020',
      card_border: '#323232',
    },
    isDarkTheme: true,
  },
  {
    id: 'executive_navy',
    label: 'Executive Navy',
    colors: {
      dark_bg: '#0a192f',
      title_dark: '#ffffff',
      subtitle_dark: '#94a3b8',
      light_bg: '#f8fafc',
      header: '#0f172a',
      accent: '#0ea5e9',
      text_body: '#334155',
      muted: '#64748b',
      box_bg: '#ffffff',
      card_border: '#e2e8f0',
    },
    isDarkTheme: false,
  },
  {
    id: 'corporate_purple',
    label: 'Corporate Purple',
    colors: {
      dark_bg: '#1e1b4b',
      title_dark: '#ffffff',
      subtitle_dark: '#c7d2fe',
      light_bg: '#f8fafc',
      header: '#1e293b',
      accent: '#6366f1',
      text_body: '#334155',
      muted: '#64748b',
      box_bg: '#ffffff',
      card_border: '#e2e8f0',
    },
    isDarkTheme: false,
  },
  {
    id: 'crimson_minimal',
    label: 'Crimson Minimal',
    colors: {
      dark_bg: '#18181b',
      title_dark: '#ffffff',
      subtitle_dark: '#a1a1aa',
      light_bg: '#fafafa',
      header: '#18181b',
      accent: '#f43f5e',
      text_body: '#3f3f46',
      muted: '#71717a',
      box_bg: '#ffffff',
      card_border: '#e4e4e7',
    },
    isDarkTheme: false,
  },
  {
    id: 'modern_tech',
    label: 'Modern Tech',
    colors: {
      dark_bg: '#0f172a',
      title_dark: '#ffffff',
      subtitle_dark: '#94a3b8',
      light_bg: '#f8fafc',
      header: '#1e293b',
      accent: '#2563eb',
      text_body: '#334155',
      muted: '#64748b',
      box_bg: '#ffffff',
      card_border: '#e2e8f0',
    },
    isDarkTheme: false,
  },
];

export const DEFAULT_PRESENTATION_THEME = 'spotify_emerald';

export function getPresentationTheme(id?: string | null): PresentationTheme {
  return (
    PRESENTATION_THEMES.find((t) => t.id === id) ||
    PRESENTATION_THEMES.find((t) => t.id === DEFAULT_PRESENTATION_THEME)!
  );
}
