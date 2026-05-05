import { describe, expect, it } from 'vitest'
import { allowedSectionsForRole, roleSystemForRole } from '../workspaceMenu'

describe('workspaceMenu role system routing', () => {
  it('maps each login role to its default authorized subsystem entry', () => {
    expect(roleSystemForRole('doctor').title).toBe('医护协同系统')
    expect(allowedSectionsForRole('doctor')[0]).toBe('doctor')

    expect(roleSystemForRole('nurse').title).toBe('医护协同系统')
    expect(allowedSectionsForRole('nurse')[0]).toBe('tasks')

    expect(roleSystemForRole('pharmacist').title).toBe('药房药库系统')
    expect(allowedSectionsForRole('pharmacist')[0]).toBe('pharmacy')

    expect(roleSystemForRole('archivist').title).toBe('病案管理系统')
    expect(allowedSectionsForRole('archivist')[0]).toBe('archive')

    expect(roleSystemForRole('admin').title).toBe('后台管理系统')
    expect(allowedSectionsForRole('admin')[0]).toBe('role-workspaces')
  })
})
