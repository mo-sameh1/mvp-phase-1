import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

type RouterContextValue = {
  path: string;
  navigate: (path: string) => void;
};

const RouterContext = createContext<RouterContextValue | null>(null);

export function BrowserRouter({ children }: { children: ReactNode }) {
  const [path, setPath] = useState(() => window.location.pathname);

  useEffect(() => {
    const onPopState = () => setPath(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const value = useMemo<RouterContextValue>(
    () => ({
      path,
      navigate: (nextPath: string) => {
        window.history.pushState({}, "", nextPath);
        setPath(nextPath);
      },
    }),
    [path],
  );

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function useRouter(): RouterContextValue {
  const value = useContext(RouterContext);
  if (!value) {
    throw new Error("useRouter must be used inside BrowserRouter");
  }
  return value;
}

export function Link({
  to,
  children,
  className,
  ariaLabel,
}: {
  to: string;
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
}) {
  const { navigate } = useRouter();
  return (
    <a
      href={to}
      className={className}
      aria-label={ariaLabel}
      onClick={(event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
          return;
        }
        event.preventDefault();
        navigate(to);
      }}
    >
      {children}
    </a>
  );
}

export function matchRoute(path: string) {
  if (path === "/") {
    return { name: "home" as const };
  }

  const runMatch = path.match(/^\/systems\/([^/]+)\/run$/);
  if (runMatch) {
    return { name: "run" as const, systemId: decodeURIComponent(runMatch[1]) };
  }

  const elementDetailMatch = path.match(/^\/systems\/([^/]+)\/elements\/([^/]+)$/);
  if (elementDetailMatch) {
    return {
      name: "elementDetail" as const,
      systemId: decodeURIComponent(elementDetailMatch[1]),
      elementId: decodeURIComponent(elementDetailMatch[2]),
    };
  }

  const elementsMatch = path.match(/^\/systems\/([^/]+)\/elements$/);
  if (elementsMatch) {
    return { name: "elements" as const, systemId: decodeURIComponent(elementsMatch[1]) };
  }

  const versionsMatch = path.match(/^\/systems\/([^/]+)\/versions$/);
  if (versionsMatch) {
    return { name: "versions" as const, systemId: decodeURIComponent(versionsMatch[1]) };
  }

  return { name: "notFound" as const };
}
