"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { Component, useEffect, useRef, useState, type ReactNode } from "react";
import { frames } from "../lib/frames.mjs";

const StoryCanvas = dynamic(() => import("./story-canvas"), { ssr: false });
class CanvasBoundary extends Component<
  { children: ReactNode; onFailure: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onFailure();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

export default function PhotoStory() {
  const [selected, setSelected] = useState(frames[0].id);
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const section = useRef<HTMLElement>(null);
  const frame = frames.find((item) => item.id === selected)!;

  useEffect(() => {
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    const compact = matchMedia("(max-width: 700px)");
    const connection = (
      navigator as Navigator & { connection?: { saveData?: boolean } }
    ).connection;
    let idle = 0;
    let timer = 0;
    let cancelled = false;
    let near = false;
    let scheduled = false;
    const hero = document.getElementById(
      "hero-image",
    ) as HTMLImageElement | null;
    const start = () => {
      if (
        cancelled ||
        scheduled ||
        !near ||
        window.scrollY < 40 ||
        motion.matches ||
        compact.matches ||
        connection?.saveData ||
        (hero && !hero.complete)
      )
        return;
      scheduled = true;
      const activate = () => {
        if (!cancelled && !motion.matches && !compact.matches) setEnabled(true);
      };
      if (typeof window.requestIdleCallback === "function")
        idle = window.requestIdleCallback(activate, { timeout: 1800 });
      else timer = window.setTimeout(activate, 250);
    };
    const observer = new IntersectionObserver(
      ([entry]) => {
        near = entry.isIntersecting;
        start();
      },
      { rootMargin: "100px" },
    );
    if (section.current) observer.observe(section.current);
    const preference = () => {
      if (motion.matches || compact.matches) {
        setEnabled(false);
        setReady(false);
        scheduled = false;
      } else start();
    };
    hero?.addEventListener("load", start);
    hero?.addEventListener("error", start);
    window.addEventListener("scroll", start, { passive: true });
    motion.addEventListener("change", preference);
    compact.addEventListener("change", preference);
    return () => {
      cancelled = true;
      observer.disconnect();
      hero?.removeEventListener("load", start);
      hero?.removeEventListener("error", start);
      window.removeEventListener("scroll", start);
      motion.removeEventListener("change", preference);
      compact.removeEventListener("change", preference);
      if (idle) window.cancelIdleCallback(idle);
      clearTimeout(timer);
    };
  }, []);

  const canvasFailure = () => {
    setReady(false);
    setFailed(true);
  };
  return (
    <section
      id="experience"
      className="story wrap"
      ref={section}
      aria-label="From pose to print"
    >
      <div className="story-visual-column">
        <div className="story-visual">
          <div className="scene-disc" aria-hidden="true" />
          <span className="scene-corner top-left" aria-hidden="true" />
          <span className="scene-corner bottom-right" aria-hidden="true" />
          <div
            className={`story-poster ${ready && !failed ? "poster-hidden" : ""}`}
          >
            <Image
              key={selected}
              src={`/images/${selected}-mobile.webp`}
              alt={`${frame.title}: ${frame.count} illustrative sample photos in the actual booth layout`}
              width={683}
              height={1024}
              sizes="(max-width: 700px) 48vw, 27vw"
            />
          </div>
          {enabled && !failed && (
            <div
              className={`canvas-layer ${ready ? "canvas-ready" : ""}`}
              aria-hidden="true"
            >
              <CanvasBoundary onFailure={canvasFailure}>
                <StoryCanvas
                  selected={selected}
                  section={section}
                  onReady={() => setReady(true)}
                  onFailure={canvasFailure}
                />
              </CanvasBoundary>
            </div>
          )}
          <div className="scene-caption">
            <span>From pose to print.</span>
            <span>Made by you.</span>
          </div>
          <span className="scene-sample">
            Illustrative sample · actual frame layout
          </span>
        </div>
      </div>
      <div className="story-copy">
        <section className="story-step" aria-labelledby="experience-title">
          <h2 id="experience-title">
            Step in.
            <br />
            Be yourself.
            <br />
            <span className="accent-word">We’ll do the rest.</span>
          </h2>
          <p>
            Turn a little time together into something you can hold. Just you,
            the camera, and a few very good seconds.
          </p>
          <ol className="journey">
            <li>
              <span>01</span>
              <div>
                <h3>Make yourself at home.</h3>
                <p>
                  Pay at the booth and choose the frame that feels like you.
                </p>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <h3>Strike a pose. Then another.</h3>
                <p>
                  Follow the countdown for your full sequence of 4, 6, or 8
                  photos.
                </p>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <h3>Hello, new favourite memory.</h3>
                <p>Review your finished collage. Print it, scan it, keep it.</p>
              </div>
            </li>
          </ol>
        </section>
        <section
          id="frames"
          className="story-step frames-step"
          aria-labelledby="frames-title"
        >
          <h2 id="frames-title">
            Find your
            <br />
            <span className="accent-word">kind of frame.</span>
          </h2>
          <p>
            Six little ways to tell your story.
            <br />
            Choose one to see how your moments fit.
          </p>
          <div className="mobile-frame-preview">
            <Image
              key={selected}
              src={`/images/${selected}-mobile.webp`}
              alt={`${frame.title}: ${frame.count} illustrative sample photos in the actual booth layout`}
              width={683}
              height={1024}
              sizes="55vw"
            />
          </div>
          <fieldset className="frame-options">
            <legend className="sr-only">Choose a sample frame</legend>
            {frames.map((item) => (
              <label
                className="frame-option"
                key={item.id}
                style={{ "--frame-accent": item.color } as React.CSSProperties}
              >
                <input
                  type="radio"
                  name="frame"
                  value={item.id}
                  checked={selected === item.id}
                  onChange={() => {
                    setSelected(item.id);
                    setReady(false);
                  }}
                />
                <Image
                  src={`/images/${item.id}-thumb.webp`}
                  alt=""
                  width={160}
                  height={240}
                  sizes="48px"
                />
                <span>
                  <strong>{item.title}</strong>
                  <small>
                    {item.count} photos
                    {item.id === "four-strip-twin" ? " · matching strips" : ""}
                  </small>
                </span>
                <span className="selection-dot" aria-hidden="true" />
              </label>
            ))}
          </fieldset>
          <p className="frame-description" aria-live="polite">
            <strong>{frame.title}.</strong> {frame.description}
          </p>
          <noscript>
            <p>
              Each thumbnail shows its frame. The interactive preview needs
              JavaScript; all six layouts are available at the booth.
            </p>
          </noscript>
        </section>
        <section className="story-step keep-step" aria-labelledby="keep-title">
          <h2 id="keep-title">
            For your wall.
            <br />
            Your wallet.
            <br />
            <span className="accent-word">Your favourite person.</span>
          </h2>
          <p>
            A small reminder of a very good time. Take your print with you and
            save a digital copy, too.
          </p>
          <ul className="keepsake-list">
            <li>
              <span className="keep-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <rect x="4" y="2" width="16" height="20" rx="1" />
                  <path d="M7 5h10v11H7zM9 19h6" />
                </svg>
              </span>
              <div>
                <h3>One print, included.</h3>
                <p>A finished collage to take into the real world.</p>
              </div>
            </li>
            <li>
              <span className="keep-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M3 9V3h6m6 0h6v6m0 6v6h-6m-6 0H3v-6M8 8h3v3H8zM15 8h2m-9 7h3m4-2v4h3" />
                </svg>
              </span>
              <div>
                <h3>Scan. Save. Keep close.</h3>
                <p>
                  Download your collage by QR. No account needed. Save it within
                  seven days.
                </p>
              </div>
            </li>
            <li>
              <span className="keep-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M4 10a8 8 0 1 1 1 8M4 4v6h6" />
                </svg>
              </span>
              <div>
                <h3>One more go, if you need it.</h3>
                <p>
                  One full retake before printing. Your new sequence replaces
                  the first.
                </p>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </section>
  );
}
