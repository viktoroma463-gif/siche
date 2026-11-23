import { useEffect, useState } from "react";
import Splash from "./components/Splash";
import Workspace from "./pages/Workspace";
import { api, cacheSession, clearCachedSession, readCachedSession } from "./api";
import type { Session } from "./types";

async function loadSession(): Promise<Session> {
  const cached = readCachedSession();
  if (cached?.id) {
    try {
      const session = await api.get(cached.id);
      if (session.modules && session.plan) {
        cacheSession(session);
        return session;
      }
    } catch {
      /* fall through to a fresh session */
    }
  }
  clearCachedSession();
  const session = await api.create();
  cacheSession(session);
  return session;
}

export default function App() {
  const [session, setSessionState] = useState<Session | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [splashDone, setSplashDone] = useState(false);

  useEffect(() => {
    let alive = true;
    loadSession()
      .then((next) => {
        if (alive) setSessionState(next);
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : "启动失败");
      });
    return () => {
      alive = false;
    };
  }, [attempt]);

  const adopt = (next: Session) => {
    setSessionState(next);
    cacheSession(next);
  };

  const retry = () => {
    setError("");
    setSessionState(null);
    setSplashDone(false);
    setAttempt((n) => n + 1);
  };

  if (!splashDone) {
    return <Splash onDone={() => setSplashDone(true)} />;
  }

  if (!session) {
    return (
      <div className="grid min-h-screen place-items-center px-6">
        {error ? (
          <div className="paper-card w-full max-w-md p-6 text-center">
            <p className="text-cinnabar">{error}</p>
            <button className="mt-4 bg-ink px-5 py-2 text-paper" onClick={retry}>
              重试
            </button>
          </div>
        ) : (
          <p className="text-sm text-ink-soft">正在准备协作区…</p>
        )}
      </div>
    );
  }

  return (
    <Workspace
      session={session}
      setSession={adopt}
      error={error}
      setError={setError}
      onNew={async () => {
        clearCachedSession();
        setSessionState(null);
        setSplashDone(false);
        setAttempt((n) => n + 1);
      }}
    />
  );
}
