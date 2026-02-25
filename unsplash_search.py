#!/usr/bin/env python3
"""
unsplash_search.py — Quick Unsplash image search, preview, and batch download.

Usage:
    python3 unsplash_search.py
    → Opens http://localhost:5001

Requires UNSPLASH_KEY in .env
Files are named: {prefix}_{query}_{001}.jpg, _002.jpg, etc.
Images downloaded at 1080px (regular) resolution.
"""

import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request, send_file

load_dotenv()

UNSPLASH_KEY = os.getenv('UNSPLASH_KEY')
if not UNSPLASH_KEY:
    sys.exit('[ERROR] UNSPLASH_KEY not found in .env — add it and restart.')

PORT = 5001

app = Flask(__name__)

# ── HTML Template ─────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Quick Unsplash Search</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .photo-card input[type=checkbox]:checked ~ img { opacity: 55%; }
    .photo-card input[type=checkbox]:checked ~ .tick { display: flex; }
    .tick { display: none; }
    .photo-card:hover .credit { opacity: 1; }
  </style>
</head>
<body class="bg-zinc-950 text-zinc-100 min-h-screen font-sans">

  <!-- Header -->
  <div class="border-b border-zinc-800 px-6 py-4 flex items-center gap-3">
    <span class="text-white font-semibold tracking-tight">Quick Unsplash Search</span>
    <span class="text-zinc-400 text-xs">· landscape · 1080px</span>
  </div>

  <!-- Search bar -->
  <div class="max-w-4xl mx-auto px-6 pt-10 pb-6 space-y-4">

    <!-- Prefix + query on one row -->
    <div class="flex gap-2 items-center">
      <div class="flex items-center gap-1">
        <span class="text-zinc-300 text-xs whitespace-nowrap">File prefix</span>
        <input id="prefixInput" type="text" placeholder="yoursite_topic"
          class="w-36 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-500 text-sm font-mono">
      </div>
      <span class="text-zinc-700 text-lg select-none">_</span>
      <input id="queryInput" type="text" placeholder="e.g. rough cement surface abstract"
        class="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-400 text-sm"
        onkeydown="if(event.key==='Enter') doSearch()">
      <button onclick="doSearch()"
        class="bg-white text-zinc-900 px-6 py-3 rounded-lg font-medium text-sm hover:bg-zinc-200 transition-colors whitespace-nowrap">
        Search
      </button>
    </div>

    <p class="text-zinc-400 text-xs">
      Files will be named <span id="namePreview" class="text-zinc-400 font-mono">yoursite_topic_query_001.jpg</span> …
      
    </p>
  </div>

  <!-- Toolbar -->
  <div id="toolbar" class="hidden max-w-7xl mx-auto px-6 pb-4 flex items-center justify-between">
    <div class="flex items-center gap-4">
      <span id="resultCount" class="text-zinc-400 text-sm"></span>
      <span id="pageIndicator" class="text-zinc-400 text-xs"></span>
      <button onclick="selectAll()" class="text-xs text-zinc-400 hover:text-white underline underline-offset-2">Select all</button>
      <button onclick="deselectAll()" class="text-xs text-zinc-400 hover:text-white underline underline-offset-2">Deselect all</button>
    </div>
    <button onclick="downloadSelected()"
      class="bg-orange-500 hover:bg-orange-400 text-white px-5 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
      </svg>
      <span id="dlLabel">Download selected</span>
    </button>
  </div>

  <!-- Loading -->
  <div id="loading" class="hidden text-center py-20 text-zinc-500 text-sm">Searching Unsplash…</div>

  <!-- Error -->
  <div id="error" class="hidden max-w-3xl mx-auto px-6 py-6 text-red-400 text-sm rounded-lg"></div>

  <!-- Grid -->
  <div id="grid" class="max-w-7xl mx-auto px-6 pb-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3"></div>

  <!-- More button -->
  <div id="moreWrap" class="hidden text-center pb-16">
    <button onclick="loadMore()"
      class="border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-white px-8 py-3 rounded-lg text-sm font-medium transition-colors">
      + Load 20 more
    </button>
    <p id="moreLoading" class="hidden text-zinc-500 text-sm mt-3">Fetching next page…</p>
  </div>

  <!-- Download overlay -->
  <div id="dlOverlay" class="hidden fixed inset-0 bg-black/75 flex items-center justify-center z-50">
    <div class="bg-zinc-900 border border-zinc-700 rounded-xl px-10 py-8 text-center">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-400 mx-auto mb-4"></div>
      <p class="text-white font-medium">Packaging zip…</p>
      <p id="dlProgress" class="text-zinc-400 text-sm mt-1">Downloading images from Unsplash</p>
    </div>
  </div>

