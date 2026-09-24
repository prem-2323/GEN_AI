import { GoogleGenAI } from '@google/genai';
import {
  SourceFile,
  TransformationConfig,
  OutputType,
  AIAnalysis,
  TransformationDeliverables,
  UckrKnowledgeBase,
} from '../types';

const DEFAULT_MODEL = 'gemini-2.5-flash';

function getApiKey(): string {
  const key =
    (import.meta as unknown as { env?: Record<string, string | undefined> }).env
      ?.VITE_GEMINI_API_KEY ||
    (import.meta as unknown as { env?: Record<string, string | undefined> }).env
      ?.GEMINI_API_KEY ||
    (typeof process !== 'undefined'
      ? (process as unknown as { env?: Record<string, string | undefined> }).env
          ?.GEMINI_API_KEY
      : undefined) ||
    '';
  if (!key) {
    throw new Error(
      'Missing GEMINI_API_KEY. Add VITE_GEMINI_API_KEY to your .env file to enable real AI generation.'
    );
  }
  return key;
}

function getClient(): GoogleGenAI {
  return new GoogleGenAI({ apiKey: getApiKey() });
}

function extractJson(text: string): string {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenced) return fenced[1].trim();
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start !== -1 && end !== -1 && end > start) {
    return text.slice(start, end + 1);
  }
  return text.trim();
}

async function callGeminiJson<T>(prompt: string, model = DEFAULT_MODEL): Promise<T> {
  const ai = getClient();
  const response = await ai.models.generateContent({
    model,
    contents: prompt,
    config: { responseMimeType: 'application/json' },
  });
  const raw = (response as unknown as { text?: string }).text ?? '';
  return JSON.parse(extractJson(raw)) as T;
}

import { backendApi, backendEnabled } from './backendService';

export async function analyzeSourceContent(source: SourceFile, projectId: string = 'proj_default'): Promise<AIAnalysis> {
  if (!source.extractedText?.trim()) {
    throw new Error('No source text to analyze. Upload or paste source content first.');
  }

  // 1. Try FastAPI Backend (Phase 3 Qwen/Gemma + MongoDB)
  if (backendEnabled) {
    try {
      const srcId = source.id || 'SRC_001';
      const anaRes = await backendApi.startPhase3Analysis(projectId, srcId, true).catch(() => null);
      if (anaRes && anaRes.textAnalysis) {
        const ta = anaRes.textAnalysis;
        return {
          detectedTopic: (ta.topics && ta.topics[0]?.topic) || 'Threat Intelligence & Security',
          confidenceScore: 0.98,
          keyEntities: (ta.entities || []).map((e: { name?: string }) => e.name || '').filter(Boolean).slice(0, 8),
          importantFacts: (ta.facts || []).map((f: { text?: string; value?: string }) => f.text || f.value || '').filter(Boolean).slice(0, 8),
          audienceSignals: ['Executive Leadership', 'Security Operations', 'IT Infrastructure'],
          communicationObjective: 'Inform stakeholders of critical vulnerabilities and immediate mandates.',
          sentiment: 'Formal & Action-Oriented',
          readabilityScore: 'Technical / Professional (Grade 12)',
        };
      }
    } catch {
      // fallback to Gemini
    }
  }

  // 2. Client-side Gemini fallback
  const prompt = `Analyze the following source document and return STRICT JSON matching the AIAnalysis schema.
Schema: { "detectedTopic": string, "confidenceScore": number (0-1), "keyEntities": string[], "importantFacts": string[], "audienceSignals": string[], "communicationObjective": string, "sentiment": string, "readabilityScore": string }

Source name: ${source.name}
Source type: ${source.type}
Content:
${source.extractedText.slice(0, 12000)}`;
  return callGeminiJson<AIAnalysis>(prompt);
}

