import { useEffect, useRef, useId } from 'react';

const TOTAL_SEC = 120;
const PLAYBACK_RATE = 1.82;
const LOOP_PAUSE_MS = 900;

declare global {
  interface Window {
    gsap?: GsapVanilla;
    THREE?: any;
  }
}

type GsapVanilla = {
  timeline: (vars?: Record<string, unknown>) => GsapTimeline;
  set: (targets: unknown, vars: Record<string, unknown>) => unknown;
  to: (targets: unknown, vars: Record<string, unknown>, position?: number | string) => unknown;
  fromTo: (targets: unknown, from: Record<string, unknown>, to: Record<string, unknown>, position?: number | string) => unknown;
};

type GsapTimeline = {
  kill: () => void;
  restart: () => void;
  timeScale: (value: number) => GsapTimeline;
  add: (callback: () => void, position?: number | string) => unknown;
  call: (fn: (...args: unknown[]) => void, params?: unknown[], position?: number | string) => unknown;
  to: (targets: unknown, vars: Record<string, unknown>, position?: number | string) => unknown;
  fromTo: (targets: unknown, from: Record<string, unknown>, to: Record<string, unknown>, position?: number | string) => unknown;
  eventCallback: (type: string, fn: (...args: unknown[]) => void) => unknown;
};

