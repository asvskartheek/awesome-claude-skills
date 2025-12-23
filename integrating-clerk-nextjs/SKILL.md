---
name: integrating-clerk-nextjs
description: Integrates Clerk authentication into Next.js App Router applications following current best practices. Use when the user asks to "add Clerk", "integrate Clerk", "set up Clerk authentication", "add user authentication", or mentions Clerk setup in Next.js App Router projects.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Integrating Clerk with Next.js App Router

Enforces current and correct instructions for integrating Clerk into Next.js App Router applications.

## Quick Start

For a typical integration:
1. Install `@clerk/nextjs@latest`
2. Set up environment variables in `.env.local`
3. Create `middleware.ts` with `clerkMiddleware()`
4. Wrap app with `<ClerkProvider>` in `app/layout.tsx`
5. Add Clerk components (`<SignInButton>`, `<UserButton>`, etc.)

## Complete Integration Workflow

### Step 1: Install Clerk SDK

```bash
npm install @clerk/nextjs
```

### Step 2: Configure Environment Variables

**Action:** Create or update `.env.local` with Clerk API keys.

**CRITICAL:**
- NEVER write actual keys to tracked files
- ONLY use placeholder values in code examples
- Verify `.gitignore` excludes `.env*` files

```bash
# .env.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=YOUR_PUBLISHABLE_KEY
CLERK_SECRET_KEY=YOUR_SECRET_KEY
```

**Get keys from:** [Clerk Dashboard → API Keys](https://dashboard.clerk.com/last-active?path=api-keys)

### Step 3: Create Middleware

**File:** `middleware.ts` (at project root, or in `src/` if using src directory)

```typescript
// middleware.ts
import { clerkMiddleware } from "@clerk/nextjs/server";

export default clerkMiddleware();

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
```

**CRITICAL:** Use `clerkMiddleware()` from `@clerk/nextjs/server` - NOT `authMiddleware()` (deprecated).

### Step 4: Wrap App with ClerkProvider

**File:** `app/layout.tsx`

**Before editing:**
1. Read the existing `app/layout.tsx` file
2. Identify the current structure
3. Preserve existing imports and metadata

**Add these imports:**
```typescript
import {
  ClerkProvider,
  SignInButton,
  SignUpButton,
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/nextjs";
```

**Wrap the app:**
```typescript
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          <header>
            <SignedOut>
              <SignInButton />
              <SignUpButton />
            </SignedOut>
            <SignedIn>
              <UserButton />
            </SignedIn>
          </header>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
```

### Step 5: Verify Implementation

Run through this checklist before completing:

- [ ] **Middleware:** `clerkMiddleware()` used in `middleware.ts`
- [ ] **Layout:** `<ClerkProvider>` wraps app in `app/layout.tsx`
- [ ] **Imports:** References from `@clerk/nextjs` or `@clerk/nextjs/server`
- [ ] **App Router:** Using `app/` directory (not `pages/` or `_app.tsx`)
- [ ] **Environment Variables:** Only placeholders in code, actual keys in `.env.local`
- [ ] **File Security:** `.env*` in `.gitignore`

### Step 6: Test the Integration

```bash
npm run dev
```

Navigate to the app and verify:
- Sign-in/sign-up buttons appear for unauthenticated users
- User button appears for authenticated users
- Authentication flow works end-to-end

## Server-Side Authentication

When accessing authentication data in Server Components or API routes:

```typescript
import { auth } from "@clerk/nextjs/server";

export default async function Page() {
  const { userId } = await auth();

  if (!userId) {
    return <div>Not authenticated</div>;
  }

  return <div>User ID: {userId}</div>;
}
```

**CRITICAL:**
- Import `auth` from `@clerk/nextjs/server`
- Always use `await auth()` (it's async)

## Protected Routes

To protect specific routes, update `middleware.ts`:

```typescript
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/profile(.*)',
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

## CRITICAL: What NOT to Do

**NEVER do the following:**

1. ❌ Use `authMiddleware()` - it's deprecated, use `clerkMiddleware()`
2. ❌ Reference `_app.tsx` or `pages/` directory for Clerk setup
3. ❌ Import from deprecated APIs (`withAuth`, old `currentUser`)
4. ❌ Write actual API keys to tracked files
5. ❌ Use sync `auth()` - it's async, always use `await auth()`
6. ❌ Forget to wrap with `<ClerkProvider>` in layout

See [reference/outdated-patterns.md](reference/outdated-patterns.md) for detailed examples of deprecated approaches.

## Troubleshooting

**Issue:** "clerkMiddleware is not a function"
- **Cause:** Using old version of `@clerk/nextjs`
- **Fix:** Run `npm install @clerk/nextjs@latest`

**Issue:** Authentication not working
- **Check:** Is `middleware.ts` at the root (or in `src/` if using src directory)?
- **Check:** Are environment variables set correctly in `.env.local`?
- **Check:** Is the app wrapped with `<ClerkProvider>`?

**Issue:** TypeScript errors with `auth()`
- **Cause:** Not awaiting async `auth()` function
- **Fix:** Change `const { userId } = auth()` to `const { userId } = await auth()`

## Best Practices

1. **Environment Variables:** Always use `.env.local` for local development
2. **Type Safety:** Use TypeScript for better autocomplete and type checking
3. **Protected Routes:** Use `createRouteMatcher` for route-based protection
4. **Server Components:** Leverage `auth()` for server-side authentication checks
5. **Error Handling:** Wrap authentication calls in try-catch for production apps

## Additional Resources

- [Clerk Next.js Quickstart](https://clerk.com/docs/nextjs/getting-started/quickstart)
- [Clerk Dashboard - API Keys](https://dashboard.clerk.com/last-active?path=api-keys)
- [Next.js App Router Docs](https://nextjs.org/docs/app)

## Example Implementation

Here's a complete minimal example:

**middleware.ts:**
```typescript
import { clerkMiddleware } from "@clerk/nextjs/server";

export default clerkMiddleware();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

**app/layout.tsx:**
```typescript
import { ClerkProvider, SignInButton, SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          <header>
            <SignedOut>
              <SignInButton />
            </SignedOut>
            <SignedIn>
              <UserButton />
            </SignedIn>
          </header>
          <main>{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
```

**app/page.tsx:**
```typescript
import { auth } from "@clerk/nextjs/server";

export default async function Home() {
  const { userId } = await auth();

  return (
    <div>
      <h1>Welcome {userId ? "back" : "to our app"}!</h1>
    </div>
  );
}
```

**.env.local:**
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```
