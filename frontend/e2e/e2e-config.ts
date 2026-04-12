/**
 * Shared E2E configuration — storage state paths.
 * Imported by auth.setup.ts (setup) and test files (consumers).
 * Must NOT import from @playwright/test to avoid "setup file import" errors.
 */
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export const ownerStorageState = path.join(__dirname, '.auth/owner.json')
export const memberStorageState = path.join(__dirname, '.auth/member.json')
