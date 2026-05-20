# Seed Architect Agent

> **Purpose:** Specialized agent for maintaining the Sportology seed system — generator factories, seed files, and schema alignment.
> **Scope:** Prisma schema → seed-data-generator.ts → individual seed files → verification.

## Golden Rule

**Schema changes flow through ONE file:** `prisma/seeds/seed-data-generator.ts`. If a field is added/renamed/removed in `schema.prisma`, edit the corresponding factory function. All 20+ seed files pick it up automatically.

## Pre-Edit Checklist (RUN THESE FIRST)

```bash
# 1. Read the current schema for the model(s) you're changing
npx prisma generate                    # Ensure client is fresh
# Read prisma/schema.prisma for the relevant model

# 2. Read the current generator function
# Read prisma/seeds/seed-data-generator.ts for the relevant factory

# 3. Check if any seed files currently reference the field
rg "fieldName" prisma/seeds/           # Search seed files for the field
```

## Workflow

```
1. READ schema.prisma   → Understand model fields, types, relations, required vs optional
2. READ generator.ts    → Find the matching factory function
3. READ affected seeds  → Check if any pass overrides for this field
4. EDIT generator.ts    → Add/update/remove the field default
5. VERIFY               → tsc --noEmit + eslint on seed files
6. Done                 → No seed files need individual changes
```

## Field Change Decision Matrix

| Schema Change | Generator Action | Seed File Action |
|---------------|-----------------|-----------------|
| New optional field | Add default (faker sentence/0/false/null) | None — overrides optional |
| New required field | Add realistic default | Check callers — update overrides if test needs specific value |
| Field renamed | Rename in factory + default value | None if using spread — field name flows through |
| Field type changed | Update default value type | None unless callers pass typed overrides |
| Field removed | Remove from factory | None — spread ignores missing fields |
| Enum values changed | Update pick() array or default | Check callers that pass enum overrides |
| New index only | Nothing | Nothing |
| New optional relation | Nothing | Nothing |
| New required relation with FK | Add FK to factory (required param) | Update callers to pass the FK |

## Calling Convention Patterns

### Pattern 1: Generator has all defaults, seed passes overrides
```typescript
// Generator provides domain-appropriate defaults
generateBlogData // title, excerpt, content, coverImageUrls, dates...
// Seed overrides only what's test-specific
generateBlogData({ title: 'Specific Title', authorId: profId })
```

### Pattern 2: Generator requires FK as first param
```typescript
// FK is always required — never buried in overrides
generateLessonData(courseId, order, overrides?)
generateQuizQuestionData(quizId, order, overrides?)
generateQuizAttemptData(quizId, userId, overrides?)
generateEnrollmentData(userId, courseId, overrides?)
generateJobPostingData(employerId, overrides?)
```

### Pattern 3: Profile/relation models need FK in overrides
```typescript
// These use `as Type` cast because FK is required but comes from overrides
generateProfessorProfileData({ userId: profId, ... })
generateStudentProfileData({ userId: studentId, ... })
generateCourseData({ professorId: profId, ... })
generateEmployerProfileData({ userId: empId, ... })
```

## Post-Edit Verification (RUN THESE)

```bash
# 1. Type-check everything
npx tsc --noEmit --pretty

# 2. Lint seed files
npx eslint prisma/seeds/ 2>&1 | Select-String "seed-"

# 3. Fix any issues:
#    - Unused imports → remove
#    - `as any` → use Prisma.InputJsonValue or correct type
#    - `?.x!` → move ! before optional chain: `foo()!.x`
#    - unused vars → remove or prefix with _
```

## Anti-Patterns (NEVER Do These)

- ❌ Adding the same field default in 5 different seed files
- ❌ Using `as any` for JSON fields → use `as Prisma.InputJsonValue`
- ❌ Hardcoding UUIDs/IDs in seed files
- ❌ Spreading query results as overrides without pruning
- ❌ Importing from `@prisma/client` types that don't exist
- ❌ Editing seed files directly for new fields — **always edit the generator**
- ❌ Using `ModelCreateInput` (relation objects) → use `ModelUncheckedCreateInput` (scalar IDs)

## Adding a New Factory Function

```typescript
export function generateNewModelData(
  overrides?: Partial<Prisma.NewModelUncheckedCreateInput>
): Prisma.NewModelUncheckedCreateInput {
  return {
    // Required fields with realistic defaults
    name: faker.lorem.words(2),
    slug: faker.helpers.slugify(faker.lorem.words(2)).toLowerCase(),
    // Optional fields with null/zero defaults
    description: faker.lorem.sentence(),
    isActive: true,
    // Timestamps
    createdAt: new Date(),
    // Overrides always last
    ...overrides,
  } as Prisma.NewModelUncheckedCreateInput;
  // ^^^ Use 'as' cast only when Prisma requires fields
  // that the caller must provide via overrides (like userId)
}
```

## Available Generators (Quick Ref)

See `prisma/seeds/SEED-SYSTEM-GUIDE.md` for the complete list.

Core categories: User & Profile, Blog, Course & Learning, Quiz, Notes & Messages, Commerce, Applications, Cases & Notifications, Careers, Dynamic Plans System, System.

## Seed Files Refactored (20 files total)

seed-02, 03, 04, 05, 06, 07(categories), 12, 14, 15, 16, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29

**Skipped** (too specific / low value): 01(clear), 08-11(warehouse items), 13(categories), 17(mapping), 18(sample plans), 21(translations), 30-32(revenue/versions/submissions), external seeds

If any of the skipped files cause schema issues, the fix is the same: update the generator, not the seed file.