function injectLink(href: string, rel: string, crossOrigin?: string) {
  if (document.querySelector(`link[href="${href}"]`)) return;
  const l = document.createElement('link');
  l.rel = rel;
  l.href = href;
  if (crossOrigin) l.crossOrigin = crossOrigin;
  document.head.appendChild(l);
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`) as HTMLScriptElement | null;
    if (existing) {
      if ((window as unknown as { gsap?: unknown }).gsap && src.includes('gsap')) {
        resolve();
        return;
      }
      if ((window as unknown as { THREE?: unknown }).THREE && src.includes('three')) {
        resolve();
        return;
      }
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error(src)), { once: true });
      return;
    }
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(src));
    document.head.appendChild(s);
  });
}

function typeOnTimeline(tl: GsapTimeline, element: HTMLElement | null, text: string, startTime: number, charDelay = 0.04) {
  if (!element) return;
  tl.call(
    () => {
      element.textContent = '';
    },
    [],
    Math.max(0, startTime - 0.02)
  );
  text.split('').forEach((char, i) => {
    tl.call(
      () => {
        element.textContent += char;
      },
      [],
      startTime + i * charDelay
    );
  });
}

function counterOnTimeline(
  tl: GsapTimeline,
  element: HTMLElement | null,
  end: number,
  startTime: number,
  duration = 2,
  formatter?: (n: number) => string
) {
  if (!element) return;
  const obj = { value: 0 };
  tl.call(() => {
    obj.value = 0;
  }, [], startTime - 0.02);
  tl.to(
    obj,
    {
      value: end,
      duration,
      ease: 'power2.out',
      onUpdate: () => {
        element.textContent = formatter ? formatter(obj.value) : Math.round(obj.value).toLocaleString();
      },
    },
    startTime
  );
}

const SCENES = [
  'TRAILER | BREACH SIGNAL',
  'TRAILER | SCALE REVEAL',
  'TRAILER | WHY IT MATTERS',
  'TRAILER | FULL TRAINING LOOP',
  'TRAILER | 10 LIVE LABS',
  'TRAILER | RED VS BLUE',
  'TRAILER | AI + INSTRUCTOR TOOLS',
  'TRAILER | READY TO LAUNCH',
];

type LabKind = 'inject' | 'xss' | 'csrf' | 'cmd' | 'auth' | 'misc' | 'storage' | 'dir' | 'xxe' | 'redirect';

const LABS: { name: string; color: string; sev: string; iconKind: LabKind }[] = [
  { name: 'SQL Injection', color: '#ef4444', sev: 'CRITICAL', iconKind: 'inject' },
  { name: 'XSS', color: '#f97316', sev: 'HIGH', iconKind: 'xss' },
  { name: 'CSRF', color: '#f59e0b', sev: 'HIGH', iconKind: 'csrf' },
  { name: 'Command Injection', color: '#dc2626', sev: 'CRITICAL', iconKind: 'cmd' },
  { name: 'Broken Auth', color: '#8b5cf6', sev: 'HIGH', iconKind: 'auth' },
  { name: 'Security Misc', color: '#06b6d4', sev: 'MEDIUM', iconKind: 'misc' },
  { name: 'Insecure Storage', color: '#10b981', sev: 'MEDIUM', iconKind: 'storage' },
  { name: 'Dir Traversal', color: '#3b82f6', sev: 'HIGH', iconKind: 'dir' },
  { name: 'XXE', color: '#ec4899', sev: 'CRITICAL', iconKind: 'xxe' },
  { name: 'Open Redirect', color: '#84cc16', sev: 'MEDIUM', iconKind: 'redirect' },
];

/** Unified lab icons (outline, same geometry language). */
function LabGlyph({ kind, color }: { kind: LabKind; color: string }) {
  const w = 18;
  const h = 18;
  const sw = 1.35;
  const common = { width: w, height: h, viewBox: '0 0 24 24', fill: 'none' as const };
  switch (kind) {
    case 'inject':
      return (
        <svg {...common}>
          <path d="M13 3 L5 14 H11 L9 21 L17 10 H11 Z" stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        </svg>
      );
    case 'xss':
      return (
        <svg {...common}>
          <path d="M8 8 L16 16 M16 8 L8 16" stroke={color} strokeWidth={sw} strokeLinecap="round" />
          <rect x={5} y={5} width={14} height={14} rx={2} stroke={color} strokeWidth={sw * 0.85} />
        </svg>
      );
    case 'csrf':
      return (
        <svg {...common}>
          <path d="M7 12 H17 M7 12 Q12 7 17 12 M7 12 Q12 17 17 12" stroke={color} strokeWidth={sw} strokeLinecap="round" fill="none" />
          <circle cx={7} cy={12} r={2} stroke={color} strokeWidth={sw * 0.85} />
          <circle cx={17} cy={12} r={2} stroke={color} strokeWidth={sw * 0.85} />
        </svg>
      );
    case 'cmd':
      return (
        <svg {...common}>
          <rect x={4} y={6} width={16} height={12} rx={2} stroke={color} strokeWidth={sw} />
          <path d="M7 10 L10 12 L7 14" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
          <path d="M12 15 H16" stroke={color} strokeWidth={sw} strokeLinecap="round" />
        </svg>
      );
    case 'auth':
      return (
        <svg {...common}>
          <path d="M12 4 L19 7 V12 Q19 17 12 20 Q5 17 5 12 V7 Z" stroke={color} strokeWidth={sw} strokeLinejoin="round" />
          <circle cx={12} cy={11} r={3} stroke={color} strokeWidth={sw * 0.85} />
        </svg>
      );
    case 'misc':
      return (
        <svg {...common}>
          <circle cx={8} cy={8} r={2} stroke={color} strokeWidth={sw} />
          <circle cx={16} cy={8} r={2} stroke={color} strokeWidth={sw} />
          <circle cx={12} cy={16} r={2} stroke={color} strokeWidth={sw} />
        </svg>
      );
    case 'storage':
      return (
        <svg {...common}>
          <ellipse cx={12} cy={7} rx={7} ry={3} stroke={color} strokeWidth={sw} />
          <path d="M5 7 V14 Q5 17 12 17 Q19 17 19 14 V7" stroke={color} strokeWidth={sw} />
        </svg>
      );
    case 'dir':
      return (
        <svg {...common}>
          <path d="M5 8 H10 L11 6 H19 V17 H5 Z" stroke={color} strokeWidth={sw} strokeLinejoin="round" />
          <path d="M9 12 H14 M14 12 L12 14 M14 12 L12 10" stroke={color} strokeWidth={sw} strokeLinecap="round" />
        </svg>
      );
    case 'xxe':
      return (
        <svg {...common}>
          <rect x={5} y={4} width={10} height={16} rx={1} stroke={color} strokeWidth={sw} />
          <path d="M15 8 H19 V19 H9 V15" stroke={color} strokeWidth={sw} strokeLinejoin="round" />
        </svg>
      );
    case 'redirect':
      return (
        <svg {...common}>
          <path d="M5 18 V8 Q5 5 8 5 H14 M11 3 L14 5 L11 7" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
          <path d="M10 14 H18 M15 11 L18 14 L15 17" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx={12} cy={12} r={6} stroke={color} strokeWidth={sw} />
        </svg>
      );
  }
}

const PROGRESS_LABELS = ['SQLi', 'XSS', 'CSRF', 'CMD', 'Auth', 'Misc', 'Storage', 'Dir', 'XXE', 'Redirect'];
const PROGRESS_VALUES = [72, 65, 58, 70, 55, 48, 62, 68, 42, 52];
const FEATURE_TAGS = [
  'Project Upload',
  'Semgrep Scanning',
  'Attack Labs',
  'Secure Fixes',
  'Docker Sandbox',
  'AI Hints',
  'Custom Quizzes',
  'Instructor Dashboard',
  'Student Progress',
  'Security Logs',
  'Red vs Blue',
  'Admin Analytics',
];
const PROOF_POINTS = [
  { label: 'Static Analysis', value: 'Semgrep + OWASP' },
  { label: 'Hands-on Modes', value: 'Attack / Fix / Tutorial' },
  { label: 'Classroom Ready', value: 'Instructor + Student views' },
  { label: 'Evidence', value: 'Logs, scores, progress' },
];
const SCAN_FINDINGS = [
  { file: 'backend/app/api/projects.py', type: 'SQL Injection', severity: 'CRITICAL', color: '#ef4444' },
  { file: 'frontend/src/pages/Scanner.tsx', type: 'XSS Sink', severity: 'HIGH', color: '#f97316' },
  { file: 'backend/requirements.txt', type: 'Dependency Risk', severity: 'MEDIUM', color: '#f59e0b' },
];
const COMMON_MISTAKES = [
  'Forgot parameterized queries',
  'Trusted redirect URL blindly',
  'Rendered user input as HTML',
];
const LEADERBOARD = [
  { name: 'Blue Falcon', score: 980, trend: '+120' },
  { name: 'Patch Runner', score: 910, trend: '+90' },
  { name: 'Red Vector', score: 860, trend: '+75' },
];

export default function TrailerPage() {
  const uid = useId().replace(/:/g, '');
  const shieldGrad2 = `shieldGrad2-${uid}`;
  const shieldGrad8 = `shieldGrad8-${uid}`;

  const rootRef = useRef<HTMLDivElement>(null);
  const threeMountRef = useRef<HTMLDivElement>(null);
  const sceneLabelRef = useRef<HTMLDivElement>(null);
  const progressFillRef = useRef<HTMLDivElement>(null);
  const progressRailRef = useRef<HTMLDivElement>(null);

  const s1Ref = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<HTMLSpanElement>(null);
  const s1Line1Ref = useRef<HTMLDivElement>(null);
  const s1Line2Ref = useRef<HTMLDivElement>(null);
  const s1Line3Ref = useRef<HTMLDivElement>(null);
  const s1GlitchRef = useRef<HTMLDivElement>(null);
  const whiteFlashRef = useRef<HTMLDivElement>(null);

  const s2Ref = useRef<HTMLDivElement>(null);
  const s2ShieldRef = useRef<SVGSVGElement>(null);
  const s2LogoRowRef = useRef<HTMLDivElement>(null);
  const s2ShimmerRef = useRef<HTMLDivElement>(null);
  const s2SubRef = useRef<HTMLDivElement>(null);
  const s2RingsRef = useRef<HTMLDivElement>(null);
  const s2LogoWrapRef = useRef<HTMLDivElement>(null);

  const s3Ref = useRef<HTMLDivElement>(null);
  const s3LeftRef = useRef<HTMLDivElement>(null);
  const s3RightRef = useRef<HTMLDivElement>(null);
  const stat1NumRef = useRef<HTMLDivElement>(null);
  const stat2NumRef = useRef<HTMLDivElement>(null);
  const stat3NumRef = useRef<HTMLDivElement>(null);
  const stat1WrapRef = useRef<HTMLDivElement>(null);
  const stat2WrapRef = useRef<HTMLDivElement>(null);
  const stat3WrapRef = useRef<HTMLDivElement>(null);
  const quoteWordsRef = useRef<HTMLDivElement>(null);
  const bridgeRef = useRef<HTMLDivElement>(null);

  const s4Ref = useRef<HTMLDivElement>(null);
  const s4TitleRef = useRef<HTMLDivElement>(null);
  const s4RowRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  const s5Ref = useRef<HTMLDivElement>(null);
  const s5GridRef = useRef<HTMLDivElement>(null);
  const s5SpotRef = useRef<HTMLDivElement>(null);
  const s5OverlayRef = useRef<HTMLDivElement>(null);
  const labCardRefs = useRef<(HTMLDivElement | null)[]>([]);

  const s6Ref = useRef<HTMLDivElement>(null);
  const s6CenterRef = useRef<HTMLDivElement>(null);
  const s6BadgeRef = useRef<HTMLDivElement>(null);
  const redTermRef = useRef<HTMLDivElement>(null);
  const blueEditorRef = useRef<HTMLDivElement>(null);
  const redBurstRef = useRef<HTMLDivElement>(null);
  const blueBurstRef = useRef<HTMLDivElement>(null);
  const redScoreRef = useRef<HTMLDivElement>(null);
  const blueScoreRef = useRef<HTMLDivElement>(null);

  const s7Ref = useRef<HTMLDivElement>(null);
  const s7BrainRef = useRef<SVGSVGElement>(null);
  const s7c1Ref = useRef<HTMLDivElement>(null);
  const s7c2Ref = useRef<HTMLDivElement>(null);
  const s7c3Ref = useRef<HTMLDivElement>(null);
  const s7c4Ref = useRef<HTMLDivElement>(null);

  const s8Ref = useRef<HTMLDivElement>(null);
  const s8ShieldRef = useRef<SVGSVGElement>(null);
  const s8RingsRef = useRef<HTMLDivElement>(null);
  const s8L1Ref = useRef<HTMLDivElement>(null);
  const s8L2Ref = useRef<HTMLDivElement>(null);
  const s8L3Ref = useRef<HTMLDivElement>(null);
  const s8PillsRef = useRef<HTMLDivElement>(null);
  const s8VignetteRef = useRef<HTMLDivElement>(null);
  const endCursorRef = useRef<HTMLSpanElement>(null);
  const endTitleRef = useRef<HTMLDivElement>(null);
  const blackFinalRef = useRef<HTMLDivElement>(null);

  const featureMarqueeRef = useRef<HTMLDivElement>(null);
  const cinemaBottomRef = useRef<HTMLDivElement>(null);

  const masterTLRef = useRef<GsapTimeline | null>(null);
  const rafRef = useRef<number>(0);
  const threeCleanupRef = useRef<(() => void) | null>(null);
  const startMsRef = useRef<number>(0);
  const phaseRef = useRef({ purple: 0, vortex: 0, camZ: 50, networkRailOpacity: 1 });

  useEffect(() => {
    injectLink(
      'https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@100;200;300;400;500&display=swap',
      'stylesheet'
    );

    let killed = false;

    Promise.all([
      loadScript('https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js'),
      loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'),
    ])
      .then(() => {
        if (killed) return;
        const gsap = window.gsap;
        const THREE = window.THREE;
        if (!gsap || !THREE || !threeMountRef.current) return;

        const mount = threeMountRef.current;
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, mount.clientWidth / Math.max(mount.clientHeight, 1), 0.1, 2000);
        camera.position.z = 50;

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(mount.clientWidth, mount.clientHeight);
        renderer.domElement.style.display = 'block';
        mount.appendChild(renderer.domElement);

        const particleCount = 3000;
        const posAttr = new Float32Array(particleCount * 3);
        const colAttr = new Float32Array(particleCount * 3);
        const pulsePhase = new Float32Array(particleCount);
        const randPick = () => Math.random();
        for (let i = 0; i < particleCount; i++) {
          posAttr[i * 3] = (Math.random() - 0.5) * 400;
          posAttr[i * 3 + 1] = (Math.random() - 0.5) * 400;
          posAttr[i * 3 + 2] = (Math.random() - 0.5) * 400;
          const r = randPick();
          let cr = 1,
            cg = 1,
            cb = 1;
          if (r > 0.7) {
            cr = 0x3b / 255;
            cg = 0x82 / 255;
            cb = 0xf6 / 255;
          } else if (r > 0.6) {
            cr = 6 / 256;
            cg = 0xb6 / 255;
            cb = 0xd4 / 255;
          }
          colAttr[i * 3] = cr;
          colAttr[i * 3 + 1] = cg;
          colAttr[i * 3 + 2] = cb;
          pulsePhase[i] = Math.random() * Math.PI * 2;
        }
        const pGeom = new THREE.BufferGeometry();
        pGeom.setAttribute('position', new THREE.BufferAttribute(posAttr, 3));
        pGeom.setAttribute('color', new THREE.BufferAttribute(colAttr, 3));
        const baseColors = new Float32Array(colAttr);
        const pMat = new THREE.PointsMaterial({
          size: 0.35,
          vertexColors: true,
          transparent: true,
          opacity: 0.85,
          depthWrite: false,
          blending: THREE.AdditiveBlending,
        });
        const particles = new THREE.Points(pGeom, pMat);
        scene.add(particles);

        const nodeMeshes: any[] = [];
        const nodePhases: number[] = [];
        const nodeGroup = new THREE.Group();
        for (let i = 0; i < 20; i++) {
          const gm = new THREE.SphereGeometry(1.2, 16, 16);
          const mat = new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.9 });
          const mesh = new THREE.Mesh(gm, mat);
          const bx = (Math.random() - 0.5) * 120;
          const by = (Math.random() - 0.5) * 120;
          const bz = (Math.random() - 0.5) * 120;
          mesh.position.set(bx, by, bz);
          Object.assign(mesh.userData, { bx, by, bz });
          nodeMeshes.push(mesh);
          nodePhases.push(Math.random() * Math.PI * 2);
          nodeGroup.add(mesh);
        }
        scene.add(nodeGroup);

        const linePts: number[] = [];
        const threshold = 42;
        for (let i = 0; i < nodeMeshes.length; i++) {
          for (let j = i + 1; j < nodeMeshes.length; j++) {
            const a = nodeMeshes[i].position;
            const b = nodeMeshes[j].position;
            if (a.distanceTo(b) < threshold) {
              linePts.push(a.x, a.y, a.z, b.x, b.y, b.z);
            }
          }
        }
        const lineGeom = new THREE.BufferGeometry();
        lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(linePts, 3));
        const lineMat = new THREE.LineBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.35 });
        const lines = new THREE.LineSegments(lineGeom, lineMat);
        scene.add(lines);

        const rainGroup = new THREE.Group();
        const rainCols = 3;
        const charsPerCol = 12;
        for (let g = 0; g < 50; g++) {
          const grp = new THREE.Group();
          const rv = (Math.random() * 0.5 + 0.5) * 0.08;
          grp.userData.speed = rv;
          grp.userData.offset = Math.random() * 200;
          grp.position.set(80 + Math.random() * 60, Math.random() * 100 - 50, -20 - Math.random() * 80);
          const pts: number[] = [];
          for (let r = 0; r < charsPerCol; r++) {
            pts.push(0, -r * rainCols, 0);
          }
          const rg = new THREE.BufferGeometry();
          rg.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
          const rm = new THREE.PointsMaterial({
            color: 0x10b981,
            size: 0.45,
            transparent: true,
            opacity: 0.2,
            depthWrite: false,
          });
          const ptsMesh = new THREE.Points(rg, rm);
          grp.add(ptsMesh);
          rainGroup.add(grp);
        }
        scene.add(rainGroup);

        const origPos = new Float32Array(posAttr);

        const onResize = () => {
          const w = mount.clientWidth;
          const h = Math.max(mount.clientHeight, 1);
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);
        };
        window.addEventListener('resize', onResize);
        startMsRef.current = performance.now();

        const tick = () => {
          if (killed) return;
          rafRef.current = requestAnimationFrame(tick);
          const elapsed = (performance.now() - startMsRef.current) / 1000;
          const t = elapsed;

          scene.rotation.y += 0.0001;

          const targetZ = 50 - (Math.min(t / TOTAL_SEC, 1) * 30);
          phaseRef.current.camZ += (targetZ - phaseRef.current.camZ) * 0.02;
          camera.position.z = phaseRef.current.camZ;

          const purpleAmt = phaseRef.current.purple;
          const colorAttr = pGeom.attributes.color as any;
          for (let i = 0; i < particleCount; i++) {
            const ix = i * 3;
            const br = baseColors[ix];
            const bg = baseColors[ix + 1];
            const bb = baseColors[ix + 2];
            const pr = 0.55,
              pg = 0.2,
              pb = 0.95;
            colorAttr.array[ix] = br + (pr - br) * purpleAmt;
            colorAttr.array[ix + 1] = bg + (pg - bg) * purpleAmt;
            colorAttr.array[ix + 2] = bb + (pb - bb) * purpleAmt;
          }
          colorAttr.needsUpdate = true;

          const positions = pGeom.attributes.position as any;
          const vtx = phaseRef.current.vortex;
          for (let i = 0; i < particleCount; i++) {
            const ix = i * 3;
            let ox = origPos[ix];
            let oy = origPos[ix + 1];
            let oz = origPos[ix + 2];
            if (vtx > 0.01) {
              const pull = vtx * 0.022;
              ox *= 1 - pull;
              oy *= 1 - pull;
              oz *= 1 - pull;
            }
            const ph = pulsePhase[i];
            const pulse = 1 + Math.sin(elapsed * 2 + ph) * 0.25 * 0.5;
            positions.array[ix] = ox * pulse;
            positions.array[ix + 1] = oy * pulse;
            positions.array[ix + 2] = oz * pulse;
          }
          positions.needsUpdate = true;

          const time = elapsed;
          nodeMeshes.forEach((mesh, i) => {
            const ph = nodePhases[i];
            const ud = mesh.userData as { bx: number; by: number; bz: number };
            const { bx, by, bz } = ud;
            mesh.position.x = bx + Math.cos(time * 0.5 + ph) * 4;
            mesh.position.y = by + Math.sin(time * 0.7 + ph) * 4;
            mesh.position.z = bz + Math.sin(time * 0.35 + ph) * 3;
          });
          const lp: number[] = [];
          for (let i = 0; i < nodeMeshes.length; i++) {
            for (let j = i + 1; j < nodeMeshes.length; j++) {
              const a = nodeMeshes[i].position;
              const b = nodeMeshes[j].position;
              if (a.distanceTo(b) < threshold) {
                lp.push(a.x, a.y, a.z, b.x, b.y, b.z);
              }
            }
          }
          lineGeom.setAttribute('position', new THREE.Float32BufferAttribute(lp, 3));

          const nrail = phaseRef.current.networkRailOpacity;
          lineMat.opacity = 0.35 * nrail;
          lines.visible = nrail > 0.02;
          nodeMeshes.forEach((m) => {
            const mat = m.material as any;
            if (mat && mat.opacity !== undefined) mat.opacity = nrail < 0.02 ? 0 : 0.14 + 0.76 * nrail;
          });
          rainGroup.children.forEach((grp: any) => {
            const g = grp;
            g.position.y -= (g.userData.speed as number) * (1 + vtx * 4);
            if (g.position.y < -120) g.position.y = 120 + (g.userData.offset as number);
          });

          renderer.render(scene, camera);
        };
        tick();

        threeCleanupRef.current = () => {
          window.removeEventListener('resize', onResize);
          cancelAnimationFrame(rafRef.current);
          lineGeom.dispose();
          lineMat.dispose();
          pGeom.dispose();
          pMat.dispose();
          nodeMeshes.forEach((m) => {
            m.geometry.dispose();
            (m.material as any).dispose();
          });
          rainGroup.traverse((obj: any) => {
            if (obj instanceof THREE.Points) {
              obj.geometry.dispose();
              (obj.material as any).dispose();
            }
          });
          renderer.dispose();
          if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
        };

        const setSceneLabel = (idx: number) => {
          const el = sceneLabelRef.current;
          if (!el) return;
          gsap.to(el, {
            opacity: 0,
            duration: 0.15,
            onComplete: () => {
              el.textContent = SCENES[idx] ?? '';
              gsap.to(el, { opacity: 1, duration: 0.3 });
            },
          });
        };

        const shieldPaths = (svg: SVGSVGElement | null) =>
          svg?.querySelectorAll('.shield-path, .shield-inner, .shield-circle') ?? [];

        const masterTL = gsap.timeline({
          onComplete: () => {
            setTimeout(() => {
              if (!killed) masterTL.restart();
            }, LOOP_PAUSE_MS);
          },
        });
        masterTL.timeScale(PLAYBACK_RATE);
        masterTLRef.current = masterTL as GsapTimeline;

        gsap.set(progressFillRef.current, { scaleX: 0, transformOrigin: 'left center' });
        masterTL.to(
          progressFillRef.current,
          { scaleX: 1, duration: TOTAL_SEC, ease: 'none' },
          0
        );

        gsap.set(
          [
            s2Ref.current,
            s3Ref.current,
            s4Ref.current,
            s5Ref.current,
            s6Ref.current,
            s7Ref.current,
            s8Ref.current,
          ],
          { opacity: 0, pointerEvents: 'none' }
        );
        gsap.set(s1Ref.current, { opacity: 1 });

        masterTL.add(() => setSceneLabel(0), 0);
        gsap.set(cursorRef.current, { opacity: 0 });
        masterTL.to(cursorRef.current, { opacity: 1, duration: 0.5 }, 0.5);
        typeOnTimeline(masterTL, s1Line1Ref.current, '> Breach simulation armed...', 0.75, 0.024);
        typeOnTimeline(masterTL, s1Line2Ref.current, '> Scanning code, routes, dependencies...', 1.85, 0.022);
        typeOnTimeline(masterTL, s1Line3Ref.current, '> 10 labs. 1 mission. Build defenders.', 2.75, 0.022);

        masterTL.to(s1GlitchRef.current, { className: '+= glitch-active' }, 4.5);
        masterTL.to(s1GlitchRef.current, { className: '-= glitch-active' }, 4.8);

        masterTL.to(whiteFlashRef.current, { opacity: 1, duration: 0.1, ease: 'power2.out' }, 5.0);
        masterTL.to(whiteFlashRef.current, { opacity: 0, duration: 0.4, ease: 'power2.in' }, 5.1);

        masterTL.to(s1Ref.current, { opacity: 0, duration: 0.6, ease: 'power2.in' }, 7.4);
        masterTL.fromTo(s2Ref.current, { opacity: 0 }, { opacity: 1, duration: 0.8, ease: 'power3.out' }, 7.2);

        masterTL.add(() => setSceneLabel(1), 8);
        const shieldEls = s2ShieldRef.current ? Array.from(shieldPaths(s2ShieldRef.current)) : [];
        shieldEls.forEach((el, idx) => {
          const node = el as SVGGeometryElement;
          let len = 300;
          try {
            len = node.getTotalLength();
          } catch {
            len = node.tagName === 'circle' ? 2 * Math.PI * 8 : 300;
          }
          node.style.strokeDasharray = `${len}`;
          node.style.strokeDashoffset = `${len}`;
          masterTL.to(node, { strokeDashoffset: 0, duration: 1.5, ease: 'power2.inOut' }, 8 + idx * 0.05);
        });

        const letters = s2LogoRowRef.current?.querySelectorAll('.scale-letter') ?? [];
        gsap.set(letters, { y: -80, opacity: 0 });
        masterTL.to(
          letters,
          { y: 0, opacity: 1, duration: 0.8, stagger: 0.08, ease: 'power4.out', willChange: 'transform' },
          9.4
        );

        gsap.set(s2SubRef.current, { opacity: 0, y: 16 });
        masterTL.to(s2SubRef.current, { opacity: 1, y: 0, duration: 1, ease: 'power3.out' }, 11);

        gsap.set(s2ShimmerRef.current, { opacity: 0, x: '-100%' });
        masterTL.to(s2ShimmerRef.current, { opacity: 0.1, duration: 0.01 }, 11.5);
        masterTL.to(s2ShimmerRef.current, { x: '100%', duration: 1.5, ease: 'power2.inOut' }, 11.5);

        const rings = s2RingsRef.current?.querySelectorAll('.exp-ring') ?? [];
        gsap.set(rings, { scale: 0.5, opacity: 1 });
        masterTL.to(
          rings,
          { scale: 3, opacity: 0, duration: 1.5, stagger: 0.3, ease: 'power2.out', transformOrigin: 'center' },
          16
        );

        masterTL.to(
          s2LogoWrapRef.current,
          { scale: 0.3, y: '-30vh', opacity: 0, duration: 2, ease: 'power2.in', transformOrigin: 'center top' },
          20
        );

        masterTL.to(s2Ref.current, { opacity: 0, duration: 0.6 }, 21.4);
        masterTL.fromTo(s3Ref.current, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 21.6);

        masterTL.add(() => setSceneLabel(2), 22);
        gsap.set([stat1WrapRef.current, stat2WrapRef.current, stat3WrapRef.current], { opacity: 0, x: -24 });
        gsap.set([s3RightRef.current], { opacity: 0, x: 24 });

        masterTL.to(stat1WrapRef.current, { opacity: 1, x: 0, duration: 0.8, ease: 'power4.out' }, 22);
        counterOnTimeline(masterTL, stat1NumRef.current, 3500000, 22, 2, (n) => {
          if (n >= 3500000) return '3.5M+';
          return (n / 1e6).toFixed(1) + 'M';
        });

        masterTL.to(stat2WrapRef.current, { opacity: 1, x: 0, duration: 0.8, ease: 'power4.out' }, 25);
        counterOnTimeline(masterTL, stat2NumRef.current, 82, 25, 2, (n) => `${Math.round(n)}%`);

        masterTL.to(stat3WrapRef.current, { opacity: 1, x: 0, duration: 0.8, ease: 'power4.out' }, 28);
        counterOnTimeline(masterTL, stat3NumRef.current, 4.9, 28, 2, (n) => {
          if (n >= 4.85) return '$4.9M';
          return '$' + n.toFixed(1) + 'M';
        });

        const words = quoteWordsRef.current?.querySelectorAll('.qw') ?? [];
        gsap.set(words, { opacity: 0, y: 10 });
        masterTL.to(words, { opacity: 1, y: 0, stagger: 0.05, duration: 0.6, ease: 'power3.out' }, 23);

        gsap.set(bridgeRef.current, { clipPath: 'inset(0 100% 0 0)' });
        masterTL.to(bridgeRef.current, { clipPath: 'inset(0 0% 0 0)', duration: 1.2, ease: 'power2.out' }, 30);

        masterTL.to(s3LeftRef.current, { x: '-100vw', duration: 1.2, ease: 'power2.in' }, 35.8);
        masterTL.to(s3RightRef.current, { x: '100vw', duration: 1.2, ease: 'power2.in' }, 35.8);
        masterTL.to(s3Ref.current, { opacity: 0, duration: 0.5 }, 36.6);

        masterTL.fromTo(s4Ref.current, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 36.4);
        masterTL.to(
          phaseRef.current,
          { networkRailOpacity: 0, duration: 0.65, ease: 'power2.out' },
          36.1
        );
        masterTL.to(featureMarqueeRef.current, { opacity: 0, duration: 0.5, ease: 'power2.out' }, 36.45);
        masterTL.to(cinemaBottomRef.current, { opacity: 0.03, duration: 0.55, ease: 'power2.out' }, 36.45);
        if (progressRailRef.current) masterTL.to(progressRailRef.current, { opacity: 0, duration: 0.45, ease: 'power2.out' }, 36.5);

        masterTL.add(() => setSceneLabel(3), 38);
        gsap.set(s4TitleRef.current, { opacity: 0, y: -20 });
        masterTL.to(s4TitleRef.current, { opacity: 1, y: 0, duration: 1, ease: 'power4.out' }, 38);
        const scannerDemo = rootRef.current?.querySelector('.scanner-demo') ?? null;
        const scanFindings = rootRef.current?.querySelectorAll('.scan-finding') ?? [];
        gsap.set(scannerDemo, { opacity: 0, y: 28, scale: 0.96 });
        gsap.set(scanFindings, { opacity: 0, x: 28 });
        masterTL.to(scannerDemo, { opacity: 1, y: 0, scale: 1, duration: 0.8, ease: 'power4.out' }, 38.7);
        masterTL.to(scanFindings, { opacity: 1, x: 0, duration: 0.45, stagger: 0.12, ease: 'power3.out' }, 39.4);

        const accentRings = [
          'rgba(59,130,246,0.55)',
          'rgba(239,68,68,0.48)',
          'rgba(16,185,129,0.48)',
          'rgba(139,92,246,0.48)',
          'rgba(6,182,212,0.48)',
        ];
        cardRefs.current.forEach((card, idx) => {
          if (!card) return;
          const start = 41 + idx * 1.65;
          masterTL.fromTo(
            card,
            { opacity: 0, y: 26, scale: 0.94 },
            { opacity: 1, y: 0, scale: 1, duration: 0.72, ease: 'power4.out', transformOrigin: 'center bottom' },
            start
          );
          masterTL.to(
            card,
            {
              boxShadow: `0 0 0 1px rgba(148,163,184,0.2), 0 0 36px ${accentRings[idx]}`,
              filter: 'brightness(1.06)',
              duration: 0.4,
              ease: 'power2.out',
            },
            start + 0.05
          );
          masterTL.to(
            card,
            {
              boxShadow: '0 12px 36px rgba(2,6,23,0.65)',
              filter: 'brightness(1)',
              duration: 0.55,
              ease: 'power2.inOut',
            },
            start + 0.42
          );
          cardRefs.current.forEach((other, j) => {
            if (!other || j === idx) return;
            if (j < idx) {
              masterTL.to(
                other,
                {
                  opacity: 0.5,
                  scale: 0.99,
                  filter: 'brightness(0.78)',
                  duration: 0.38,
                  ease: 'power2.out',
                  transformOrigin: 'center bottom',
                },
                start
              );
            }
          });
        });

        const pipeCards = cardRefs.current.filter(Boolean) as HTMLDivElement[];
        masterTL.to(
          pipeCards,
          { opacity: 1, scale: 1, filter: 'none', duration: 0.55, stagger: 0.06, ease: 'power2.out', transformOrigin: 'center bottom' },
          49.1
        );

        masterTL.to(featureMarqueeRef.current, { opacity: 1, duration: 0.52, ease: 'power2.out' }, 57.35);
        masterTL.to(cinemaBottomRef.current, { opacity: 1, duration: 0.52, ease: 'power2.out' }, 57.35);
        if (progressRailRef.current) masterTL.to(progressRailRef.current, { opacity: 1, duration: 0.4, ease: 'power2.out' }, 57.35);
        PROGRESS_VALUES.forEach((v, j) => {
          const el = typeof document !== 'undefined' ? document.querySelector(`.bar-fill-${j}`) : null;
          if (el)
            masterTL.fromTo(el, { scaleY: 0 }, { scaleY: v / 100, duration: 0.45, ease: 'power3.out', transformOrigin: 'bottom center' }, 49.5 + j * 0.08);
        });
        const proofCards = rootRef.current?.querySelectorAll('.proof-card') ?? [];
        gsap.set(proofCards, { opacity: 0, y: 18, filter: 'blur(10px)' });
        masterTL.to(proofCards, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.55, stagger: 0.08, ease: 'power3.out' }, 51.1);

        masterTL.to(s4RowRef.current, { scale: 0.985, duration: 0.85, ease: 'power2.inOut' }, 56.8);
        masterTL.to(s4Ref.current, { opacity: 0, duration: 0.6 }, 57.6);
        masterTL.fromTo(s5Ref.current, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 57.4);

        masterTL.add(() => setSceneLabel(4), 58);
        labCardRefs.current.forEach((card, i) => {
          if (!card) return;
          gsap.set(card, { scale: 0.5, opacity: 0 });
          masterTL.to(card, { scale: 1, opacity: 1, duration: 0.8, ease: 'power4.out', willChange: 'transform' }, 58 + i * 0.06);
        });

        gsap.set(s5SpotRef.current, { opacity: 0 });
        masterTL.to(s5SpotRef.current, { opacity: 1, duration: 0.4 }, 64);
        masterTL.to(s5SpotRef.current, { x: '70%', y: '70%', duration: 3, ease: 'power1.inOut' }, 64);

        const olines = s5OverlayRef.current?.querySelectorAll('.s5-line') ?? [];
        gsap.set(olines, { opacity: 0, scale: 0.82, y: 16, skewX: -4 });

        masterTL.to(
          labCardRefs.current,
          {
            opacity: 0,
            scale: 0.92,
            duration: 2.6,
            ease: 'power2.inOut',
            stagger: { each: 0.05, from: 'random' },
          },
          65.2
        );

        masterTL.to(
          olines,
          {
            opacity: 1,
            scale: 1.05,
            y: 0,
            skewX: 0,
            stagger: 0.28,
            duration: 1.15,
            ease: 'power4.out',
          },
          65.9
        );
        masterTL.to(s5Ref.current, { opacity: 0, duration: 0.5 }, 74);
        masterTL.fromTo(s6Ref.current, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 73.7);
        masterTL.to(
          phaseRef.current,
          { networkRailOpacity: 1, duration: 0.85, ease: 'power2.out' },
          73.35
        );

        masterTL.add(() => setSceneLabel(5), 74);
        gsap.set(s6CenterRef.current, { scaleY: 0 });
        masterTL.to(s6CenterRef.current, { scaleY: 1, duration: 0.8, ease: 'power4.out', transformOrigin: 'center' }, 74);

        masterTL.call(() => {
          if (redTermRef.current) redTermRef.current.textContent = '';
          if (blueEditorRef.current) blueEditorRef.current.textContent = '';
        }, [], 74);

        typeOnTimeline(masterTL, redTermRef.current, "> Payload: ' OR 1=1 --", 74.5, 0.026);
        masterTL.call(() => {
          redTermRef.current!.textContent += '\n> Testing endpoint...';
        }, [], 76);
        masterTL.call(() => {
          redTermRef.current!.textContent += '\n> ✓ EXPLOIT CONFIRMED';
        }, [], 77);

        typeOnTimeline(masterTL, blueEditorRef.current, 'cursor.execute("SELECT * FROM users WHERE name = ?", [username])', 77.5, 0.018);

        gsap.set([redBurstRef.current, blueBurstRef.current, redScoreRef.current, blueScoreRef.current], {
          opacity: 0,
          scale: 0.5,
        });
        masterTL.to(redScoreRef.current, { opacity: 1, scale: 1, duration: 0.6, ease: 'elastic.out(1, 0.6)' }, 79);
        masterTL.to(redBurstRef.current, { opacity: 1, duration: 0.01 }, 79);
        masterTL.to(redBurstRef.current, { opacity: 0, scale: 2.2, duration: 0.6, ease: 'power2.out' }, 79);

        masterTL.to(blueScoreRef.current, { opacity: 1, scale: 1, duration: 0.6, ease: 'elastic.out(1, 0.6)' }, 79.2);
        masterTL.to(blueBurstRef.current, { opacity: 1, duration: 0.01 }, 79.2);
        masterTL.to(blueBurstRef.current, { opacity: 0, scale: 2.2, duration: 0.6, ease: 'power2.out' }, 79.2);

        masterTL.to(s6CenterRef.current, { scaleX: 3, duration: 0.15, yoyo: true, repeat: 1, ease: 'power2.inOut' }, 80);
        gsap.set(s6BadgeRef.current, { opacity: 0, scale: 0.8 });
        masterTL.to(s6BadgeRef.current, { opacity: 1, scale: 1, duration: 0.5, ease: 'power4.out' }, 80);
        masterTL.to(s6BadgeRef.current, { opacity: 0.6, duration: 0.4, yoyo: true, repeat: 3 }, 80.3);

        masterTL.to(s6Ref.current, { opacity: 0, scale: 0.2, duration: 1, ease: 'power3.in' }, 85.6);
        masterTL.fromTo(s7Ref.current, { opacity: 0 }, { opacity: 1, duration: 0.8 }, 85.4);

        masterTL.add(() => setSceneLabel(6), 86);
        masterTL.to(
          phaseRef.current,
          {
            purple: 1,
            duration: 12,
            ease: 'none',
            onUpdate: () => {},
          },
          86
        );

        gsap.set([s7c1Ref.current, s7c2Ref.current, s7c3Ref.current, s7c4Ref.current], { opacity: 0, scale: 0.92 });
        const mistakeRows = rootRef.current?.querySelectorAll('.mistake-row') ?? [];
        const leaderRows = rootRef.current?.querySelectorAll('.leader-row') ?? [];
        gsap.set(mistakeRows, { opacity: 0, x: 18 });
        gsap.set(leaderRows, { opacity: 0, x: 18 });
        masterTL.to(s7c1Ref.current, { opacity: 1, scale: 1, duration: 0.8, ease: 'power4.out' }, 86);
        masterTL.to(s7c2Ref.current, { opacity: 1, scale: 1, duration: 0.8, ease: 'power4.out' }, 89);
        masterTL.to(mistakeRows, { opacity: 1, x: 0, duration: 0.35, stagger: 0.09, ease: 'power3.out' }, 89.5);
        masterTL.to(s7c3Ref.current, { opacity: 1, scale: 1, duration: 0.8, ease: 'power4.out' }, 92);
        masterTL.to(s7c4Ref.current, { opacity: 1, scale: 1, duration: 0.8, ease: 'power4.out' }, 93.5);
        masterTL.to(leaderRows, { opacity: 1, x: 0, duration: 0.35, stagger: 0.09, ease: 'power3.out' }, 94);

        const brainPulse = s7BrainRef.current?.querySelectorAll('.brain-node') ?? [];
        masterTL.to(
          brainPulse,
          { opacity: 1, stagger: 0.08, duration: 0.4, yoyo: true, repeat: 1, ease: 'power2.inOut' },
          95
        );

        masterTL.to(featureMarqueeRef.current, { opacity: 0, duration: 0.42 }, 96);
        masterTL.to(cinemaBottomRef.current, { opacity: 0.06, duration: 0.42 }, 96);
        if (progressRailRef.current) masterTL.to(progressRailRef.current, { opacity: 0, duration: 0.42, ease: 'power2.out' }, 96);
        masterTL.to(phaseRef.current, { networkRailOpacity: 0, duration: 0.55, ease: 'power2.out' }, 96.05);

        masterTL.to(s7Ref.current, { scale: 0.5, y: '-40vh', opacity: 0, duration: 1.4, ease: 'power3.in' }, 96.6);
        masterTL.fromTo(s8Ref.current, { opacity: 0, y: '40vh' }, { opacity: 1, y: 0, duration: 1.2, ease: 'power4.out' }, 96.4);

        masterTL.add(() => setSceneLabel(7), 98);
        masterTL.to(phaseRef.current, { vortex: 1, duration: 22, ease: 'power2.in' }, 98);

        const s8paths = s8ShieldRef.current ? Array.from(shieldPaths(s8ShieldRef.current)) : [];
        s8paths.forEach((el, idx) => {
          const node = el as SVGGeometryElement;
          let len = 300;
          try {
            len = node.getTotalLength();
          } catch {
            len = node.tagName === 'circle' ? 2 * Math.PI * 8 : 300;
          }
          node.style.strokeDasharray = `${len}`;
          node.style.strokeDashoffset = `${len}`;
          masterTL.to(node, { strokeDashoffset: 0, duration: 1.5, ease: 'power2.inOut' }, 98 + idx * 0.06);
        });

        const s8rings = s8RingsRef.current?.querySelectorAll('.pulse-ring') ?? [];
        gsap.set(s8rings, { scale: 1, opacity: 0.8 });
        masterTL.to(
          s8rings,
          { scale: 4, opacity: 0, duration: 1.5, stagger: 0.2, ease: 'power2.out', transformOrigin: 'center' },
          100
        );

        const l1ch = s8L1Ref.current?.querySelectorAll('.stamp-ch') ?? [];
        gsap.set(l1ch, { scale: 2, opacity: 0, filter: 'blur(20px)' });
        masterTL.to(
          l1ch,
          { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.1, stagger: 0.05, ease: 'power4.out' },
          102
        );

        const l2ch = s8L2Ref.current?.querySelectorAll('.stamp-ch') ?? [];
        gsap.set(l2ch, { scale: 2, opacity: 0, filter: 'blur(20px)' });
        masterTL.to(
          l2ch,
          { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.1, stagger: 0.05, ease: 'power4.out' },
          104
        );

        gsap.set(s8L3Ref.current, { scale: 0.5, opacity: 0, textShadow: '0 0 100px #3b82f6' });
        masterTL.to(
          s8L3Ref.current,
          { scale: 1, opacity: 1, textShadow: '0 0 20px #3b82f6', duration: 1, ease: 'elastic.out(1, 0.5)' },
          107
        );

        masterTL.call(() => {
          const el = s8L3Ref.current;
          if (el) el.classList.add('shimmer-text');
        }, [], 110);

        const pills = s8PillsRef.current?.querySelectorAll('.pill') ?? [];
        gsap.set(pills, { scale: 0 });
        masterTL.to(pills, { scale: 1, duration: 0.9, stagger: 0.15, ease: 'elastic.out(1, 0.55)' }, 112);

        gsap.set(s8VignetteRef.current, { opacity: 0 });
        masterTL.to(s8VignetteRef.current, { opacity: 1, duration: 2, ease: 'none' }, 115);

        masterTL.to(s8Ref.current, { opacity: 0, duration: 3, ease: 'power2.inOut' }, 117);
        gsap.set(endCursorRef.current, { opacity: 0 });
        masterTL.to(endCursorRef.current, { opacity: 1, duration: 0.4 }, 118);
        masterTL.to(endCursorRef.current, { opacity: 0, duration: 0.4 }, 118.6);

        gsap.set(endTitleRef.current, { opacity: 0 });
        masterTL.to(endTitleRef.current, { opacity: 1, duration: 0.5, ease: 'power2.out' }, 119);
        masterTL.to(blackFinalRef.current, { opacity: 1, duration: 0.8 }, 119.5);

        masterTL.to(featureMarqueeRef.current, { opacity: 1, duration: 0.45 }, 119.55);
        masterTL.to(cinemaBottomRef.current, { opacity: 1, duration: 0.45 }, 119.55);
        if (progressRailRef.current) masterTL.to(progressRailRef.current, { opacity: 1, duration: 0.45, ease: 'power2.out' }, 119.55);
        masterTL.to(phaseRef.current, { networkRailOpacity: 1, duration: 0.35, ease: 'none' }, 119.55);

        masterTL.eventCallback('onRestart', () => {
          startMsRef.current = performance.now();
          phaseRef.current.purple = 0;
          phaseRef.current.vortex = 0;
          phaseRef.current.camZ = 50;
          phaseRef.current.networkRailOpacity = 1;
          camera.position.z = 50;
          gsap.set(progressFillRef.current, { scaleX: 0, transformOrigin: 'left center' });
          if (featureMarqueeRef.current) gsap.set(featureMarqueeRef.current, { opacity: 1 });
          if (cinemaBottomRef.current) gsap.set(cinemaBottomRef.current, { opacity: 1 });
          if (progressRailRef.current) gsap.set(progressRailRef.current, { opacity: 1 });
          if (s1Line1Ref.current) s1Line1Ref.current.textContent = '';
          if (s1Line2Ref.current) s1Line2Ref.current.textContent = '';
          if (s1Line3Ref.current) s1Line3Ref.current.textContent = '';
          if (cursorRef.current) gsap.set(cursorRef.current, { opacity: 0 });
          if (whiteFlashRef.current) gsap.set(whiteFlashRef.current, { opacity: 0 });
          s1GlitchRef.current?.classList.remove('glitch-active');
          gsap.set(s1Ref.current, { opacity: 1 });
        });
      })
      .catch(() => {});

    return () => {
      killed = true;
      masterTLRef.current?.kill();
      threeCleanupRef.current?.();
    };
  }, [shieldGrad2, shieldGrad8, uid]);

  return (
    <div
      ref={rootRef}
      style={{
        position: 'relative',
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        background: '#020408',
        cursor: 'none',
      }}
    >
      <style
        dangerouslySetInnerHTML={{
          __html: `
@keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
@keyframes glitch {
  0%, 100% { clip-path: inset(0 0 95% 0); transform: translateX(0); }
  20% { clip-path: inset(30% 0 50% 0); transform: translateX(-5px); }
  40% { clip-path: inset(70% 0 10% 0); transform: translateX(5px); }
  60% { clip-path: inset(50% 0 30% 0); transform: translateX(-3px); }
  80% { clip-path: inset(10% 0 70% 0); transform: translateX(3px); }
}
@keyframes glitch-active { 0% { animation: glitch 0.0375s steps(1) 8; } }
.glitch-active { animation: glitch 0.0375s steps(1) 8 forwards; }
@keyframes shimmer { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
@keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-12px); } }
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(59,130,246,0.4); filter: drop-shadow(0 0 20px rgba(59,130,246,0.4)); }
  50% { box-shadow: 0 0 50px rgba(59,130,246,0.8), 0 0 100px rgba(59,130,246,0.3); filter: drop-shadow(0 0 50px rgba(59,130,246,0.8)); }
}
@keyframes rotate-gradient { 0% { filter: hue-rotate(0deg); } 100% { filter: hue-rotate(360deg); } }
@keyframes data-stream {
  0% { transform: translateY(-100%); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(100vh); opacity: 0; }
}
@keyframes counter-ping { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
@keyframes lab-glitch { 0%, 88% { transform: translateZ(0); filter: brightness(1); } 90% { transform: translate(2px,-1px); filter: brightness(1.15); } 93% { transform: translate(-2px,1px); } 96% { transform: translateZ(0); filter: brightness(1); } }
@keyframes scan-sweep { 0% { transform: translateY(-100%); } 100% { transform: translateY(100%); } }
@keyframes scan-bar { 0% { transform: translateX(-100%); } 100% { transform: translateX(240%); } }
@keyframes rotate-conic { to { transform: rotate(360deg); } }
@keyframes trailer-pan { 0% { transform: translateX(-35%) skewX(-8deg); opacity: 0; } 20% { opacity: .75; } 100% { transform: translateX(65%) skewX(-8deg); opacity: 0; } }
@keyframes premium-drift { 0%,100% { transform: translate3d(-2%, -1%, 0) scale(1); } 50% { transform: translate3d(2%, 1%, 0) scale(1.06); } }
@keyframes feature-marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
@keyframes pill-glow {
  0%,100%{ box-shadow: 0 0 12px rgba(59,130,246,0.25), 0 0 24px rgba(139,92,246,0.15); filter: drop-shadow(0 0 8px rgba(59,130,246,0.3)); }
  50%{ box-shadow: 0 0 28px rgba(6,182,212,0.45), 0 0 48px rgba(59,130,246,0.25); filter: drop-shadow(0 0 18px rgba(6,182,212,0.45)); }
}
.shimmer-text {
  background-size: 200% auto;
  animation: shimmer 4s linear infinite;
}
.terminal-cursor { animation: blink 1s step-end infinite; font-family: 'JetBrains Mono', monospace; font-size: 16px; color: #fff; }
.learn-detail-shell {
  box-sizing: border-box;
  width: 192px;
  min-height: 104px;
  padding: 11px 12px;
  border-radius: 14px;
  background: rgba(2, 6, 23, 0.97);
  border: 1px solid rgba(59, 130, 246, 0.28);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  line-height: 1.42;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: 0 8px 40px rgba(2, 4, 8, 0.95), 0 0 0 1px rgba(15, 23, 42, 0.95), 0 0 48px rgba(59, 130, 246, 0.12);
}
.learn-detail-inline {
  box-sizing: border-box;
  width: 100%;
  flex: 1;
  min-height: 108px;
  padding: 11px 11px 12px;
  margin: 0;
  border-radius: 0 0 11px 11px;
  background: rgba(2, 6, 23, 0.62);
  border: none;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  line-height: 1.42;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  box-shadow: none;
}
.scan-overlay {
  position: fixed; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
}
.cinema-bar { position: fixed; left: 0; right: 0; height: 4.8vh; z-index: 90; pointer-events: none; background: linear-gradient(180deg, rgba(0,0,0,.9), rgba(0,0,0,.2), transparent); }
.cinema-bar.bottom { bottom: 0; transform: rotate(180deg); }
.cinema-bar.top { top: 0; }
.premium-haze {
  position: fixed; inset: -20%; z-index: 2; pointer-events: none;
  background:
    radial-gradient(circle at 20% 20%, rgba(59,130,246,.22), transparent 28%),
    radial-gradient(circle at 82% 18%, rgba(139,92,246,.20), transparent 30%),
    radial-gradient(circle at 50% 84%, rgba(6,182,212,.12), transparent 34%);
  mix-blend-mode: screen;
  animation: premium-drift 9s ease-in-out infinite;
}
.trailer-beam {
  position: fixed; top: -12vh; bottom: -12vh; width: 34vw; z-index: 3; pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.16), transparent);
  filter: blur(18px);
  animation: trailer-pan 5.5s ease-in-out infinite;
}
.feature-marquee {
  position: fixed; left: 0; right: 0; bottom: 1.7vh; z-index: 101; overflow: hidden; pointer-events: none;
  mask-image: linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent);
}
.feature-marquee-track { display: flex; width: max-content; gap: 9px; animation: feature-marquee 24s linear infinite; }
.feature-chip {
  font-family: 'JetBrains Mono', monospace; font-size: 8px; letter-spacing: .14em; text-transform: uppercase;
  color: #94a3b8; border: 1px solid rgba(148,163,184,.16); border-radius: 999px;
  padding: 4px 8px; background: rgba(2,6,23,.28); backdrop-filter: blur(8px);
  box-shadow: 0 0 14px rgba(59,130,246,.08);
}
.scanner-sweep { position: absolute; top: 0; bottom: 0; width: 34%; background: linear-gradient(90deg, transparent, rgba(56,189,248,.24), transparent); animation: scan-bar 2.4s ease-in-out infinite; pointer-events: none; }
.panel-glass { background: linear-gradient(135deg, rgba(15,23,42,.88), rgba(2,6,23,.62)); border: 1px solid rgba(148,163,184,.22); backdrop-filter: blur(18px); box-shadow: 0 0 42px rgba(59,130,246,.12); }
`,
        }}
      />

      <div ref={threeMountRef} style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }} />

      <div className="scan-overlay" />
      <div className="premium-haze" />
      <div className="trailer-beam" />
      <div className="cinema-bar top" />
      <div ref={cinemaBottomRef} className="cinema-bar bottom" />
      <div ref={featureMarqueeRef} className="feature-marquee">
        <div className="feature-marquee-track">
          {[...FEATURE_TAGS, ...FEATURE_TAGS].map((tag, i) => (
            <span key={`${tag}-${i}`} className="feature-chip">
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div
        style={{
          position: 'fixed',
          top: 8,
          left: 16,
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          opacity: 0.6,
          fontFamily: 'Inter, sans-serif',
          fontWeight: 300,
          fontSize: 10,
          color: '#3b82f6',
        }}
      >
        <svg width={14} height={14} viewBox="0 0 24 24" fill="none">
          <path d="M12 3 L20 7 V13 Q20 18 12 21 Q4 18 4 13 V7 Z" stroke="#3b82f6" strokeWidth={1.2} />
        </svg>
        SCALE · OFFICIAL TRAILER
      </div>

      <div
        ref={sceneLabelRef}
        style={{
          position: 'fixed',
          top: 9,
          right: 16,
          zIndex: 100,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 9,
          color: '#475569',
          opacity: 1,
        }}
      >
        TRAILER | BREACH SIGNAL
      </div>

      <div
        ref={progressRailRef}
        style={{ position: 'fixed', bottom: 0, left: 0, right: 0, height: 2, zIndex: 100, background: 'rgba(15,23,42,0.6)' }}
      >
        <div
          ref={progressFillRef}
          style={{
            height: '100%',
            width: '100%',
            transform: 'scaleX(0)',
            transformOrigin: 'left center',
            background: 'linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4)',
            willChange: 'transform',
          }}
        />
      </div>

      <div style={{ position: 'relative', zIndex: 10, width: '100%', height: '100%' }}>
        <div
          ref={s1Ref}
          style={{
            position: 'absolute',
            inset: 0,
            background: '#000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div ref={s1GlitchRef} style={{ textAlign: 'left', maxWidth: 720 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span ref={cursorRef} className="terminal-cursor" style={{ opacity: 0 }}>
                ░
              </span>
            </div>
            <div ref={s1Line1Ref} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 16, color: '#ef4444', textShadow: '0 0 10px #ef4444' }} />
            <div ref={s1Line2Ref} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 16, color: '#f59e0b', marginTop: 8 }} />
            <div ref={s1Line3Ref} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 16, color: '#ef4444', fontWeight: 700, marginTop: 8 }} />
          </div>
          <div ref={whiteFlashRef} style={{ position: 'absolute', inset: 0, background: '#fff', opacity: 0, pointerEvents: 'none' }} />
        </div>

        <div ref={s2Ref} style={{ position: 'absolute', inset: 0, opacity: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div ref={s2LogoWrapRef} style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ width: 140, height: 168, marginBottom: 16 }}>
              <svg ref={s2ShieldRef} viewBox="0 0 100 120" fill="none" style={{ width: '100%', height: '100%' }}>
                <path
                  d="M50 5 L90 20 L90 55 Q90 95 50 115 Q10 95 10 55 L10 20 Z"
                  stroke={`url(#${shieldGrad2})`}
                  strokeWidth={1.5}
                  fill="none"
                  strokeDasharray={300}
                  strokeDashoffset={300}
                  className="shield-path"
                />
                <path
                  d="M50 20 L75 30 L75 55 Q75 80 50 95 Q25 80 25 55 L25 30 Z"
                  stroke="rgba(59,130,246,0.4)"
                  strokeWidth={0.5}
                  fill="none"
                  strokeDasharray={220}
                  strokeDashoffset={220}
                  className="shield-inner"
                />
                <circle cx={50} cy={58} r={8} stroke="rgba(59,130,246,0.7)" strokeWidth={1} fill="none" className="shield-circle" />
                <defs>
                  <linearGradient id={shieldGrad2} x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="50%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#06b6d4" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div style={{ position: 'relative', overflow: 'hidden' }}>
              <div ref={s2LogoRowRef} style={{ display: 'flex', gap: '0.3em' }}>
                {'SCALE'.split('').map((ch, si) => (
                  <span
                    key={`${ch}-${si}`}
                    className="scale-letter"
                    style={{
                      display: 'inline-block',
                      fontFamily: "'Space Grotesk', sans-serif",
                      fontWeight: 900,
                      fontSize: 120,
                      letterSpacing: '0.3em',
                      background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4)',
                      WebkitBackgroundClip: 'text',
                      backgroundClip: 'text',
                      color: 'transparent',
                      willChange: 'transform',
                    }}
                  >
                    {ch}
                  </span>
                ))}
              </div>
              <div
                ref={s2ShimmerRef}
                style={{
                  position: 'absolute',
                  inset: 0,
                  pointerEvents: 'none',
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent)',
                  opacity: 0,
                  mixBlendMode: 'screen',
                  transform: 'translateX(-100%)',
                }}
              />
            </div>
            <div
              ref={s2SubRef}
              style={{
                marginTop: 24,
                fontFamily: 'Inter, sans-serif',
                fontWeight: 200,
                fontSize: 18,
                letterSpacing: '0.5em',
                color: '#94a3b8',
                textTransform: 'uppercase',
              }}
            >
              Attack labs. AI guidance. Classroom-grade proof.
            </div>
            <div ref={s2RingsRef} style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="exp-ring"
                  style={{
                    position: 'absolute',
                    width: 200,
                    height: 200,
                    borderRadius: '50%',
                    border: '1px solid rgba(59,130,246,0.3)',
                    opacity: 0,
                  }}
                />
              ))}
            </div>
          </div>
        </div>

        <div
          ref={s3Ref}
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0,
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'stretch',
            background: 'linear-gradient(180deg, #020408 0%, #0a0f1a 100%)',
          }}
        >
          <div
            ref={s3LeftRef}
            style={{
              flex: 1,
              padding: '10vh 6vw',
              display: 'flex',
              flexDirection: 'column',
              gap: 48,
              justifyContent: 'center',
              willChange: 'transform',
            }}
          >
            <div ref={stat1WrapRef}>
              <div ref={stat1NumRef} style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 64, color: '#f8fafc' }}>
                0
              </div>
              <div style={{ height: 2, width: '80%', marginTop: 12, background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)' }} />
              <div style={{ fontFamily: 'Inter, sans-serif', fontWeight: 300, fontSize: 14, color: '#94a3b8', marginTop: 12 }}>
                Cybersecurity roles waiting for practical skill
              </div>
            </div>
            <div ref={stat2WrapRef}>
              <div ref={stat2NumRef} style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 64, color: '#ef4444' }}>
                0%
              </div>
              <div style={{ fontFamily: 'Inter, sans-serif', fontWeight: 300, fontSize: 14, color: '#94a3b8', marginTop: 12 }}>
                Breaches still begin with preventable mistakes
              </div>
            </div>
            <div ref={stat3WrapRef}>
              <div ref={stat3NumRef} style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 64, color: '#f59e0b' }}>
                $0M
              </div>
              <div style={{ fontFamily: 'Inter, sans-serif', fontWeight: 300, fontSize: 14, color: '#94a3b8', marginTop: 12 }}>
                Average breach impact makes practice urgent
              </div>
            </div>
          </div>
          <div
            ref={s3RightRef}
            style={{
              flex: 1,
              padding: '10vh 6vw',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              gap: 28,
              willChange: 'transform',
            }}
          >
            <div
              ref={quoteWordsRef}
              style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 28, color: '#f8fafc', lineHeight: 1.35 }}
            >
              {'Theory is not enough.'.split(' ').map((w, i) => (
                <span key={`q1-${i}`} className="qw" style={{ display: 'inline-block', marginRight: 8 }}>
                  {w}
                </span>
              ))}
              <br />
              {'SCALE turns every finding into a mission.'.split(' ').map((w, i) => (
                <span key={`q2-${i}`} className="qw" style={{ display: 'inline-block', marginRight: 8 }}>
                  {w}
                </span>
              ))}
            </div>
            <div
              ref={bridgeRef}
              style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontWeight: 700,
                fontSize: 20,
                background: 'linear-gradient(90deg, #3b82f6, #06b6d4)',
                WebkitBackgroundClip: 'text',
                backgroundClip: 'text',
                color: 'transparent',
              }}
            >
              Scan the project. Break the weakness. Fix it. Prove mastery.
            </div>
          </div>
        </div>

        <div
          ref={s4Ref}
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '5vh 4vw clamp(100px, 14vh, 160px)',
            background: 'rgba(2, 4, 8, 0.82)',
          }}
        >
          <div
            ref={s4TitleRef}
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 800,
              fontSize: 42,
              marginBottom: 18,
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              color: 'transparent',
            }}
          >
            Scan. Simulate. Learn.
          </div>
          <div
            className="panel-glass"
            style={{
              width: 'min(1120px, 94vw)',
              borderRadius: 22,
              padding: '20px 22px 22px',
              display: 'flex',
              flexDirection: 'column',
              gap: 17,
              position: 'relative',
              zIndex: 14,
              overflow: 'visible',
              boxShadow: '0 0 0 1px rgba(59,130,246,0.14), 0 28px 88px rgba(2,4,8,0.88)',
            }}
          >
            <div
              className="scanner-demo"
              style={{
                position: 'relative',
                borderRadius: 18,
                overflow: 'hidden',
                border: '1px solid rgba(59,130,246,0.22)',
                background: 'linear-gradient(180deg, rgba(15,23,42,0.55), rgba(2,6,23,0.38))',
              }}
            >
              <div className="scanner-sweep" />
              <div style={{ display: 'grid', gridTemplateColumns: '1.05fr 1.35fr 1fr', gap: 14, alignItems: 'stretch', padding: 16 }}>
                <div style={{ borderRadius: 14, background: 'rgba(2,6,23,.58)', border: '1px solid rgba(59,130,246,.22)', padding: 14 }}>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: '.18em', color: '#38bdf8', textTransform: 'uppercase' }}>Project Scanner</div>
                  <div style={{ marginTop: 12, fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 22, color: '#f8fafc' }}>Upload source code</div>
                  <div style={{ marginTop: 10, height: 8, borderRadius: 999, background: '#0f172a', overflow: 'hidden' }}>
                    <div className="scan-progress" style={{ height: '100%', width: '78%', background: 'linear-gradient(90deg,#3b82f6,#06b6d4)', borderRadius: 999, boxShadow: '0 0 22px rgba(56,189,248,.45)' }} />
                  </div>
                  <div style={{ marginTop: 12, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: '#94a3b8', lineHeight: 1.7 }}>
                    <div>Semgrep rules loaded</div>
                    <div>Dependencies analyzed</div>
                    <div>Routes mapped to labs</div>
                  </div>
                </div>
                <div
                  style={{
                    borderRadius: 14,
                    background: 'rgba(2,6,23,.48)',
                    border: '1px solid rgba(148,163,184,.18)',
                    padding: 14,
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: 0,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: '#64748b', letterSpacing: '.16em' }}>LIVE FINDINGS</span>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: '#10b981' }}>3 confirmed</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
                    {SCAN_FINDINGS.map((finding) => (
                      <div
                        key={finding.type}
                        className="scan-finding"
                        style={{
                          display: 'grid',
                          gridTemplateColumns: '1fr auto',
                          gap: 10,
                          alignItems: 'center',
                          padding: '9px 10px',
                          borderRadius: 10,
                          background: `${finding.color}12`,
                          border: `1px solid ${finding.color}44`,
                        }}
                      >
                        <div>
                          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 13, color: '#f8fafc' }}>{finding.type}</div>
                          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: '#94a3b8', marginTop: 3 }}>{finding.file}</div>
                        </div>
                        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: finding.color, border: `1px solid ${finding.color}55`, borderRadius: 999, padding: '4px 7px' }}>{finding.severity}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div style={{ borderRadius: 14, background: 'rgba(6,182,212,.08)', border: '1px solid rgba(6,182,212,.24)', padding: 14 }}>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: '#67e8f9', letterSpacing: '.14em' }}>AI EXPLAINS</div>
                  <div style={{ marginTop: 12, fontFamily: 'Inter, sans-serif', fontSize: 12, color: '#cbd5e1', lineHeight: 1.55 }}>
                    &quot;This finding becomes an attack simulation, then a fix challenge, then a mistake-based quiz.&quot;
                  </div>
                  <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                    {['Explain', 'Simulate', 'Quiz', 'Retest'].map((step) => (
                      <span key={step} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: '#e0f2fe', padding: '5px 7px', borderRadius: 999, background: 'rgba(59,130,246,.18)' }}>
                        {step}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'baseline',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: 10,
                padding: '2px 4px 0',
              }}
            >
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: '0.2em', color: '#64748b', textTransform: 'uppercase' }}>
                Training pipeline
              </span>
              <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 11, color: '#475569' }}>Finding → lab → patch → quiz → proof</span>
            </div>
            <div
              ref={s4RowRef}
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
                gap: 11,
                width: '100%',
                willChange: 'transform',
              }}
            >
              {[
                {
                  n: '01',
                  t: 'SCAN',
                  d: 'Upload a project. Detect vulnerable code, routes, and packages.',
                  accent: '#3b82f6',
                  icon: (
                    <svg width={36} height={36} viewBox="0 0 24 24" fill="none">
                      <defs>
                        <clipPath id={`scanLens-${uid}`}>
                          <circle cx={11} cy={11} r={7} />
                        </clipPath>
                      </defs>
                      <circle cx={11} cy={11} r={7} stroke="#3b82f6" strokeWidth={1.5} />
                      <g clipPath={`url(#scanLens-${uid})`}>
                        <rect x={4} width={14} height={3} fill="rgba(59,130,246,0.55)">
                          <animate attributeName="y" values="-4;18;-4" dur="2.2s" repeatCount="indefinite" />
                        </rect>
                      </g>
                      <path d="M16 16 L21 21" stroke="#3b82f6" strokeWidth={1.5} />
                    </svg>
                  ),
                },
                {
                  n: '02',
                  t: 'ATTACK',
                  d: 'Exploit safely inside guided labs with real payloads.',
                  accent: '#ef4444',
                  icon: (
                    <svg width={36} height={36} viewBox="0 0 24 24" fill="none">
                      <path d="M13 3 L5 14 H11 L9 21 L17 10 H11 Z" fill="#ef4444" />
                    </svg>
                  ),
                },
                {
                  n: '03',
                  t: 'FIX',
                  d: 'Patch the flaw and validate it in a Docker sandbox.',
                  accent: '#10b981',
                  icon: (
                    <svg width={36} height={36} viewBox="0 0 24 24" fill="none">
                      <path d="M14 3 L5 12 L10 17 L21 6" stroke="#10b981" strokeWidth={2} />
                    </svg>
                  ),
                },
                {
                  n: '04',
                  t: 'QUIZ',
                  d: 'Focused questions from scan results and lab progress.',
                  accent: '#8b5cf6',
                  icon: (
                    <svg width={36} height={36} viewBox="0 0 24 24" fill="none">
                      <path d="M12 4 Q8 8 8 14 Q8 18 12 20 Q16 18 16 14 Q16 8 12 4 Z" stroke="#8b5cf6" strokeWidth={1.5} fill="none" />
                    </svg>
                  ),
                },
                {
                  n: '05',
                  t: 'MASTERY',
                  d: 'Scores, logs, and classroom-ready reporting.',
                  accent: '#06b6d4',
                  icon: (
                    <svg width={36} height={36} viewBox="0 0 24 24" fill="none">
                      <polyline points="4,18 8,12 12,14 20,6" stroke="#06b6d4" strokeWidth={2} fill="none" />
                    </svg>
                  ),
                },
              ].map((c, i) => (
                <div
                  key={c.t}
                  ref={(el) => {
                    cardRefs.current[i] = el;
                  }}
                  className={`learn-card-${i}`}
                  style={{
                    borderRadius: 14,
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: 0,
                    background: 'rgba(15, 23, 42, 0.78)',
                    border: `1px solid ${c.accent}40`,
                    backdropFilter: 'blur(18px)',
                    boxShadow: '0 10px 36px rgba(2,4,8,0.65)',
                    willChange: 'transform',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 10,
                      padding: '11px 11px 10px',
                      borderBottom: '1px solid rgba(148,163,184,0.12)',
                      background: 'rgba(2,6,23,0.45)',
                    }}
                  >
                    <div
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: 9,
                        background: 'rgba(2, 6, 23, 0.72)',
                        border: `1px solid ${c.accent}55`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        boxSizing: 'border-box',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', transform: 'scale(0.68)', transformOrigin: 'center' }}>{c.icon}</div>
                    </div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: '#64748b', letterSpacing: '0.08em' }}>{c.n}</div>
                      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 13, color: '#f8fafc', letterSpacing: '0.06em', marginTop: 2 }}>{c.t}</div>
                      <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 9.5, color: '#64748b', lineHeight: 1.35, marginTop: 5 }}>{c.d}</div>
                    </div>
                  </div>
                  {i === 0 && (
                    <div className="learn-detail-inline">
                      <div style={{ fontSize: 8.5, letterSpacing: '0.14em', color: '#64748b', marginBottom: 8 }}>FINDINGS</div>
                      <div>/src/app.py</div>
                      <div style={{ color: '#ef4444' }}>query = f&quot;SELECT * WHERE id={'{id}'}&quot;</div>
                      <div>/routes/login.ts</div>
                      <div style={{ color: '#ef4444' }}>redirect(nextUrl)</div>
                    </div>
                  )}
                  {i === 1 && (
                    <div className="learn-detail-inline">
                      <div style={{ fontSize: 8.5, letterSpacing: '0.14em', color: '#64748b', marginBottom: 8 }}>EXPLOIT</div>
                      <div>
                        <span style={{ color: '#10b981' }}>$ </span>
                        <span>{' OR 1=1 --'}</span>
                      </div>
                      <div style={{ color: '#10b981', marginTop: 6 }}>ACCESS GRANTED</div>
                    </div>
                  )}
                  {i === 2 && (
                    <div className="learn-detail-inline">
                      <div style={{ fontSize: 8.5, letterSpacing: '0.14em', color: '#64748b', marginBottom: 8 }}>DIFF</div>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'stretch', minHeight: 42 }}>
                        <div style={{ flex: 1, padding: 7, background: 'rgba(239,68,68,0.1)', borderRadius: 8, display: 'flex', alignItems: 'center' }}>
                          <div style={{ color: '#ef4444', fontSize: 8.5 }}>- query = f&quot;...{'{name}'}&quot;</div>
                        </div>
                        <div style={{ color: '#94a3b8', alignSelf: 'center', fontSize: 11 }}>→</div>
                        <div style={{ flex: 1, padding: 7, background: 'rgba(16,185,129,0.1)', borderRadius: 8, display: 'flex', alignItems: 'center' }}>
                          <div style={{ color: '#10b981', fontSize: 8.5 }}>+ execute(sql, params)</div>
                        </div>
                      </div>
                    </div>
                  )}
                  {i === 3 && (
                    <div className="learn-detail-inline">
                      <div style={{ fontSize: 8.5, letterSpacing: '0.14em', color: '#64748b', marginBottom: 8 }}>QUIZ</div>
                      <div style={{ marginBottom: 8, fontFamily: "'Space Grotesk', sans-serif", fontWeight: 600, fontSize: 10.5, color: '#e2e8f0' }}>Why is string concat unsafe?</div>
                      <div style={{ color: '#10b981' }}>✓ SQL injection risk</div>
                    </div>
                  )}
                  {i === 4 && (
                    <div className="learn-detail-inline">
                      <div style={{ fontSize: 8.5, letterSpacing: '0.14em', color: '#64748b', marginBottom: 8 }}>MASTERY</div>
                      <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end', justifyContent: 'space-between', flex: 1 }}>
                        {PROGRESS_VALUES.map((_v, j) => (
                          <div key={PROGRESS_LABELS[j]} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, flex: 1 }}>
                            <div style={{ width: '100%', maxWidth: 11, height: 26, background: '#1e293b', borderRadius: 3, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                              <div
                                className={`bar-fill-${j}`}
                                style={{
                                  width: '100%',
                                  height: '100%',
                                  transform: 'scaleY(0)',
                                  transformOrigin: 'bottom center',
                                  background: '#06b6d4',
                                  willChange: 'transform',
                                }}
                              />
                            </div>
                            <div style={{ fontSize: 6.5, color: '#64748b', textAlign: 'center', lineHeight: 1 }}>{PROGRESS_LABELS[j]}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
              gap: 11,
              width: '100%',
            }}
          >
            {PROOF_POINTS.map((point) => (
              <div
                key={point.label}
                className="proof-card"
                style={{
                  borderRadius: 13,
                  padding: '11px 13px',
                  background: 'rgba(15,23,42,0.72)',
                  border: '1px solid rgba(59,130,246,0.18)',
                  backdropFilter: 'blur(18px)',
                  boxShadow: '0 8px 28px rgba(2,4,8,0.55)',
                }}
              >
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: '0.16em', color: '#64748b', textTransform: 'uppercase' }}>{point.label}</div>
                <div style={{ marginTop: 6, fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 14, color: '#e2e8f0' }}>{point.value}</div>
              </div>
            ))}
          </div>
          </div>
        </div>

        <div
          ref={s5Ref}
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '8vh 5vw',
            background: 'rgba(2, 4, 8, 0.78)',
            isolation: 'isolate',
          }}
        >
          <div style={{ position: 'relative', width: '100%', maxWidth: 1120, minHeight: 460 }}>
            <div
              ref={s5SpotRef}
              style={{
                position: 'absolute',
                inset: 0,
                zIndex: 1,
                pointerEvents: 'none',
                opacity: 0,
                background: 'radial-gradient(circle at 20% 20%, rgba(255,255,255,0.14), transparent 48%)',
                mixBlendMode: 'screen',
                willChange: 'transform, opacity',
              }}
            />
            <div
              ref={s5GridRef}
              style={{
                position: 'relative',
                zIndex: 4,
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 200px)',
                gridTemplateRows: 'repeat(2, 120px)',
                gap: 16,
                justifyContent: 'center',
              }}
            >
              {LABS.map((lab, idx) => (
                <div
                  key={lab.name}
                  ref={(el) => {
                    labCardRefs.current[idx] = el;
                  }}
                  style={{
                    width: 200,
                    height: 120,
                    borderRadius: 12,
                    background: 'rgba(15,23,42,0.96)',
                    border: '1px solid rgba(148,163,184,0.25)',
                    overflow: 'hidden',
                    boxShadow: `0 0 24px ${lab.color}22`,
                    filter: 'drop-shadow(0 0 8px rgba(59,130,246,0.15))',
                    animation: 'lab-glitch 4s ease-in-out infinite',
                    animationDelay: `${idx * 0.27}s`,
                    willChange: 'transform',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <div style={{ height: 4, background: lab.color }} />
                  <div
                    style={{
                      padding: '10px 12px',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      flex: 1,
                      minHeight: 86,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10 }}>
                      <span
                        style={{
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: 13,
                          color: '#f8fafc',
                          lineHeight: 1.25,
                          flex: 1,
                          paddingTop: 2,
                        }}
                      >
                        {lab.name}
                      </span>
                      <span style={{ flexShrink: 0, width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <LabGlyph kind={lab.iconKind} color={lab.color} />
                      </span>
                    </div>
                    <div
                      style={{
                        alignSelf: 'flex-start',
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 10,
                        padding: '3px 9px',
                        borderRadius: 999,
                        background: `${lab.color}22`,
                        color: lab.color,
                        border: `1px solid ${lab.color}55`,
                        marginTop: 8,
                      }}
                    >
                      {lab.sev}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div
              ref={s5OverlayRef}
              style={{
                position: 'absolute',
                inset: 0,
                zIndex: 18,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                pointerEvents: 'none',
                padding: '0 16px',
              }}
            >
              <div
                className="s5-line"
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 900,
                  fontSize: 'clamp(30px, 4.5vw, 44px)',
                  lineHeight: 1.12,
                  letterSpacing: '-0.02em',
                  background: 'linear-gradient(90deg,#3b82f6,#06b6d4)',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  color: 'transparent',
                  filter: 'drop-shadow(0 2px 24px rgba(0,0,0,0.9)) drop-shadow(0 0 18px rgba(59,130,246,0.65))',
                  textShadow: '0 0 40px rgba(2,4,8,1)',
                }}
              >
                EVERY core vulnerability.
              </div>
              <div
                className="s5-line"
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 900,
                  fontSize: 'clamp(30px, 4.5vw, 44px)',
                  lineHeight: 1.12,
                  letterSpacing: '-0.02em',
                  marginTop: 14,
                  background: 'linear-gradient(90deg,#8b5cf6,#ef4444)',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  color: 'transparent',
                  filter: 'drop-shadow(0 2px 24px rgba(0,0,0,0.9)) drop-shadow(0 0 18px rgba(236,72,153,0.55))',
                }}
              >
                REAL exploitation paths.
              </div>
              <div
                className="s5-line"
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 900,
                  fontSize: 'clamp(30px, 4.5vw, 44px)',
                  lineHeight: 1.12,
                  letterSpacing: '-0.02em',
                  marginTop: 14,
                  background: 'linear-gradient(90deg,#10b981,#3b82f6)',
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  color: 'transparent',
                  filter: 'drop-shadow(0 2px 24px rgba(0,0,0,0.9)) drop-shadow(0 0 18px rgba(16,185,129,0.55))',
                }}
              >
                REAL remediation evidence.
              </div>
            </div>
          </div>
        </div>

        <div ref={s6Ref} style={{ position: 'absolute', inset: 0, opacity: 0, display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>
          <div style={{ flex: 1, background: '#1a0000', padding: '8vh 5vw', display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 900, fontSize: 36, color: '#ef4444', filter: 'drop-shadow(0 0 14px rgba(239,68,68,0.45))', boxShadow: 'none' }}>RED TEAM</div>
            <div style={{ fontFamily: 'Inter, sans-serif', fontWeight: 500, fontSize: 14, color: '#fca5a5', letterSpacing: '0.4em' }}>ATTACK</div>
            <div
              ref={redTermRef}
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 13,
                color: '#fecaca',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6,
                textShadow: '0 0 10px rgba(239,68,68,0.45)',
              }}
            />
            <div style={{ position: 'relative', marginTop: 'auto' }}>
              <div
                ref={redScoreRef}
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 900,
                  fontSize: 28,
                  color: '#ef4444',
                  opacity: 0,
                  filter: 'drop-shadow(0 0 18px rgba(239,68,68,0.5))',
                  boxShadow: '0 0 24px rgba(239,68,68,0.25)',
                }}
              >
                SCORE +1
              </div>
              <div ref={redBurstRef} style={{ position: 'absolute', left: '40%', top: '40%', width: 8, height: 8, opacity: 0, pointerEvents: 'none' }}>
                {[...Array(10)].map((_, bi) => (
                  <span
                    key={bi}
                    style={{
                      position: 'absolute',
                      width: 6,
                      height: 6,
                      borderRadius: 999,
                      background: bi % 2 ? '#f97316' : '#ef4444',
                      transform: `rotate(${bi * 36}deg) translateX(0px)`,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
          <div
            ref={s6CenterRef}
            style={{
              width: 2,
              alignSelf: 'stretch',
              background: 'linear-gradient(180deg, #ef4444, #3b82f6)',
              boxShadow: '0 0 24px rgba(255,255,255,0.35), 0 0 48px rgba(59,130,246,0.35)',
              filter: 'drop-shadow(0 0 12px rgba(239,68,68,0.35))',
              transformOrigin: 'center',
              willChange: 'transform',
            }}
          />
          <div style={{ flex: 1, background: '#00001a', padding: '8vh 5vw', display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 900, fontSize: 36, color: '#3b82f6', filter: 'drop-shadow(0 0 14px rgba(59,130,246,0.45))' }}>BLUE TEAM</div>
            <div style={{ fontFamily: 'Inter, sans-serif', fontWeight: 500, fontSize: 14, color: '#93c5fd', letterSpacing: '0.4em' }}>DEFEND</div>
            <div
              ref={blueEditorRef}
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 13,
                color: '#a7f3d0',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6,
                borderLeft: '2px solid rgba(59,130,246,0.5)',
                paddingLeft: 12,
              }}
            />
            <div style={{ position: 'relative', marginTop: 'auto' }}>
              <div
                ref={blueScoreRef}
                style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontWeight: 900,
                  fontSize: 26,
                  color: '#3b82f6',
                  opacity: 0,
                  filter: 'drop-shadow(0 0 18px rgba(59,130,246,0.5))',
                  boxShadow: '0 0 24px rgba(59,130,246,0.25)',
                }}
              >
                FIX SUBMITTED · TESTS PASSED · SCORE +1
              </div>
              <div ref={blueBurstRef} style={{ position: 'absolute', left: '40%', top: '40%', width: 8, height: 8, opacity: 0, pointerEvents: 'none' }}>
                {[...Array(10)].map((_, bi) => (
                  <span
                    key={bi}
                    style={{
                      position: 'absolute',
                      width: 6,
                      height: 6,
                      borderRadius: 999,
                      background: bi % 2 ? '#06b6d4' : '#3b82f6',
                      transform: `rotate(${bi * 36}deg) translateX(0px)`,
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
          <div
            ref={s6BadgeRef}
            style={{
              position: 'absolute',
              left: '50%',
              top: '12%',
              transform: 'translateX(-50%)',
              padding: '10px 22px',
              borderRadius: 999,
              border: '1px solid rgba(255,255,255,0.35)',
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 800,
              fontSize: 14,
              letterSpacing: '0.25em',
              color: '#f8fafc',
              background: 'rgba(15,23,42,0.75)',
              backdropFilter: 'blur(16px)',
              opacity: 0,
              boxShadow: '0 0 30px rgba(59,130,246,0.25), 0 0 60px rgba(239,68,68,0.15)',
              filter: 'drop-shadow(0 0 14px rgba(255,255,255,0.25))',
            }}
          >
            BATTLE ACTIVE
          </div>
        </div>

        <div ref={s7Ref} style={{ position: 'absolute', inset: 0, opacity: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '6vh 4vw', willChange: 'transform' }}>
          <svg ref={s7BrainRef} width={340} height={340} viewBox="0 0 200 200" style={{ position: 'absolute', filter: 'drop-shadow(0 0 24px rgba(139,92,246,0.35))' }}>
            {[0, 1, 2, 3, 4, 5].map((i) => {
              const cx = 100 + Math.cos((i / 6) * Math.PI * 2) * 55;
              const cy = 100 + Math.sin((i / 6) * Math.PI * 2) * 55;
              return <circle key={i} className="brain-node" cx={cx} cy={cy} r={7} fill="#c4b5fd" opacity={0.35} stroke="#8b5cf6" strokeWidth={1} />;
            })}
            {[0, 2, 4].map((i) => (
              <line key={`ln-${i}`} x1={100} y1={100} x2={100 + Math.cos((i / 6) * Math.PI * 2) * 55} y2={100 + Math.sin((i / 6) * Math.PI * 2) * 55} stroke="rgba(139,92,246,0.45)" strokeWidth={1.5} />
            ))}
          </svg>

          <div
            ref={s7c1Ref}
            style={{
              position: 'absolute',
              left: '8%',
              top: '22%',
              width: 260,
              padding: 16,
              borderRadius: 16,
              background: 'rgba(15,23,42,0.72)',
              border: '1px solid rgba(139,92,246,0.35)',
              backdropFilter: 'blur(18px)',
              boxShadow: '0 0 36px rgba(139,92,246,0.22)',
              filter: 'drop-shadow(0 0 14px rgba(139,92,246,0.35))',
            }}
          >
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, color: '#f8fafc', marginBottom: 8 }}>AI Explains the Simulation</div>
            <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>Every exploit is explained step by step before the learner fixes it.</div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: '#cbd5e1', lineHeight: 1.45 }}>
              <div>&quot;Why did this payload work?&quot;</div>
              <div style={{ color: '#a78bfa', marginTop: 8 }}>AI: &quot;The query trusted user input, so the condition became always true.&quot;</div>
            </div>
          </div>

          <div
            ref={s7c2Ref}
            style={{
              position: 'absolute',
              right: '8%',
              top: '22%',
              width: 260,
              padding: 16,
              borderRadius: 16,
              background: 'rgba(15,23,42,0.72)',
              border: '1px solid rgba(59,130,246,0.35)',
              backdropFilter: 'blur(18px)',
              boxShadow: '0 0 36px rgba(59,130,246,0.22)',
              filter: 'drop-shadow(0 0 14px rgba(59,130,246,0.35))',
            }}
          >
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, color: '#f8fafc', marginBottom: 8 }}>Common Mistakes Exam</div>
            <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>Quizzes learn from wrong answers and repeat the weak points.</div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: '#cbd5e1' }}>
              {COMMON_MISTAKES.map((mistake, i) => (
                <div key={mistake} className="mistake-row" style={{ marginTop: i ? 7 : 0, padding: '7px 8px', borderRadius: 8, background: 'rgba(59,130,246,.08)', border: '1px solid rgba(59,130,246,.18)' }}>
                  {i + 1}. {mistake}
                </div>
              ))}
            </div>
          </div>

          <div
            ref={s7c3Ref}
            style={{
              position: 'absolute',
              left: '50%',
              bottom: '8%',
              transform: 'translateX(-50%)',
              width: 280,
              padding: 16,
              borderRadius: 16,
              background: 'rgba(15,23,42,0.72)',
              border: '1px solid rgba(6,182,212,0.35)',
              backdropFilter: 'blur(18px)',
              boxShadow: '0 0 36px rgba(6,182,212,0.22)',
              filter: 'drop-shadow(0 0 14px rgba(6,182,212,0.35))',
            }}
          >
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, color: '#f8fafc', marginBottom: 8 }}>AI-Powered Scanning</div>
            <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>Semgrep + OWASP rulesets. 30+ languages.</div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, color: '#cbd5e1' }}>
              <span style={{ color: '#94a3b8' }}>rules:</span> <span style={{ color: '#f59e0b' }}>python.sqlalchemy.security</span>
            </div>
          </div>

          <div
            ref={s7c4Ref}
            style={{
              position: 'absolute',
              right: '11%',
              bottom: '10%',
              width: 270,
              padding: 16,
              borderRadius: 16,
              background: 'rgba(15,23,42,0.72)',
              border: '1px solid rgba(16,185,129,0.35)',
              backdropFilter: 'blur(18px)',
              boxShadow: '0 0 36px rgba(16,185,129,0.18)',
              filter: 'drop-shadow(0 0 14px rgba(16,185,129,0.28))',
            }}
          >
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 16, color: '#f8fafc', marginBottom: 8 }}>Leaderboard + Instructor View</div>
            <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>Scores update from labs, quizzes, fixes, and Red vs Blue wins.</div>
            <div style={{ display: 'grid', gap: 7, fontFamily: "'JetBrains Mono', monospace", fontSize: 10 }}>
              {LEADERBOARD.map((row, i) => (
                <div key={row.name} className="leader-row" style={{ display: 'grid', gridTemplateColumns: '22px 1fr auto auto', gap: 8, alignItems: 'center', color: '#e2e8f0', padding: '7px 8px', borderRadius: 9, background: i === 0 ? 'rgba(16,185,129,.14)' : 'rgba(59,130,246,.08)' }}>
                  <span style={{ color: i === 0 ? '#facc15' : '#94a3b8' }}>#{i + 1}</span>
                  <span>{row.name}</span>
                  <span style={{ color: '#38bdf8' }}>{row.score}</span>
                  <span style={{ color: '#10b981' }}>{row.trend}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div ref={s8Ref} style={{ position: 'absolute', inset: 0, opacity: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '6vh 4vw', willChange: 'transform, opacity' }}>
          <div style={{ position: 'relative', width: 400, height: 400 }}>
            <div
              style={{
                position: 'absolute',
                inset: -40,
                borderRadius: '50%',
                background: 'conic-gradient(from 0deg, #3b82f6, #8b5cf6, #06b6d4, #10b981, #3b82f6)',
                opacity: 0.35,
                animation: 'rotate-conic 12s linear infinite',
                filter: 'blur(24px)',
              }}
            />
            <svg ref={s8ShieldRef} viewBox="0 0 100 120" fill="none" style={{ width: 400, height: 400, position: 'relative', filter: 'drop-shadow(0 0 40px rgba(59,130,246,0.45))' }}>
              <path
                d="M50 5 L90 20 L90 55 Q90 95 50 115 Q10 95 10 55 L10 20 Z"
                stroke={`url(#${shieldGrad8})`}
                strokeWidth={1.5}
                fill="none"
                strokeDasharray={300}
                strokeDashoffset={300}
                className="shield-path"
              />
              <path
                d="M50 20 L75 30 L75 55 Q75 80 50 95 Q25 80 25 55 L25 30 Z"
                stroke="rgba(59,130,246,0.4)"
                strokeWidth={0.5}
                fill="none"
                strokeDasharray={220}
                strokeDashoffset={220}
                className="shield-inner"
              />
              <circle cx={50} cy={58} r={8} stroke="rgba(59,130,246,0.7)" strokeWidth={1} fill="none" className="shield-circle" />
              <defs>
                <linearGradient id={shieldGrad8} x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="50%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
            </svg>
            <div ref={s8RingsRef} style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
              {['#3b82f6', '#06b6d4', '#8b5cf6', '#10b981', '#f8fafc'].map((col) => (
                <div
                  key={col}
                  className="pulse-ring"
                  style={{
                    position: 'absolute',
                    width: 120,
                    height: 120,
                    borderRadius: '50%',
                    border: `2px solid ${col}`,
                    opacity: 0.8,
                    boxShadow: `0 0 40px ${col}66`,
                    filter: `drop-shadow(0 0 24px ${col}88)`,
                  }}
                />
              ))}
            </div>
          </div>

          <div ref={s8L1Ref} style={{ marginTop: 28, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.06em' }}>
            {'ENTER THE LAB.'.split('').map((ch, i) => (
              <span key={`${ch}-${i}`} className="stamp-ch" style={{ display: 'inline-block', fontFamily: "'Space Grotesk', sans-serif", fontWeight: 900, fontSize: 72, color: '#f8fafc', willChange: 'transform, opacity, filter' }}>
                {ch === ' ' ? '\u00a0' : ch}
              </span>
            ))}
          </div>
          <div ref={s8L2Ref} style={{ marginTop: 16, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.06em' }}>
            {'ATTACK. DEFEND. PROVE MASTERY.'.split('').map((ch, i) => (
              <span key={`${ch}-l2-${i}`} className="stamp-ch" style={{ display: 'inline-block', fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300, fontSize: 48, color: '#94a3b8', willChange: 'transform, opacity, filter' }}>
                {ch === ' ' ? '\u00a0' : ch}
              </span>
            ))}
          </div>
          <div
            ref={s8L3Ref}
            style={{
              marginTop: 24,
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 900,
              fontSize: 96,
              background: 'linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              color: 'transparent',
              filter: 'drop-shadow(0 0 24px rgba(59,130,246,0.35))',
              boxSizing: 'border-box',
            }}
          >
            SCALE
          </div>

          <div ref={s8PillsRef} style={{ marginTop: 28, display: 'flex', gap: 14, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 940, position: 'relative', zIndex: 30 }}>
            {['Project Scanner', 'Attack Simulation', 'AI Explanation', 'Common Mistakes Exam', 'Leaderboard', 'Red vs Blue Arena'].map((t) => (
              <div
                key={t}
                className="pill"
                style={{
                  padding: '10px 18px',
                  borderRadius: 999,
                  fontFamily: 'Inter, sans-serif',
                  fontWeight: 500,
                  fontSize: 13,
                  color: '#e2e8f0',
                  border: '2px solid transparent',
                  background: 'linear-gradient(#0a0f1a, #0a0f1a) padding-box, linear-gradient(135deg, #3b82f6, #8b5cf6, #06b6d4) border-box',
                  backdropFilter: 'blur(12px)',
                  animation: 'pill-glow 3s ease-in-out infinite',
                  boxShadow: '0 0 24px rgba(59,130,246,0.22)',
                  filter: 'drop-shadow(0 0 12px rgba(139,92,246,0.28))',
                }}
              >
                {t}
              </div>
            ))}
          </div>

          <div
            ref={s8VignetteRef}
            style={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              background: 'radial-gradient(circle at center, transparent 35%, rgba(2,4,8,0.85) 100%)',
              opacity: 0,
            }}
          />

          <div
            style={{
              position: 'fixed',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none',
              zIndex: 120,
            }}
          >
            <span ref={endCursorRef} className="terminal-cursor" style={{ opacity: 0 }}>
              ░
            </span>
          </div>
          <div
            ref={endTitleRef}
            style={{
              position: 'fixed',
              bottom: '18%',
              left: 0,
              right: 0,
              textAlign: 'center',
              fontFamily: 'Inter, sans-serif',
              fontWeight: 200,
              fontSize: 14,
              color: '#475569',
              opacity: 0,
              zIndex: 121,
            }}
          >
            SCALE — Security Challenge and Learning Environment
          </div>
          <div ref={blackFinalRef} style={{ position: 'fixed', inset: 0, background: '#000', opacity: 0, zIndex: 122, pointerEvents: 'none' }} />
        </div>
      </div>
    </div>
  );
}
