export type AppSection =
  | 'doctor'
  | 'archive'
  | 'tasks'
  | 'governance'
  | 'model-dashboard'
  | 'insights'
  | 'contacts'
  | 'flow'
  | 'data-quality'

export type DoctorMode = 'list' | 'detail'

export type ArchiveMode = 'list' | 'detail' | 'create' | 'import'

export type ArchiveFocusSection = 'overview' | 'events'
