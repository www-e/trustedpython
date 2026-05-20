# New Feature Development

Plan and implement a new feature using parallel execution:

## Phase 1: Planning (Parallel)
- **dev-planner**: Break down the feature into tasks
- **database-architect**: Design schema changes if needed
- **api-designer**: Design API contracts

## Phase 2: Implementation (Parallel)
- Load relevant skills automatically based on feature type
- Launch specialized agents simultaneously:
  - Database changes → database-architect
  - API endpoints → api-designer + backend-developer
  - UI components → react-specialist + ui-designer
  - Type safety → typescript-pro

## Phase 3: Review (Parallel)
- **testing-qa-expert**: Write tests for new code
- **code-quality-enforcer**: Review code standards
- **security-scanner**: Check for vulnerabilities

## Phase 4: Verification
- Run `pnpm run build:strict`
- Verify all tests pass
- Check for regressions

Always format output with visual status tracking.