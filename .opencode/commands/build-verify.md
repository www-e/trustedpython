# Build Verification

Run the full build verification pipeline in parallel:

```bash
pnpm run lint && pnpm run type-check && pnpm run build
```

Check for:
- ESLint errors
- TypeScript type errors
- Build success
- Any new warnings

Report results in a visual table format.