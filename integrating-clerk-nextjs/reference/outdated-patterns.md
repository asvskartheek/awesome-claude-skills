# Outdated Clerk Patterns to Avoid

This document lists deprecated Clerk integration patterns that should NOT be used in Next.js App Router applications.

## Table of Contents

1. [Deprecated Middleware Patterns](#deprecated-middleware-patterns)
2. [Pages Router Patterns](#pages-router-patterns)
3. [Deprecated API Imports](#deprecated-api-imports)
4. [Environment Variable Patterns](#environment-variable-patterns)

---

## Deprecated Middleware Patterns

### ❌ Using `authMiddleware()` (DEPRECATED)

**Outdated code:**
```typescript
// middleware.ts - DO NOT USE
import { authMiddleware } from "@clerk/nextjs";

export default authMiddleware();

export const config = {
  matcher: ["/((?!.*\\..*|_next).*)", "/", "/(api|trpc)(.*)"],
};
```

**Why it's wrong:**
- `authMiddleware()` is deprecated in newer versions of `@clerk/nextjs`
- Replaced by `clerkMiddleware()` for better flexibility and performance

**✅ Correct approach:**
```typescript
// middleware.ts - USE THIS
import { clerkMiddleware } from "@clerk/nextjs/server";

export default clerkMiddleware();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
```

---

## Pages Router Patterns

### ❌ Using `_app.tsx` for Clerk Setup

**Outdated code:**
```typescript
// pages/_app.tsx - DO NOT USE FOR APP ROUTER
import { ClerkProvider } from "@clerk/nextjs";
import type { AppProps } from "next/app";

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ClerkProvider {...pageProps}>
      <Component {...pageProps} />
    </ClerkProvider>
  );
}

export default MyApp;
```

**Why it's wrong:**
- `_app.tsx` is for Pages Router, not App Router
- App Router uses `app/layout.tsx` instead

**✅ Correct approach:**
```typescript
// app/layout.tsx - USE THIS FOR APP ROUTER
import { ClerkProvider } from "@clerk/nextjs";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

### ❌ Creating Sign-In Pages Under `pages/`

**Outdated structure:**
```
pages/
├── signin.js      ❌ Wrong for App Router
├── signup.js      ❌ Wrong for App Router
└── _app.tsx       ❌ Wrong for App Router
```

**Why it's wrong:**
- Clerk handles sign-in/sign-up routes automatically
- No need to create custom pages under `pages/`
- App Router uses `app/` directory

**✅ Correct approach:**
- Use Clerk's built-in components: `<SignInButton>`, `<SignUpButton>`
- Or use Clerk's prebuilt UI pages (configured in Clerk Dashboard)

---

## Deprecated API Imports

### ❌ Using Deprecated `currentUser` Import

**Outdated code:**
```typescript
// DO NOT USE
import { currentUser } from "@clerk/nextjs";

export default async function Page() {
  const user = currentUser(); // Missing await
  return <div>{user?.firstName}</div>;
}
```

**Why it's wrong:**
- Old import path and usage pattern
- Not using async/await correctly

**✅ Correct approach:**
```typescript
// USE THIS
import { currentUser } from "@clerk/nextjs/server";

export default async function Page() {
  const user = await currentUser();
  return <div>{user?.firstName}</div>;
}
```

### ❌ Using Deprecated `withAuth` HOC

**Outdated code:**
```typescript
// DO NOT USE
import { withAuth } from "@clerk/nextjs";

function ProtectedPage() {
  return <div>Protected content</div>;
}

export default withAuth(ProtectedPage);
```

**Why it's wrong:**
- `withAuth` is a Pages Router pattern
- App Router uses Server Components with `auth()` or middleware

**✅ Correct approach:**
```typescript
// USE THIS
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

export default async function ProtectedPage() {
  const { userId } = await auth();

  if (!userId) {
    redirect("/sign-in");
  }

  return <div>Protected content</div>;
}
```

### ❌ Synchronous `auth()` Usage

**Outdated code:**
```typescript
// DO NOT USE
import { auth } from "@clerk/nextjs/server";

export default function Page() {
  const { userId } = auth(); // Missing await
  return <div>{userId}</div>;
}
```

**Why it's wrong:**
- `auth()` is now async and must be awaited
- Component must be async

**✅ Correct approach:**
```typescript
// USE THIS
import { auth } from "@clerk/nextjs/server";

export default async function Page() {
  const { userId } = await auth();
  return <div>{userId}</div>;
}
```

---

## Environment Variable Patterns

### ❌ Outdated Environment Variable Names

**Outdated code:**
```bash
# DO NOT USE these old variable names
NEXT_PUBLIC_CLERK_FRONTEND_API=clerk.example.com
CLERK_API_KEY=sk_test_...
```

**Why it's wrong:**
- Old variable naming convention
- Not supported in newer Clerk versions

**✅ Correct approach:**
```bash
# USE THESE variable names
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

---

## Client-Side API Patterns

### ❌ Using `useUser` Without Error Handling

**Outdated code:**
```typescript
// Incomplete pattern
import { useUser } from "@clerk/nextjs";

export default function UserProfile() {
  const { user } = useUser();
  return <div>{user.firstName}</div>; // May error if user is undefined
}
```

**Why it's incomplete:**
- No loading state handling
- No check for undefined user

**✅ Better approach:**
```typescript
// USE THIS
import { useUser } from "@clerk/nextjs";

export default function UserProfile() {
  const { user, isLoaded } = useUser();

  if (!isLoaded) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <div>Not signed in</div>;
  }

  return <div>{user.firstName}</div>;
}
```

---

## Consequences of Using Outdated Patterns

Using deprecated Clerk methods will cause:

1. **Application Errors**: Authentication flow may break entirely
2. **Build Failures**: Deprecated APIs may not exist in newer versions
3. **TypeScript Errors**: Type definitions have changed
4. **Security Issues**: Old patterns may not follow current security best practices
5. **Maintenance Burden**: Code will need refactoring when dependencies update

---

## Migration Checklist

If you have existing code using outdated patterns:

- [ ] Replace `authMiddleware()` with `clerkMiddleware()`
- [ ] Move Clerk setup from `_app.tsx` to `app/layout.tsx`
- [ ] Update all `auth()` calls to use `await`
- [ ] Update imports to use `@clerk/nextjs/server` where needed
- [ ] Update environment variable names
- [ ] Remove custom sign-in/sign-up pages if using Clerk's prebuilt UI
- [ ] Test authentication flow end-to-end

---

## Additional Resources

- [Clerk Migration Guide](https://clerk.com/docs/upgrade-guides/overview)
- [Next.js App Router Migration](https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration)
- [Clerk Changelog](https://clerk.com/changelog)
