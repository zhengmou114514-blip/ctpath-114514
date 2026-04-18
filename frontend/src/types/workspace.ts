export type AppSection =
  | 'doctor'
  | 'archive'
  | 'drug-management'
  | 'tasks'
  | 'governance'
  | 'model-dashboard'
  | 'insights'
  | 'contacts'
  | 'flow'
  | 'data-quality'
  | 'system'

export type DoctorMode = 'list' | 'detail'

export type ArchiveMode = 'list' | 'detail' | 'create' | 'import'

export type ArchiveFocusSection = 'overview' | 'events'
