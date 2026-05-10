import json
from datetime import datetime

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.bootstrap import Container
from app.domain.file_type import FileType

_container: Container | None = None
_router = APIRouter()


def create_app(container: Container) -> FastAPI:
    global _container
    _container = container
    app = FastAPI(title="Memory Archive")
    app.include_router(_router)
    return app


def _slug(event_id: str) -> str:
    raw = event_id.replace("-", "")
    return raw[:4] + raw[-8:]


# ── HTML helpers ───────────────────────────────────────────────────────────────

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: system-ui, -apple-system, sans-serif; background: #f0f2f5;
       color: #1a1a2e; min-height: 100vh; }
a { color: inherit; }
.topbar { background: #1A669A; color: #fff; padding: 14px 24px;
          display: flex; align-items: center; gap: 14px; }
.topbar h1 { font-size: 1.2rem; font-weight: 700; letter-spacing: .3px; }
.topbar a { color: rgba(255,255,255,.75); text-decoration: none; }
.topbar a:hover { color: #fff; }
.topbar-icon { height: 32px; width: auto; flex-shrink: 0; }
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }

/* ── Index controls ── */
.controls { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 24px; align-items: center; }
.search-input { flex: 1; min-width: 180px; padding: 10px 14px; border: 1px solid #d0d4db;
                border-radius: 8px; font-size: .95rem; outline: none; }
