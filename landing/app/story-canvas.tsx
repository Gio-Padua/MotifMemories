'use client';

import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useRef, useState, type RefObject } from 'react';
import { BoxGeometry, Group, Mesh, MeshBasicMaterial, PlaneGeometry, SRGBColorSpace, Texture, TextureLoader } from 'three';
import { clamp, frames, storyStage } from '../lib/frames.mjs';

type Props = { selected: string; section: RefObject<HTMLElement | null>; onReady: () => void; onFailure: () => void };

function Scene({ selected, section, onReady, onFailure }: Props) {
  const { invalidate, gl } = useThree();
  const root = useRef<Group>(null);
  const portraitGroup = useRef<Group>(null);
  const frameGroup = useRef<Group>(null);
  const current = useRef(-1);
  const target = useRef(0);
  const pointer = useRef({ x: 0, y: 0 });
  const active = useRef(false);
  const announced = useRef(false);
  const callbacks = useRef({ onReady, onFailure });
  const [assets, setAssets] = useState<{ portraits: Mesh[]; print: Mesh; back: Mesh; dispose: () => void } | null>(null);
  const assetRef = useRef<typeof assets>(null);
  useEffect(() => { callbacks.current = { onReady, onFailure }; });

  useEffect(() => {
    let cancelled = false;
    let dispose: (() => void) | undefined;
    const frame = frames.find(f => f.id === selected)!;
    const size = matchMedia('(max-width: 700px)').matches ? 'mobile' : 'desktop';
    new TextureLoader().load(`/images/${selected}-${size}.webp`, texture => {
      if (cancelled) { texture.dispose(); return; }
      texture.colorSpace = SRGBColorSpace;
      texture.anisotropy = Math.min(4, gl.capabilities.getMaxAnisotropy());
      const geometry = new PlaneGeometry(1, 1);
      const box = new BoxGeometry(2.4, 3.6, 0.018);
      const textures: Texture[] = [texture];
      const portraits = frame.placements.map(([x, y, w, h, angle, capture]: number[], i: number) => {
        const crop = texture.clone();
        crop.repeat.set(w / 1200, h / 1800);
        crop.offset.set(x / 1200, 1 - (y + h) / 1800);
        crop.needsUpdate = true;
        textures.push(crop);
        const mesh = new Mesh(geometry, new MeshBasicMaterial({ map: crop, transparent: true }));
        mesh.scale.set(w / 500, h / 500, 1);
        mesh.userData = { x: (x + w / 2 - 600) / 500, y: (900 - y - h / 2) / 500, angle: angle * Math.PI / 180, capture, i };
        return mesh;
      });
      const print = new Mesh(geometry, new MeshBasicMaterial({ map: texture, transparent: true }));
      print.scale.set(2.4, 3.6, 1);
      print.position.z = 0.025;
      const back = new Mesh(box, new MeshBasicMaterial({ color: '#fffdfa', transparent: true }));
      dispose = () => { geometry.dispose(); box.dispose(); [...portraits, print, back].forEach(mesh => (mesh.material as MeshBasicMaterial).dispose()); textures.forEach(t => t.dispose()); };
      announced.current = false;
      current.current = -1;
      const loaded = { portraits, print, back, dispose };
      assetRef.current = loaded;
      setAssets(loaded);
      invalidate();
    }, undefined, () => { if (!cancelled) callbacks.current.onFailure(); });
    return () => { cancelled = true; assetRef.current = null; dispose?.(); };
  }, [selected, gl, invalidate]);

  useEffect(() => {
    const element = section.current;
    const visual = element?.querySelector('.story-visual');
    if (!element || !visual) return;
    const update = () => {
      if (!active.current || document.hidden) return;
      const rect = element.getBoundingClientRect();
      target.current = clamp(-rect.top / Math.max(1, rect.height - innerHeight));
      invalidate();
    };
    const observer = new IntersectionObserver(([entry]) => { active.current = entry.isIntersecting; update(); });
    observer.observe(visual);
    const move = (event: Event) => {
      if (!active.current || document.hidden || !matchMedia('(pointer: fine)').matches) return;
      const e = event as PointerEvent;
      const rect = visual.getBoundingClientRect();
      pointer.current = { x: ((e.clientX - rect.left) / rect.width - .5) * .14, y: ((e.clientY - rect.top) / rect.height - .5) * .08 };
      invalidate();
    };
    const leave = () => { pointer.current = { x: 0, y: 0 }; if (active.current && !document.hidden) invalidate(); };
    const lost = (event: Event) => { event.preventDefault(); callbacks.current.onFailure(); };
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    document.addEventListener('visibilitychange', update);
    visual.addEventListener('pointermove', move);
    visual.addEventListener('pointerleave', leave);
    gl.domElement.addEventListener('webglcontextlost', lost);
    return () => { observer.disconnect(); window.removeEventListener('scroll', update); window.removeEventListener('resize', update); document.removeEventListener('visibilitychange', update); visual.removeEventListener('pointermove', move); visual.removeEventListener('pointerleave', leave); gl.domElement.removeEventListener('webglcontextlost', lost); };
  }, [section, invalidate, gl]);

  useFrame(() => {
    const assets = assetRef.current;
    if (!assets || !root.current || !portraitGroup.current || !frameGroup.current || document.hidden) return;
    if (current.current < 0) current.current = target.current;
    current.current += (target.current - current.current) * .18;
    const { assemble, keep } = storyStage(current.current);
    root.current.rotation.set(pointer.current.y + keep * .08, pointer.current.x + keep * -.24, -.08 + keep * .19);
    root.current.position.y = keep * .08;
    const reveal = clamp((assemble - .76) / .24);
    (assets.print.material as MeshBasicMaterial).opacity = reveal;
    (assets.back.material as MeshBasicMaterial).opacity = reveal;
    assets.portraits.forEach(mesh => {
      const { x, y, angle, i } = mesh.userData;
      const spread = 1 - assemble;
      mesh.position.set(x + Math.sin(i * 2.7) * .75 * spread, y + Math.cos(i * 1.9) * .28 * spread, .06 + spread * (i % 3) * .16);
      mesh.rotation.z = angle + Math.sin(i * 2.1) * .22 * spread;
      (mesh.material as MeshBasicMaterial).opacity = 1 - reveal;
    });
    // Announce after this frame has actually painted, keeping the poster during initialization.
    if (!announced.current) { announced.current = true; requestAnimationFrame(() => callbacks.current.onReady()); }
    if (active.current && Math.abs(target.current - current.current) > .0005) invalidate();
  });

  return <group ref={root}>
    <group ref={portraitGroup}>{assets?.portraits.map((mesh, i) => <primitive key={`${selected}-${i}`} object={mesh}/>)}</group>
    <group ref={frameGroup}>{assets && <><primitive object={assets.back}/><primitive object={assets.print}/></>}</group>
  </group>;
}

export default function StoryCanvas(props: Props) {
  const mobile = typeof window !== 'undefined' && matchMedia('(max-width: 700px)').matches;
  return <Canvas frameloop="demand" dpr={mobile ? 1 : 1.5} orthographic camera={{ position: [0, 0, 10], zoom: mobile ? 66 : 125, near: .1, far: 30 }} gl={{ antialias: true, alpha: true, powerPreference: 'low-power' }} fallback={<span/>} onCreated={({ gl }) => { gl.setClearAlpha(0); }}><Scene {...props}/></Canvas>;
}
