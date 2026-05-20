# Bug Fix Protocol

Systematic bug fixing with parallel investigation:

## Step 1: Reproduce & Investigate
- Identify the bug from user description or error logs
- Find relevant files using grep/glob
- Review recent commits that may have introduced the bug

## Step 2: Parallel Analysis
- **security-scanner**: Check if bug has security implications
- **perf-analyzer**: Check if bug affects performance
- **prisma-optimizer**: Check if bug involves DB queries

## Step 3: Fix & Verify
- Implement minimal fix
- Write regression test
- Run `pnpm run build:strict`
- Verify fix doesn't break existing functionality

## Output Format
```markdown
## Bug Analysis
| Aspect | Finding |
|--------|---------|
| Root Cause | ... |
| Files Affected | ... |
| Severity | ... |

## Fix Applied
- `file.ts` - Description of change

## Verification
- [x] Build passes
- [x] Tests pass
- [x] Manual verification done
```