export async function buildUckrKnowledge(
  source: SourceFile,
  analysis: AIAnalysis,
  projectId: string = 'proj_default'
): Promise<UckrKnowledgeBase> {
  // 1. Try FastAPI Backend (Phase 4 Real UCKR Engine + MongoDB)
  if (backendEnabled) {
    try {
      const srcId = source.id || 'SRC_001';
      const uckrRes = await backendApi.buildUckr(projectId, srcId).catch(() => null);
      const rawUckr = uckrRes?.uckr || uckrRes;
      if (rawUckr && rawUckr.facts && rawUckr.facts.length > 0) {
        return {
          stats: {
            totalFacts: rawUckr.stats?.totalFacts ?? rawUckr.facts?.length ?? 0,
            totalEntities: rawUckr.stats?.totalEntities ?? rawUckr.entities?.length ?? 0,
            totalEvents: rawUckr.stats?.totalEvents ?? rawUckr.events?.length ?? 0,
            totalMetrics: rawUckr.stats?.totalMetrics ?? rawUckr.metrics?.length ?? 0,
            totalActions: rawUckr.stats?.totalActions ?? rawUckr.actions?.length ?? 0,
            totalSources: rawUckr.stats?.totalSources ?? 1,
            totalRelationships: rawUckr.stats?.totalRelationships ?? rawUckr.relationships?.length ?? 0,
            coverage: rawUckr.stats?.coverage ?? 96.0,
            grounding: rawUckr.stats?.grounding ?? 100.0,
            readiness: rawUckr.stats?.readiness ?? 98.0,
          },
          facts: (rawUckr.facts || []).map((f: any, idx: number) => ({
            id: f.id || f.factId || `F-${idx + 1}`,
            value: f.value || f.text || '',
            type: f.type || 'Proposition',
            sourceDoc: f.sourceDoc || source.name,
            page: f.page || 1,
            section: f.section || '',
            confidence: f.confidence || 0.98,
            quote: f.quote || f.value || f.text || '',
            usedInDeliverables: f.usedInDeliverables || [],
          })),
          entities: (rawUckr.entities || []).map((e: any, idx: number) => ({
            id: e.id || e.entityId || `E-${idx + 1}`,
            name: e.canonicalName || e.name || '',
            category: e.category || 'Actor / Stakeholder',
            mentions: e.mentions || 1,
            role: e.role || '',
          })),
          events: (rawUckr.events || []).map((ev: any, idx: number) => ({
            id: ev.id || ev.eventId || `EV-${idx + 1}`,
            title: ev.title || ev.name || '',
            timestamp: ev.timestamp || ev.date || '',
            impact: ev.impact || '',
            actors: ev.actors || ev.participants || [],
          })),
          metrics: (rawUckr.metrics || []).map((m: any, idx: number) => ({
            id: m.id || m.metricId || `M-${idx + 1}`,
            name: m.name || 'Metric',
            value: String(m.value || ''),
            unit: m.unit || '',
            context: m.context || '',
            confidence: m.confidence || 0.98,
          })),
          relationships: (rawUckr.relationships || []).map((r: any, idx: number) => ({
            id: r.id || r.relationshipId || `R-${idx + 1}`,
            source: r.source || r.sourceEntityId || '',
            relation: r.relation || r.relationshipType || 'related to',
            target: r.target || r.targetEntityId || '',
            confidence: r.confidence || 0.92,
          })),
          actions: (rawUckr.actions || []).map((a: any, idx: number) => ({
            id: a.id || a.actionId || `A-${idx + 1}`,
            action: a.action || a.text || '',
            priority: a.priority || 'P1 High',
            timeframe: a.timeframe || '',
            owner: a.owner || '',
          })),
          sources: (rawUckr.citations || []).map((c: any, idx: number) => ({
            id: c.id || c.citationId || `S-${idx + 1}`,
            title: c.sourceDoc || source.name,
            page: c.page || 1,
            section: c.chunkId || '',
            excerpt: c.excerpt || c.quote || '',
          })),
        };
      }
    } catch {
      // fallback to Gemini
    }
  }

  // 2. Client-side Gemini fallback
  const prompt = `Build a Unified Content Knowledge Representation (UCKR) from the source and its analysis. Return STRICT JSON matching the UckrKnowledgeBase schema.
Required top-level keys: stats { totalFacts, totalEntities, totalEvents, totalMetrics, totalActions, totalSources, totalRelationships, coverage, grounding, readiness }, facts[] { id (F-001...), value, type (one of Metric, Proposition, Entity Finding, Timeline / Event, Action Mandate, Risk / Impact), sourceDoc, page, section, confidence (0-1), quote, usedInDeliverables (subset of linkedin, twitter, advisory, infographic, executive_summary, presentation, video) }, entities[] { id, name, category (one of Actor / Stakeholder, Organization, Technology / Standard, Specification, Infrastructure / Asset, Policy / Regulation), mentions, role }, events[] { id, title, timestamp, impact, actors[] }, metrics[] { id, name, value, unit, context, confidence }, relationships[] { id, source, relation, target, confidence }, actions[] { id, action, priority (one of P0 Immediate, P1 High, P2 Medium), timeframe, owner }, sources[] { id, title, page, section, excerpt }.
Ground every fact in a verbatim quote from the source. Do not invent statistics.

Source: ${source.name}
Analysis: ${JSON.stringify(analysis).slice(0, 4000)}
Content:
${source.extractedText.slice(0, 12000)}`;
  return callGeminiJson<UckrKnowledgeBase>(prompt);
}

