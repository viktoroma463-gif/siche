import { useCallback, useEffect, useRef } from "react";
import { gsap, useGSAP } from "../gsap";

export default function Splash({ onDone }: { onDone: () => void }) {
  const root = useRef<HTMLDivElement>(null);
  const seal = useRef<HTMLDivElement>(null);
  const fired = useRef(false);
  const doneRef = useRef(onDone);

  useEffect(() => {
    doneRef.current = onDone;
  }, [onDone]);

  const finish = useCallback(() => {
    if (fired.current) return;
    fired.current = true;
    doneRef.current();
  }, []);

  // 兜底：rAF 被节流或 GSAP 异常时，3.8 秒后也必须进入主界面
  useEffect(() => {
    const timer = window.setTimeout(finish, 3800);
    return () => window.clearTimeout(timer);
  }, [finish]);

  useGSAP(
    (_context, contextSafe) => {
      const done = contextSafe ? contextSafe(finish) : finish;
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      if (reduce) {
        const tl = gsap.timeline({ onComplete: done });
        tl.fromTo(root.current, { opacity: 0 }, { opacity: 1, duration: 0.3 })
          .to(root.current, { opacity: 0, duration: 0.4 }, "+=2.8");
        return;
      }

      const tl = gsap.timeline({ onComplete: done });
      tl.fromTo(root.current, { opacity: 0 }, { opacity: 1, duration: 0.6 }, 0)
        .fromTo(
          seal.current,
          { opacity: 0, scale: 0.9, rotation: -1.5 },
          { opacity: 1, scale: 1, rotation: 0, duration: 0.8, ease: "power3.out" },
          0.1,
        )
        .to(
          seal.current,
          { scale: 1.012, duration: 1.1, ease: "sine.inOut", yoyo: true, repeat: 1 },
          0.95,
        )
        .to(root.current, { opacity: 0, duration: 0.5, ease: "power2.in" }, 3.0);
    },
    { scope: root },
  );

  return (
    <div ref={root} className="splash-stage fixed inset-0 z-[100] grid place-items-center" aria-label="思拆">
      <div ref={seal} className="splash-seal">
        思拆
      </div>
    </div>
  );
}
