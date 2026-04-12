import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    {
      section: 'doctor',
      label: '\u8bca\u7597\u5de5\u4f5c\u53f0',
      description: '\u6162\u75c5\u8f85\u52a9\u8bca\u7597\u3001\u98ce\u9669\u8bc6\u522b\u4e0e\u5904\u7f6e\u5efa\u8bae',
    },
    {
      section: 'archive',
      label: '\u60a3\u8005\u6863\u6848',
      description: '\u60a3\u8005\u6863\u6848\u7ef4\u62a4\u4e0e\u4e8b\u4ef6\u8865\u5f55',
    },
    {
      section: 'governance',
      label: '\u6cbb\u7406\u770b\u677f',
      description: '\u7cfb\u7edf\u72b6\u6001\u4e0e\u6570\u636e\u6cbb\u7406\u603b\u89c8',
    },
    {
      section: 'insights',
      label: '\u6a21\u578b\u6d1e\u5bdf',
      description: '\u6a21\u578b\u8868\u73b0\u3001\u9884\u6d4b\u4f9d\u636e\u4e0e\u8d8b\u52bf\u89c2\u5bdf',
    },
  ],
  nurse: [
    {
      section: 'tasks',
      label: '\u968f\u8bbf\u4efb\u52a1',
      description: '\u5f85\u529e\u968f\u8bbf\u4efb\u52a1\u4e0e\u6267\u884c\u60c5\u51b5',
    },
    {
      section: 'contacts',
      label: '\u60a3\u8005\u8054\u7cfb\u8bb0\u5f55',
      description: '\u7535\u8bdd/\u5fae\u4fe1/\u5bb6\u5c5e\u8054\u7cfb\u8bb0\u5f55\u7ba1\u7406',
    },
    {
      section: 'flow',
      label: '\u6d41\u8f6c\u770b\u677f',
      description: '\u60a3\u8005\u6d41\u8f6c\u72b6\u6001\u4e0e\u4e0b\u4e00\u6b65\u52a8\u4f5c',
    },
  ],
  archivist: [
    {
      section: 'archive',
      label: '\u6863\u6848\u7ba1\u7406',
      description: '\u6863\u6848\u5efa\u6863\u3001\u66f4\u65b0\u4e0e\u8d28\u91cf\u7ef4\u62a4',
    },
    {
      section: 'data-quality',
      label: '\u6570\u636e\u5b8c\u6574\u6027',
      description: '\u7ed3\u6784\u5316\u5b57\u6bb5\u4e0e\u5173\u952e\u4fe1\u606f\u5b8c\u6574\u6027\u68c0\u67e5',
    },
    {
      section: 'governance',
      label: '\u6cbb\u7406\u6a21\u5757',
      description: '\u6cbb\u7406\u6a21\u5757\u4e0e\u6570\u636e\u7ef4\u62a4\u72b6\u6001',
    },
  ],
}

export const SECTION_LABELS: Record<AppSection, string> = {
  doctor: '\u8bca\u7597\u5de5\u4f5c\u53f0',
  archive: '\u60a3\u8005\u6863\u6848',
  tasks: '\u968f\u8bbf\u4efb\u52a1',
  governance: '\u6cbb\u7406\u770b\u677f',
  insights: '\u6a21\u578b\u6d1e\u5bdf',
  contacts: '\u60a3\u8005\u8054\u7cfb\u8bb0\u5f55',
  flow: '\u6d41\u8f6c\u770b\u677f',
  'data-quality': '\u6570\u636e\u5b8c\u6574\u6027',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}