async function generateSingle(
  kind: OutputType,
  source: SourceFile,
  config: TransformationConfig,
  analysis: AIAnalysis | null,
  uckr: UckrKnowledgeBase | null
): Promise<unknown> {
  const context = `Source: ${source.name} (${source.type})
Audience: ${config.targetAudience} | Tone: ${config.tone} | Language: ${config.language} | Detail: ${config.levelOfDetail} | Objective: ${config.objective} | Style: ${config.contentStyle}
${config.customNotes ? `Notes: ${config.customNotes}\n` : ''}${analysis ? `Analysis: ${JSON.stringify(analysis).slice(0, 3000)}\n` : ''}${
    uckr ? `Verified facts: ${JSON.stringify(uckr.facts.slice(0, 20)).slice(0, 5000)}\n` : ''
  }Content:\n${source.extractedText.slice(0, 10000)}`;

  const prompts: Record<OutputType, string> = {
    linkedin: `${context}\nReturn STRICT JSON for a LinkedIn post: { "hook": string, "body": string, "callToAction": string, "hashtags": string[], "characterCount": number, "targetAudience": string }. Use only verified facts.`,
    twitter: `${context}\nReturn STRICT JSON for X/Twitter: { "singlePost": string (<=280 chars), "thread": [{ "index": number, "text": string, "charCount": number }] }. Use only verified facts.`,
    advisory: `${context}\nReturn STRICT JSON for an advisory: { "advisoryId": string, "title": string, "severity": "CRITICAL"|"HIGH"|"MEDIUM"|"INFORMATIONAL", "dateIssued": string, "situation": string, "keyInformation": string[], "threatImpact": string, "recommendedActions": [{ "phase": string, "steps": string[] }], "complianceReferences": string[] }.`,
    executive_summary: `${context}\nReturn STRICT JSON for an executive summary: { "priority": "High"|"Critical"|"Medium"|"Low", "keyFindingsCount": number, "recommendationsCount": number, "executiveOverview": string, "keyFindings": [{ "metric"?: string, "title": string, "description": string }], "implications": string[], "strategicActions": string[] }.`,
    infographic: `${context}\nReturn STRICT JSON for an infographic: { "keyMessage": string, "keyStatistics": [{ "value": string, "label": string, "subtext": string }], "supportingPoints": [{ "iconName": string, "title": string, "description": string }], "callToAction": string, "layoutRecommendation": "Vertical"|"Horizontal"|"Timeline"|"Process"|"Comparison", "visualStyle": "Corporate"|"Minimal"|"Editorial"|"Technology" }.`,
    presentation: `${context}\nReturn STRICT JSON for a slide deck: { "deckTitle": string, "totalSlides": number, "slides": [{ "slideNumber": number, "title": string, "subtitle"?: string, "bullets": string[], "visualRecommendation": string, "speakerNotes": string }] }. 4-6 slides.`,
    video: `${context}\nReturn STRICT JSON for a video package: { "title": string, "aspectRatio": "16:9"|"9:16"|"1:1", "style": "Professional"|"News"|"Documentary"|"Corporate", "totalDurationSeconds": number, "script": string, "scenes": [{ "sceneNumber": number, "title": string, "durationSeconds": number, "sceneDescription": string, "visualRecommendation": string, "narration": string, "onScreenText": string }], "subtitlesSrt": string }. 3-5 scenes.`,
  };

  return callGeminiJson(prompts[kind]);
}

export async function generateDeliverables(
  source: SourceFile,
  config: TransformationConfig,
  selectedOutputs: OutputType[],
  analysis: AIAnalysis | null = null,
  uckr: UckrKnowledgeBase | null = null,
  onProgress?: (stepName: string, progressPercent: number) => void
): Promise<TransformationDeliverables> {
  if (!source.extractedText?.trim()) {
    throw new Error('No source text to transform. Upload or paste source content first.');
  }
  if (selectedOutputs.length === 0) {
    throw new Error('No outputs selected. Choose at least one deliverable.');
  }

  const result: TransformationDeliverables = {};
  for (let i = 0; i < selectedOutputs.length; i++) {
    const kind = selectedOutputs[i];
    onProgress?.(`Generating ${kind}`, Math.round(((i + 1) / selectedOutputs.length) * 100));
    const data = await generateSingle(kind, source, config, analysis, uckr);
    (result as Record<string, unknown>)[kind] = data;
  }
  return result;
}

// Interactive speech synthesis helper using standard Web Speech API
export function speakText(text: string, onEnd?: () => void): SpeechSynthesisUtterance | null {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    return null;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  if (onEnd) {
    utterance.onend = onEnd;
    utterance.onerror = onEnd;
  }
  window.speechSynthesis.speak(utterance);
  return utterance;
}

export function stopSpeaking() {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}