<script>
  let currentQuery = '';
  let currentPage  = 1;
  let allPhotos    = [];   // accumulates across pages for correct numbering

  // Persist prefix in localStorage
  const prefixEl = document.getElementById('prefixInput');
  prefixEl.value = localStorage.getItem('unsplash_prefix') || '';
  prefixEl.addEventListener('input', () => {
    localStorage.setItem('unsplash_prefix', prefixEl.value.trim());
    updateNamePreview();
  });

  document.getElementById('queryInput').addEventListener('input', updateNamePreview);
  updateNamePreview();

  function getPrefix() {
    const raw = prefixEl.value.trim();
    return raw ? slugify(raw) : 'image';
  }

  function slugify(s) {
    return s.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  function updateNamePreview() {
    const prefix = getPrefix();
    const q      = slugify(document.getElementById('queryInput').value.trim() || 'query');
    document.getElementById('namePreview').textContent = `${prefix}_${q}_001.jpg`;
  }

  // ── Search (new query resets grid) ──────────────────────────────────────────

  async function doSearch() {
    const q = document.getElementById('queryInput').value.trim();
    if (!q) return;
    currentQuery = q;
    currentPage  = 1;
    allPhotos    = [];

    document.getElementById('grid').innerHTML = '';
    document.getElementById('toolbar').classList.add('hidden');
    document.getElementById('moreWrap').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');

    await fetchPage(1, true);
  }

  // ── Load more (append) ───────────────────────────────────────────────────────

  async function loadMore() {
    document.getElementById('moreLoading').classList.remove('hidden');
    document.getElementById('moreWrap').querySelector('button').classList.add('hidden');
    currentPage++;
    await fetchPage(currentPage, false);
    document.getElementById('moreLoading').classList.add('hidden');
    document.getElementById('moreWrap').querySelector('button').classList.remove('hidden');
  }

  // ── Core fetch ───────────────────────────────────────────────────────────────

  async function fetchPage(page, replace) {
    try {
      const resp = await fetch('/search?' + new URLSearchParams({ q: currentQuery, page }));
      const data = await resp.json();
      document.getElementById('loading').classList.add('hidden');

      if (data.error) {
        document.getElementById('error').textContent = 'Error: ' + data.error;
        document.getElementById('error').classList.remove('hidden');
        return;
      }

      const startIndex = allPhotos.length;  // for correct numbering
      allPhotos = allPhotos.concat(data.photos);

      if (replace) {
        document.getElementById('grid').innerHTML = '';
      }

      appendToGrid(data.photos, startIndex);

      document.getElementById('resultCount').textContent =
        allPhotos.length + ' image' + (allPhotos.length !== 1 ? 's' : '') + ' loaded';
      document.getElementById('pageIndicator').textContent = `page ${page}`;
      document.getElementById('toolbar').classList.remove('hidden');
      document.getElementById('moreWrap').classList.remove('hidden');
      updateDlLabel();
    } catch (e) {
      document.getElementById('loading').classList.add('hidden');
      document.getElementById('error').textContent = 'Request failed: ' + e.message;
      document.getElementById('error').classList.remove('hidden');
    }
  }

  // ── Grid rendering ───────────────────────────────────────────────────────────

  function appendToGrid(photos, startIndex) {
    const grid = document.getElementById('grid');
    photos.forEach((p, i) => {
      const globalIndex = startIndex + i;
      const card = document.createElement('label');
      card.className = 'photo-card relative cursor-pointer group block rounded-lg overflow-hidden bg-zinc-900';
      card.innerHTML = `
        <input type="checkbox" class="absolute top-2 left-2 z-20 w-4 h-4 accent-orange-500" data-index="${globalIndex}">
        <img src="${esc(p.thumb)}" alt="${esc(p.alt)}"
          class="w-full aspect-video object-cover transition-opacity duration-150 block">
        <div class="tick absolute top-2 right-2 z-20 bg-orange-500 rounded-full w-6 h-6 items-center justify-center">
          <svg class="w-4 h-4 text-white m-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
          </svg>
        </div>
        <div class="credit absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-2 py-2 opacity-0 transition-opacity pointer-events-none">
          <p class="text-white text-xs truncate">${esc(p.photographer)}</p>
        </div>`;
      card.querySelector('input').addEventListener('change', updateDlLabel);
      grid.appendChild(card);
    });
  }

  function esc(s) {
    return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── Selection helpers ────────────────────────────────────────────────────────

  function getSelected() {
    return [...document.querySelectorAll('#grid input[type=checkbox]:checked')]
      .map(cb => parseInt(cb.dataset.index));
  }

  function updateDlLabel() {
    const n = getSelected().length;
    document.getElementById('dlLabel').textContent =
      n ? `Download ${n} image${n > 1 ? 's' : ''}` : 'Download selected';
  }

  function selectAll()   { document.querySelectorAll('#grid input[type=checkbox]').forEach(c => c.checked = true);  updateDlLabel(); }
  function deselectAll() { document.querySelectorAll('#grid input[type=checkbox]').forEach(c => c.checked = false); updateDlLabel(); }

  // ── Download ─────────────────────────────────────────────────────────────────

  async function downloadSelected() {
    const indices = getSelected();
    if (!indices.length) { alert('Select at least one image first.'); return; }

    const prefix   = getPrefix();
    const qSlug    = slugify(currentQuery);
    const selected = indices.map((gi, pos) => ({
      download_url:      allPhotos[gi].download_url,
      download_location: allPhotos[gi].download_location,
      position:          pos + 1,   // sequential numbering within selection
    }));

    document.getElementById('dlOverlay').classList.remove('hidden');
    document.getElementById('dlProgress').textContent =
      `Packaging ${selected.length} image${selected.length > 1 ? 's' : ''}…`;

    try {
      const resp = await fetch('/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prefix, query: currentQuery, photos: selected }),
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        alert('Download failed: ' + (err.error || resp.statusText));
        return;
      }

      const blob = await resp.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `${prefix}_${qSlug}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Download error: ' + e.message);
    } finally {
      document.getElementById('dlOverlay').classList.add('hidden');
    }
  }
</script>
</body>
</html>"""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    page  = max(1, int(request.args.get('page', 1)))
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    params = urllib.parse.urlencode({
        'query':       query,
        'orientation': 'landscape',
        'per_page':    20,
        'page':        page,
        'client_id':   UNSPLASH_KEY,
    })
    req = urllib.request.Request(
        f"https://api.unsplash.com/search/photos?{params}",
        headers={'Accept-Version': 'v1'}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    photos = [
        {
            'thumb':             p['urls']['small'],    # 400px for preview
            'download_url':      p['urls']['regular'],  # 1080px for download
            'download_location': p['links']['download_location'],
            'alt':               p.get('alt_description') or query,
            'photographer':      p['user']['name'],
        }
        for p in data.get('results', [])
    ]
    return jsonify({'photos': photos, 'query': query, 'page': page})


@app.route('/download', methods=['POST'])
def download():
    data   = request.get_json()
    prefix = data.get('prefix', 'image').strip() or 'image'
    query  = data.get('query', 'search')
    photos = data.get('photos', [])

    if not photos:
        return jsonify({'error': 'No photos selected'}), 400

    q_slug = query.lower().strip()
    q_slug = ''.join(c if c.isalnum() else '_' for c in q_slug)
    q_slug = '_'.join(p for p in q_slug.split('_') if p)

    zip_buf   = io.BytesIO()
    downloaded = 0

    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            pos = photo.get('position', downloaded + 1)

            # Unsplash ToS: trigger download endpoint
            try:
                trigger = f"{photo['download_location']}&client_id={UNSPLASH_KEY}"
                urllib.request.urlopen(trigger, timeout=10)
            except Exception:
                pass

            # Download 1080px image
            try:
                req = urllib.request.Request(
                    photo['download_url'],
                    headers={'User-Agent': 'QuickUnsplashSearch/1.0'}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    img_bytes = resp.read()

                filename = f"{prefix}_{q_slug}_{pos:03d}.jpg"
                zf.writestr(filename, img_bytes)
                downloaded += 1
                print(f"  [{pos:03d}] {filename}  ({len(img_bytes)//1024} KB)")
            except Exception as e:
                print(f"  [WARN] Failed image #{pos}: {e}")

    if downloaded == 0:
        return jsonify({'error': 'All image downloads failed'}), 500

    zip_buf.seek(0)
    zip_name = f"{prefix}_{q_slug}.zip"
    print(f"\n  Done — {downloaded} image(s) → {zip_name}\n")

    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_name,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import webbrowser
    print(f"\n  Quick Unsplash Search → http://localhost:{PORT}\n")
    webbrowser.open(f'http://localhost:{PORT}')
    app.run(port=PORT, debug=False)
