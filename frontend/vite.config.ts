import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import type { Connect } from 'vite'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

/** Serve tutorial MP4s from repo `Web-Videos` in dev (Docker: mount to `./web-videos`). */
function resolveWebVideosRoot(): string | null {
  const candidates = [
    path.join(__dirname, 'web-videos'),
    path.resolve(__dirname, '..', 'Web-Videos'),
  ]
  for (const dir of candidates) {
    try {
      if (fs.existsSync(dir) && fs.statSync(dir).isDirectory()) {
        return dir
      }
    } catch {
      /* ignore */
    }
  }
  return null
}

function challengeVideosMiddleware(): Connect.NextHandleFunction {
  return (req, res, next) => {
    if (!req.url?.startsWith('/challenge-videos/')) {
      next()
      return
    }
    const root = resolveWebVideosRoot()
    if (!root) {
      next()
      return
    }
    const raw = req.url.replace(/^\/challenge-videos\//, '').split('?')[0] || ''
    let name: string
    try {
      name = decodeURIComponent(raw)
    } catch {
      next()
      return
    }
    const safe = path.basename(name)
    if (safe !== name || !safe.toLowerCase().endsWith('.mp4')) {
      next()
      return
    }
    const file = path.join(root, safe)
    if (!file.startsWith(root)) {
      next()
      return
    }
    fs.stat(file, (err, st) => {
      if (err || !st.isFile()) {
        next()
        return
      }
      const size = st.size
      const range = typeof req.headers.range === 'string' ? req.headers.range : undefined
      if (range) {
        const m = /^bytes=(\d*)-(\d*)$/.exec(range)
        if (!m) {
          next()
          return
        }
        let start = m[1] ? parseInt(m[1], 10) : 0
        let end = m[2] ? parseInt(m[2], 10) : size - 1
        if (Number.isNaN(start) || Number.isNaN(end) || start >= size || end >= size || start > end) {
          res.statusCode = 416
          res.setHeader('Content-Range', `bytes */${size}`)
          res.end()
          return
        }
        res.statusCode = 206
        res.setHeader('Content-Type', 'video/mp4')
        res.setHeader('Accept-Ranges', 'bytes')
        res.setHeader('Content-Range', `bytes ${start}-${end}/${size}`)
        res.setHeader('Content-Length', String(end - start + 1))
        fs.createReadStream(file, { start, end }).pipe(res)
        return
      }
      res.setHeader('Content-Type', 'video/mp4')
      res.setHeader('Accept-Ranges', 'bytes')
      res.setHeader('Content-Length', String(size))
      fs.createReadStream(file).pipe(res)
    })
  }
}

function webVideosDevPlugin() {
  return {
    name: 'serve-challenge-tutorial-videos',
    configureServer(server: { middlewares: Connect.Server }) {
      server.middlewares.use(challengeVideosMiddleware())
    },
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), webVideosDevPlugin()],
})
