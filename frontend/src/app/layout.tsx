import type { Metadata } from "next";
import { AuthProvider } from "@/contexts/AuthContext";
import { ToastProvider } from "@/components/ui/Toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "序话Story - 一句话，一个完整故事",
  description: "AI驱动的条漫和短视频创作平台。输入你的创意，获得可发布的完整作品。",
  keywords: ["AI创作", "条漫", "短视频", "故事创作", "AIGC"],
  authors: [{ name: "序话Story" }],
  openGraph: {
    title: "序话Story - 一句话，一个完整故事",
    description: "AI驱动的条漫和短视频创作平台",
    type: "website",
    locale: "zh_CN",
  },
};

// [A2-frontend] Client-side console proxy script
// Captures ALL browser console events and forwards to backend /api/_client_log
// Full capture: no throttle, no sampling, no batching — every event is POSTed immediately
// Covers: console.error / console.warn / window.onerror / window.unhandledrejection /
//         React strict mode warnings / Next.js hydration warnings / network fetch failures
//
// NEXT_PUBLIC_API_URL is expanded at build time (Server Component context) via template literal.
// Project convention: NEXT_PUBLIC_API_URL already INCLUDES the /api suffix (see lib/api.ts:13,
// Dockerfile.frontend:11, s/[token]/page.tsx:14, ContactContent.tsx:38). So we append only '/_client_log'.
// JSON.stringify ensures proper quoting + escaping of the value before injection into the IIFE string.
// The browser IIFE never sees process.env — it only sees the already-resolved string value.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';
// Wave 13 #5: bump this when the proxy script changes so we can confirm in logs which
// version a browser actually loaded (test28 lesson: code审查≠实测生效 — old script ran in a
// stale tab so the routine-404 classification never fired). The version is POSTed once on load.
const CLIENT_LOG_PROXY_VERSION = "w13-404-v2";
const CLIENT_LOG_PROXY_SCRIPT = `
(function() {
  var ENDPOINT = ${JSON.stringify(API_BASE)} + '/_client_log';
  var PROXY_VERSION = ${JSON.stringify(CLIENT_LOG_PROXY_VERSION)};

  function serializeArg(a) {
    if (a === null) return 'null';
    if (a === undefined) return 'undefined';
    if (a instanceof Error) {
      return (a.stack || (a.name + ': ' + a.message)) || String(a);
    }
    if (typeof a === 'object') {
      try { return JSON.stringify(a); } catch(_) { return String(a); }
    }
    return String(a);
  }

  function post(payload) {
    try {
      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }).catch(function() {});
    } catch(_) {}
  }

  // Intercept console.error (covers React strict mode warnings + general errors)
  var origError = console.error;
  console.error = function() {
    var args = Array.prototype.slice.call(arguments);
    post({
      level: 'error',
      ts: new Date().toISOString(),
      args: args.map(serializeArg),
      url: location.href
    });
    origError.apply(console, args);
  };

  // Intercept console.warn (covers Next.js hydration mismatch warnings + general warnings)
  var origWarn = console.warn;
  console.warn = function() {
    var args = Array.prototype.slice.call(arguments);
    post({
      level: 'warn',
      ts: new Date().toISOString(),
      args: args.map(serializeArg),
      url: location.href
    });
    origWarn.apply(console, args);
  };

  // Capture global uncaught errors (window.onerror + addEventListener fallback)
  // window.onerror fires for JS errors and gives message/source/line/col/error directly.
  // addEventListener('error', capture:true) fires for both JS errors AND media/resource errors.
  // We use BOTH: window.onerror for JS errors (has full stack), listener for resource errors.
  window.onerror = function(message, source, line, col, error) {
    var stack = '';
    if (error && error.stack) {
      stack = error.stack;
    } else if (error) {
      stack = String(error);
    }
    post({
      level: 'uncaught',
      ts: new Date().toISOString(),
      args: [String(message || 'Unknown error')],
      url: location.href,
      source: source || '',
      line: line || 0,
      col: col || 0,
      stack: stack
    });
    // Return false: do NOT suppress the error (let browser also log it normally)
    return false;
  };

  // Capture resource/media errors (audio/video/img load failures) via capture-phase listener.
  // These fire as ErrorEvent on the element, bubble up to window — no JS stack available.
  // e.filename/lineno/colno are all empty for resource errors; detect via e.target.
  window.addEventListener('error', function(e) {
    // JS errors are now handled by window.onerror above — skip to avoid double logging.
    // Resource errors have no e.error (Error object) — only fire handler for those.
    if (e.error) {
      // This is a JS error already caught by window.onerror — skip.
      return;
    }
    // Resource/media error: extract element info for diagnostics.
    var target = e.target;
    var targetInfo = '';
    if (target && target !== window) {
      var tagName = (target.tagName || '').toLowerCase();
      var src = target.src || target.href || target.currentSrc || '';
      var mediaError = target.error; // HTMLMediaElement.error (MediaError object)
      var mediaCode = mediaError ? mediaError.code : null;
      var mediaMsg = mediaError ? (mediaError.message || '') : '';
      targetInfo = tagName + (src ? ' src=' + src : '') +
        (mediaCode ? ' MediaError.code=' + mediaCode + ' msg=' + mediaMsg : '');
    }
    post({
      level: 'uncaught',
      ts: new Date().toISOString(),
      args: [e.message || ('Resource load error: ' + targetInfo) || 'Unknown error'],
      url: location.href,
      source: e.filename || (target && (target.src || target.href)) || '',
      line: e.lineno || 0,
      col: e.colno || 0,
      stack: '',
      target_info: targetInfo
    });
  }, true);

  // Capture unhandled Promise rejections
  window.addEventListener('unhandledrejection', function(e) {
    var reason = e.reason;
    var reasonStr;
    var stack = '';
    if (reason instanceof Error) {
      stack = reason.stack || '';
      reasonStr = reason.stack || (reason.name + ': ' + reason.message);
    } else if (reason && typeof reason === 'object') {
      // Could be a native Event object (e.g. MediaError event rejected in a Promise).
      // Stringify but also capture type/isTrusted for diagnostics.
      var eventType = reason.type || '';
      var isTrusted = reason.isTrusted;
      var targetSrc = (reason.target && (reason.target.src || reason.target.currentSrc)) || '';
      var mediaError = (reason.target && reason.target.error) ? reason.target.error : null;
      var mediaCode = mediaError ? mediaError.code : null;
      var mediaMsg = mediaError ? (mediaError.message || '') : '';
      reasonStr = 'Event{type=' + eventType +
        (isTrusted !== undefined ? ',isTrusted=' + isTrusted : '') +
        (targetSrc ? ',targetSrc=' + targetSrc : '') +
        (mediaCode ? ',MediaError.code=' + mediaCode + ',msg=' + mediaMsg : '') +
        '}';
    } else {
      reasonStr = String(reason);
    }
    post({
      level: 'promise-reject',
      ts: new Date().toISOString(),
      args: [reasonStr],
      url: location.href,
      stack: stack
    });
  });

  // Capture network failures: wrap fetch to detect non-2xx/3xx responses
  var origFetch = window.fetch;
  window.fetch = function(input, init) {
    var url = typeof input === 'string' ? input : (input && input.url) || String(input);
    // Do NOT intercept calls to our own logging endpoint (avoid infinite loop)
    if (url && url.indexOf('/_client_log') !== -1) {
      return origFetch.apply(window, arguments);
    }
    return origFetch.apply(window, arguments).then(function(response) {
      if (!response.ok && response.status >= 400) {
        // P3-3 (Wave 12): the create flow polls chapter endpoints that return 404 BY DESIGN
        // before the chapter exists (pre-confirm-outline) or before a stage's data is written
        // (pre-generation). The application code catches these as routine (console.warn), but
        // this global fetch wrapper would otherwise log every 404 as level:'network' — mixing
        // expected 404s with genuine network failures. We classify by-design pre-confirm 404s
        // as level:'routine-404' so monitoring de-noise treats them consistently.
        // Endpoints: /chapters/{n}/status | /story | /storyboard | /bgm | /scene-references
        //
        // Wave 13 #5 ROOT CAUSE FIX: this used to be a regex literal that tested the url. But
        // CLIENT_LOG_PROXY_SCRIPT is a JS template literal, so every backslash in that regex was
        // consumed by template-string escaping at construction time (backslash-d becomes d,
        // backslash-slash becomes slash, etc). The emitted browser script started with a double
        // slash which turned the whole assignment into a line comment, leaving isRoutine404
        // undefined so ALL chapter 404s were logged as network. That is exactly why test28 showed
        // 0 routine-404 + 18 network despite the Wave B fix.
        // Rewritten with backslash-free plain-string checks (no regex literal, nothing to mangle).
        var isRoutine404 = false;
        if (response.status === 404 && url.indexOf('/chapters/') !== -1) {
          var routineSuffixes = ['/status', '/story', '/storyboard', '/bgm', '/scene-references'];
          // strip query string so '/status?x=1' still matches the '/status' suffix
          var qIdx = url.indexOf('?');
          var pathOnly = qIdx === -1 ? url : url.slice(0, qIdx);
          for (var ri = 0; ri < routineSuffixes.length; ri++) {
            var suf = routineSuffixes[ri];
            if (pathOnly.length >= suf.length && pathOnly.slice(pathOnly.length - suf.length) === suf) {
              isRoutine404 = true;
              break;
            }
          }
        }
        post({
          level: isRoutine404 ? 'routine-404' : 'network',
          ts: new Date().toISOString(),
          args: ['HTTP ' + response.status + ' ' + response.statusText + ' — ' + url],
          url: location.href,
          source: url
        });
      }
      return response;
    }).catch(function(err) {
      post({
        level: 'network',
        ts: new Date().toISOString(),
        args: ['fetch failed: ' + serializeArg(err) + ' — ' + url],
        url: location.href,
        source: url
      });
      throw err;
    });
  };

  // Wave 13 #5: announce which proxy version loaded — lets us confirm in client.log that a
  // browser is running the routine-404 build (not a stale tab). Fires once per page load.
  post({
    level: 'proxy-init',
    ts: new Date().toISOString(),
    args: ['client-log-proxy loaded version=' + PROXY_VERSION],
    url: location.href
  });
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {/* [A2-frontend] Console proxy: captures all browser errors/warnings to backend logs/client.log */}
        <script dangerouslySetInnerHTML={{ __html: CLIENT_LOG_PROXY_SCRIPT }} />
        <AuthProvider>
          <ToastProvider>
            {children}
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