.search-input:focus { border-color: #1A669A; }
select.year-sel { padding: 10px 14px; border: 1px solid #d0d4db; border-radius: 8px;
                  font-size: .95rem; background: #fff; outline: none; cursor: pointer; }
select.year-sel:focus { border-color: #1A669A; }
.sort-btn { padding: 10px 16px; border: 1px solid #d0d4db; border-radius: 8px;
            background: #fff; font-size: .95rem; cursor: pointer; user-select: none;
            transition: background .15s; display: flex; align-items: center; gap: 6px; }
.sort-btn:hover { background: #e0eaf5; }

/* ── Event cards ── */
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 16px; }
.card { display: block; background: #fff; border-radius: 12px; padding: 20px;
        text-decoration: none; color: inherit; box-shadow: 0 1px 4px rgba(0,0,0,.08);
        transition: box-shadow .2s, transform .15s; }
.card:hover { box-shadow: 0 6px 20px rgba(0,0,0,.12); transform: translateY(-2px); }
.card-name { font-size: 1.05rem; font-weight: 600; margin-bottom: 6px; }
.card-meta { font-size: .83rem; color: #7a7a9a; }
.empty { color: #9a9ab0; margin-top: 32px; text-align: center; font-size: .95rem; }
.hidden { display: none !important; }

/* ── Category folder ── */
.cat-folder { grid-column: 1 / -1; background: #e8edf2; border-radius: 14px; padding: 16px; }
.cat-folder-header { display: flex; align-items: center; gap: 10px; cursor: pointer;
                     user-select: none; padding: 2px 0; }
.cat-folder-header:hover .cat-folder-name { color: #1A669A; }
.cat-folder-name { font-size: 1.05rem; font-weight: 700; color: #1a1a2e; transition: color .15s; }
.cat-folder-count { font-size: .83rem; color: #7a7a9a; margin-left: auto; }
.cat-folder-arrow { font-size: .8rem; color: #7a7a9a; transition: transform .2s; margin-left: 4px; }
.cat-folder.open .cat-folder-arrow { transform: rotate(90deg); }
.cat-folder-inner { display: none; margin-top: 14px;
                    grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 12px; }
.cat-folder.open .cat-folder-inner { display: grid; }

/* ── Event page ── */
.event-header { margin-bottom: 20px; }
.event-title { font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }
.event-date { color: #7a7a9a; font-size: .9rem; margin-bottom: 12px; }
.event-desc { background: #fff; border-radius: 10px; padding: 14px 18px;
              font-size: .92rem; line-height: 1.6; color: #444; margin-bottom: 20px;
              border-left: 3px solid #1A669A; }

/* ── File type filter ── */
.type-filters { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.type-btn { padding: 7px 16px; border-radius: 20px; border: 2px solid #d0d4db;
            background: #fff; font-size: .88rem; cursor: pointer; user-select: none;
            transition: all .15s; font-weight: 500; }
.type-btn:hover { border-color: #1A669A; color: #1A669A; }
.type-btn.active { background: #1A669A; border-color: #1A669A; color: #fff; }

/* ── Media grid ── */
.media-grid { display: grid;
              grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 14px; }
.media-card { background: #fff; border-radius: 10px; overflow: hidden;
              box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.media-card a { display: block; }
.media-card img { width: 100%; aspect-ratio: 1; object-fit: cover; display: block;
                  transition: opacity .15s; }
.media-card a:hover img { opacity: .88; }
.media-card video { width: 100%; display: block; background: #000; }
.file-card { display: flex; align-items: center; gap: 12px; padding: 14px 16px;
             background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08);
             text-decoration: none; color: inherit; transition: box-shadow .15s; }
.file-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.12); }
.file-icon { font-size: 2rem; flex-shrink: 0; }
.file-info { overflow: hidden; }
.file-name { font-size: .88rem; font-weight: 500; white-space: nowrap;
             overflow: hidden; text-overflow: ellipsis; }
.file-type { font-size: .78rem; color: #9a9ab0; margin-top: 2px; }

/* ── Single file page ── */
.file-page { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 24px 0; }
.file-page img { max-width: 100%; max-height: 80vh; border-radius: 10px;
                 box-shadow: 0 4px 20px rgba(0,0,0,.15); }
.file-page video { max-width: 100%; border-radius: 10px; }
.download-btn { display: inline-flex; align-items: center; gap: 8px;
                padding: 12px 24px; background: #1A669A; color: #fff;
                border-radius: 8px; text-decoration: none; font-weight: 600;
                font-size: .95rem; transition: background .15s; }
.download-btn:hover { background: #155580; }
.back-btn { display: inline-flex; align-items: center; color: rgba(255,255,255,.75);
            text-decoration: none; font-size: 1.4rem; line-height: 1; }
.back-btn:hover { color: #fff; }
"""

_JS_INDEX = """
const searchInput = document.getElementById('search');
const yearSel = document.getElementById('year-sel');
const sortBtn = document.getElementById('sort-btn');
const grid = document.getElementById('cards-grid');
const emptyMsg = document.getElementById('empty-msg');
let sortAsc = false;

function normalize(s) { return s.toLowerCase().trim(); }

function makeCard(ev) {
  const a = document.createElement('a');
  a.className = 'card';
  a.href = '/' + ev.slug;
  a.innerHTML = '<div class="card-name">' + ev.name + '</div>'
    + '<div class="card-meta">' + ev.date_str + ' &bull; ' + ev.photos_count + ' file(s)</div>';
  return a;
}

function makeFolder(catName, events) {
  const div = document.createElement('div');
  div.className = 'cat-folder';
  const header = document.createElement('div');
  header.className = 'cat-folder-header';
  header.innerHTML = '<span class="cat-folder-name">\\uD83D\\uDCC1 ' + catName + '</span>'
    + '<span class="cat-folder-count">' + events.length + ' events</span>'
    + '<span class="cat-folder-arrow">&#9654;</span>';
  div.appendChild(header);
  const inner = document.createElement('div');
  inner.className = 'cat-folder-inner';
  events.forEach(ev => inner.appendChild(makeCard(ev)));
  div.appendChild(inner);
  header.addEventListener('click', () => div.classList.toggle('open'));
  return div;
}

function render() {
  const q = normalize(searchInput.value);
  const yr = yearSel.value;

  const visible = EVENTS.filter(ev => {
    const nameMatch = !q || normalize(ev.name).includes(q) || normalize(ev.cat_name).includes(q);
    const yearMatch = !yr || String(ev.year) === yr;
    return nameMatch && yearMatch;
  });

  grid.innerHTML = '';

  if (visible.length === 0) {
    emptyMsg.classList.remove('hidden');
    return;
  }
  emptyMsg.classList.add('hidden');

  const catMap = new Map();
  const noCat = [];
  visible.forEach(ev => {
    if (!ev.cat_id) { noCat.push(ev); return; }
    if (!catMap.has(ev.cat_id)) catMap.set(ev.cat_id, { name: ev.cat_name, events: [] });
    catMap.get(ev.cat_id).events.push(ev);
  });

  const items = [];
  noCat.forEach(ev => items.push({ ts: ev.ts, el: makeCard(ev) }));
  catMap.forEach(({ name, events }) => {
    if (events.length === 1) {
      items.push({ ts: events[0].ts, el: makeCard(events[0]) });
    } else {
      const ts = Math.max(...events.map(ev => ev.ts));
      items.push({ ts, el: makeFolder(name, events) });
    }
  });

  items.sort((a, b) => sortAsc ? a.ts - b.ts : b.ts - a.ts);
  items.forEach(i => grid.appendChild(i.el));
}

sortBtn.addEventListener('click', () => {
  sortAsc = !sortAsc;
  sortBtn.querySelector('.arrow').textContent = sortAsc ? '▲' : '▼';
  render();
});
searchInput.addEventListener('input', render);
yearSel.addEventListener('change', render);
render();
"""

_JS_EVENT = """
const btns = document.querySelectorAll('.type-btn');
const items = document.querySelectorAll('.media-item');
const activeTypes = new Set();

function refresh() {
  items.forEach(el => {
    const t = el.dataset.type;
    el.classList.toggle('hidden', activeTypes.size > 0 && !activeTypes.has(t));
  });
}

btns.forEach(btn => {
  btn.addEventListener('click', () => {
    const t = btn.dataset.type;
    if (activeTypes.has(t)) { activeTypes.delete(t); btn.classList.remove('active'); }
    else { activeTypes.add(t); btn.classList.add('active'); }
    refresh();
  });
});
"""


_ICON_SVG = """<svg class="topbar-icon" viewBox="0 0 229 159" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M20.354 55.5172V149C20.354 150.105 21.2494 151 22.354 151H114.5H206.646C207.751 151 208.646 150.105 208.646 149V55.5172M20.354 55.5172H114.5H208.646M20.354 55.5172H10C8.89543 55.5172 8 54.6218 8 53.5172V10C8 8.89543 8.89543 8 10 8H114.5H219C220.105 8 221 8.89543 221 10V53.5172C221 54.6218 220.105 55.5172 219 55.5172H208.646" stroke="white" stroke-width="15" stroke-linecap="round"/>
<path d="M97.6729 117.414H114.5H131.327" stroke="white" stroke-width="15" stroke-linecap="round"/>
<path d="M77 63C77 70.9565 80.9509 78.5871 87.9835 84.2132C95.0161 89.8393 104.554 93 114.5 93C124.446 93 133.984 89.8393 141.017 84.2132C148.049 78.5871 152 70.9565 152 63L133.675 63C133.675 67.0684 131.655 70.9702 128.059 73.847C124.463 76.7237 119.585 78.3399 114.5 78.3399C109.414 78.3399 104.537 76.7237 100.941 73.847C97.3453 70.9702 95.3251 67.0684 95.3251 63L77 63Z" fill="white"/>
</svg>"""


def _base_html(title: str, body: str, js: str = "", back_href: str | None = None) -> str:
    script = f"<script>{js}</script>" if js else ""
    if back_href:
        topbar_content = f'<a class="back-btn" href="{back_href}">‹</a><h1>{title}</h1>'
    else:
        topbar_content = f'{_ICON_SVG}<h1>{title}</h1>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{_CSS}</style>
</head>
<body>
<div class="topbar">
  {topbar_content}
</div>
<div class="container">
{body}
</div>
{script}
</body>
</html>"""


# ── Index page ─────────────────────────────────────────────────────────────────

@_router.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    events = await _container.event_service.get_all()
    categories = await _container.category_service.get_all()
    cat_map = {c.id: c.name for c in categories}

    current_year = datetime.now().year
    year_options = "".join(
        f'<option value="{y}">{y}</option>'
        for y in range(current_year, 1986, -1)
    )

    events_data = json.dumps([
        {
            "slug": _slug(e.id),
            "name": e.name,
            "year": e.date.year,
            "ts": int(e.date.timestamp()),
            "date_str": e.date.strftime("%d %b %Y"),
            "photos_count": e.photos_count,
            "cat_id": e.category_id or "",
            "cat_name": cat_map.get(e.category_id, "") if e.category_id else "",
        }
        for e in events
    ], ensure_ascii=False)

    controls = f"""
<div class="controls">
  <input id="search" class="search-input" type="text" placeholder="Search by name…">
  <select id="year-sel" class="year-sel">
    <option value="">All years</option>
    {year_options}
  </select>
  <button id="sort-btn" class="sort-btn">Date <span class="arrow">▼</span></button>
</div>"""

    body = (
        controls
        + '<div class="grid" id="cards-grid"></div>'
        + '<p class="empty hidden" id="empty-msg">No events found.</p>'
    )

    js = f"const EVENTS = {events_data};\n" + _JS_INDEX

    return HTMLResponse(_base_html("Memory Archive", body, js))


# ── Event page ─────────────────────────────────────────────────────────────────

@_router.get("/{slug}", response_class=HTMLResponse)
async def event_page(slug: str) -> HTMLResponse:
    events = await _container.event_service.get_all()
    ev = next((e for e in events if _slug(e.id) == slug), None)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")

    media_files = await _container.media_file_service.get_visible_for_event(ev.id)

    date_str = ev.date.strftime("%d %b %Y")

    desc_html = ""
    if ev.description:
        desc_html = f'<div class="event-desc">{ev.description}</div>'

    type_filter_html = """
<div class="type-filters">
  <button class="type-btn" data-type="IMAGE">🖼 Images</button>
  <button class="type-btn" data-type="VIDEO">🎬 Videos</button>
  <button class="type-btn" data-type="FILE">📄 Files</button>
</div>"""

    if not media_files:
        media_html = "<p class='empty'>No files uploaded yet.</p>"
    else:
        _type_order = {FileType.FILE: 0, FileType.IMAGE: 1, FileType.VIDEO: 2}
        media_files_sorted = sorted(media_files, key=lambda f: _type_order[f.type])
        items = []
        for mf in media_files_sorted:
            s3_key = f"{ev.images_folder}/{mf.file_name}"
            url = await _container.s3_client.presigned_url(s3_key, expires_seconds=86400)
            display = mf.original_name or mf.file_name
            items.append(_render_media_item(display, mf.type, url, slug, mf.id))
        media_html = f'<div class="media-grid">{"".join(items)}</div>'

    header = f"""
<div class="event-header">
  <div class="event-title">{ev.name}</div>
  <div class="event-date">{date_str}</div>
</div>
{desc_html}"""

    body = header + type_filter_html + media_html

    return HTMLResponse(_base_html(ev.name, body, _JS_EVENT, back_href="/"))


# ── Single file page ───────────────────────────────────────────────────────────

@_router.get("/{slug}/{file_id}", response_class=HTMLResponse)
async def file_page(slug: str, file_id: str) -> HTMLResponse:
    events = await _container.event_service.get_all()
    ev = next((e for e in events if _slug(e.id) == slug), None)
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")

    mf = await _container.media_file_service.get_by_id(file_id)
    if mf is None or mf.event_id != ev.id:
        raise HTTPException(status_code=404, detail="File not found")

    s3_key = f"{ev.images_folder}/{mf.file_name}"
    url = await _container.s3_client.presigned_url(s3_key, expires_seconds=86400)
    display = mf.original_name or mf.file_name
    ext = display.rsplit(".", 1)[-1].lower() if "." in display else ""

    if mf.type == FileType.IMAGE:
        media_html = f'<img src="{url}" alt="{display}">'
    elif mf.type == FileType.VIDEO:
        media_html = f'<video src="{url}" controls></video>'
    else:
        icon = "📄" if ext not in ("zip", "gz", "tar") else "🗜"
        media_html = f'<span style="font-size:4rem">{icon}</span>'

    body = f"""
<div class="file-page">
  {media_html}
  <a class="download-btn" href="{url}" download="{display}">⬇ Download</a>
</div>"""

    return HTMLResponse(_base_html(display, body, back_href=f"/{slug}"))


def _render_media_item(filename: str, file_type: FileType, url: str, slug: str, file_id: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    t = file_type.value
    file_href = f"/{slug}/{file_id}"

    if file_type == FileType.IMAGE:
        inner = f'<a href="{file_href}"><img src="{url}" alt="{filename}" loading="lazy"></a>'
        return f'<div class="media-card media-item" data-type="{t}">{inner}</div>'

    if file_type == FileType.VIDEO:
        inner = f'<video src="{url}" controls preload="metadata"></video>'
        return f'<div class="media-card media-item" data-type="{t}">{inner}</div>'

    # Generic file
    icon = "📄" if ext not in ("zip", "gz", "tar") else "🗜"
    return (
        f'<a class="file-card media-item" data-type="{t}" href="{url}" '
        f'target="_blank" download="{filename}">'
        f'<div class="file-icon">{icon}</div>'
        f'<div class="file-info">'
        f'<div class="file-name">{filename}</div>'
        f'<div class="file-type">{ext.upper() if ext else "FILE"}</div>'
        f'</div></a>'
    )
