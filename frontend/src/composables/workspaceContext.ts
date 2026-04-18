import { inject, provide, type InjectionKey } from 'vue'
import type { WorkspaceController } from './useWorkspaceController'

const workspaceContextKey: InjectionKey<WorkspaceController> = Symbol('workspace-context')

export function provideWorkspaceContext(workspace: WorkspaceController) {
  provide(workspaceContextKey, workspace)
}

export function useWorkspaceContext() {
  const workspace = inject(workspaceContextKey)
  if (!workspace) {
    throw new Error('Workspace context is unavailable.')
  }
  return workspace
}
