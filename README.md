# Quick Unsplash Search

A lightweight, self-hosted web tool for searching Unsplash, previewing results in a visual grid, selecting images, and downloading them as a named zip file — all from your browser, running locally.

## Demo

<video src="demo.mp4" controls width="100%" title="Quick Unsplash Search — demo"></video>

---

> **Disclaimer:** This tool is an independent open-source project. It is not affiliated with, endorsed by, or officially connected to [Unsplash](https://unsplash.com) in any way. Use of the Unsplash API is subject to the [Unsplash API Terms](https://unsplash.com/api-terms).

---

## Why This Tool?

Most Unsplash workflows involve clicking through their website one image at a time, manually downloading files, and then renaming them. This tool solves that:

- **Batch download** — select as many images as you want from a 20-result grid and download them all in one zip
- **Custom naming convention** — set a file prefix (e.g. `mybrand_topic`) and every downloaded file is named consistently: `mybrand_topic_001.jpg`, `_002.jpg`, etc.
- **Paginate freely** — click **+ Load 20 more** to keep fetching additional results for the same query without losing your current selections
- **1080px resolution** — downloads at Unsplash's `regular` size (1080px wide), a practical balance between quality and file size
- **Landscape only** — all results are filtered to landscape orientation, ideal for blog headers, hero images, and social banners
- **No database, no cloud** — runs entirely on your machine. Nothing is stored anywhere.
- **Zero frontend dependencies** — uses Tailwind CDN and vanilla JS. No npm, no build step.

---

## Requirements

- Python 3.9+
- A free [Unsplash Developer account](https://unsplash.com/developers) to get an API key

---

## Installation

```bash
git clone https://github.com/callmefredcom/quickunsplashsearch.git
cd quickunsplashsearch
pip install -r requirements.txt
```

Copy the example environment file and add your Unsplash API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
UNSPLASH_KEY=your_unsplash_access_key_here
```

---

## Getting an Unsplash API Key

1. Go to [https://unsplash.com/developers](https://unsplash.com/developers)
2. Click **Your apps** → **New Application**
3. Accept the API guidelines
4. Your **Access Key** is the value you need — copy it into `.env`

> The free Unsplash API tier allows 50 requests per hour, which is more than enough for normal use.

---

## Usage

```bash
python3 unsplash_search.py
```

Your browser will open automatically at `http://localhost:5001`.

### Workflow

1. **Set your file prefix** in the left field — e.g. `mybrand_hero`. This prefix will be used in all downloaded filenames. It persists in your browser's localStorage between sessions.
2. **Type a search query** — texture/surface keywords work best for clean, usable results (e.g. `rough concrete surface`, `dark stone texture`, `grey cement abstract`). Avoid queries with people or specific places if you want versatile imagery.
3. **Click Search** — 20 landscape results appear as a grid.
4. **Click images to select them** — a tick appears on selected images. Use **Select all** / **Deselect all** as needed.
5. **Click + Load 20 more** to append the next page of results to the grid without losing your selections.
6. **Click Download** — the server fetches the full 1080px versions, packages them into a zip, and your browser downloads it automatically.

### Output

Files inside the zip are named:

```
{prefix}_{query}_{001}.jpg
{prefix}_{query}_{002}.jpg
...
```

The zip itself is named `{prefix}_{query}.zip`.

**Example:** prefix `mybrand_hero` + query `rough concrete surface` →

```
mybrand_hero_rough_concrete_surface.zip
  mybrand_hero_rough_concrete_surface_001.jpg
  mybrand_hero_rough_concrete_surface_002.jpg
  ...
```

---

## Unsplash API Guidelines

This tool complies with Unsplash API guidelines:

- The Unsplash download endpoint is triggered for every image before it is served (as required by the Unsplash API Terms)
- Images are attributed to their photographer in the hover overlay
- The API key is never exposed to the browser

Please review the full [Unsplash API Terms](https://unsplash.com/api-terms) before using this tool in a production or commercial context.

---

## License

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
