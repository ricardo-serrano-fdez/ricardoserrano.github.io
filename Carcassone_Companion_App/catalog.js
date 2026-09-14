const tileIds = ['IMG_2949', 'IMG_2950', 'IMG_2951', 'IMG_2952', 'IMG_2953', 'IMG_2954', 'IMG_2955', 'IMG_2956', 'IMG_2957', 'IMG_2958', 'IMG_2959', 'IMG_2960', 'IMG_2961', 'IMG_2962', 'IMG_2963', 'IMG_2964', 'IMG_2965', 'IMG_2966', 'IMG_2967', 'IMG_2968', 'IMG_2969', 'IMG_2970', 'IMG_2971', 'IMG_2972', 'IMG_2973', 'IMG_2974', 'IMG_2975', 'IMG_2976', 'IMG_2977', 'IMG_2978', 'IMG_2979', 'IMG_2980', 'IMG_2981', 'IMG_2982', 'IMG_2983', 'IMG_2984', 'IMG_2985', 'IMG_2986', 'IMG_2987', 'IMG_2988', 'IMG_2989', 'IMG_2990', 'IMG_2991', 'IMG_2992', 'IMG_2993', 'IMG_2994', 'IMG_2995', 'IMG_2996', 'IMG_2997', 'IMG_2998', 'IMG_2999', 'IMG_3001', 'IMG_3002', 'IMG_3003', 'IMG_3004', 'IMG_3005', 'IMG_3006', 'IMG_3007', 'IMG_3008', 'IMG_3009', 'IMG_3010', 'IMG_3011', 'IMG_3012', 'IMG_3014', 'IMG_3015', 'IMG_3016', 'IMG_3017', 'IMG_3018', 'IMG_3019', 'IMG_3020', 'IMG_3021', 'IMG_3022'];
const catalog = Object.fromEntries(tileIds.map((id) => [id, { id, image: `tile_library_z-man_2014/crops/${id}.jpg` }]));
let currentId = tileIds[0];
let extractionData = window.tileAnalysis
  ? Object.fromEntries(window.tileAnalysis.tiles.map((tile) => [tile.id, tile]))
  : null;
const $ = (selector) => document.querySelector(selector);

async function loadExtractionData() {
  if (extractionData) {
    renderExtraction();
    return;
  }
  try {
    const response = await fetch('tile_library_z-man_2014/tile_analysis.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    extractionData = Object.fromEntries(data.tiles.map((tile) => [tile.id, tile]));
    renderExtraction();
  } catch (error) {
    $('#extraction-status').textContent = 'Extracted analysis could not be loaded.';
    console.error('Unable to load tile analysis', error);
  }
}

function renderExtraction() {
  const tile = extractionData?.[currentId];
  if (!tile) return;
  $('#extraction-status').textContent = `${tile.id} · ${tile.mask_size.join(' × ')} mask`;
  $('#extracted-crop').src = catalog[currentId].image;
  $('#extracted-mask').src = `tile_library_z-man_2014/masks/${currentId}.png`;
  const edgeReview = $('#extracted-edges');
  const connectionOverlay = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  connectionOverlay.id = 'connection-overlay';
  connectionOverlay.setAttribute('aria-hidden', 'true');
  const edgeItems = tile.edges.map((edge) => {
    const item = document.createElement('div');
    item.className = `edge-chip segment-${edge.segment}`; item.dataset.terrain = edge.terrain;
    item.title = `${edge.confidence * 100}% confidence`;
    item.innerHTML = `<strong>Segment ${edge.segment}</strong><span>${edge.terrain}</span>`;
    return item;
  });
  edgeReview.replaceChildren(connectionOverlay, ...edgeItems);
  requestAnimationFrame(() => renderConnectionLines(tile.connections));
  $('#extracted-connections').replaceChildren(...tile.connections.map((connection) => {
    const item = document.createElement('li');
    const segments = connection.edge_segments.length ? connection.edge_segments.join(', ') : 'interior only';
    item.textContent = `${connection.terrain}: segments ${segments}`;
    return item;
  }));
  $('#extracted-features').replaceChildren(...Object.entries(tile.features).map(([name, present]) => {
    const item = document.createElement('span');
    item.className = `feature-pill ${present ? 'present' : ''}`;
    item.textContent = `${name}: ${present ? 'yes' : 'no'}`;
    return item;
  }));
}

function renderConnectionLines(connections) {
  const container = $('#extracted-edges');
  const overlay = $('#connection-overlay');
  if (!container || !overlay) return;
  const containerBounds = container.getBoundingClientRect();
  overlay.setAttribute('viewBox', `0 0 ${containerBounds.width} ${containerBounds.height}`);
  overlay.replaceChildren();
  const colors = { city: '#a43e32', road: '#2e6652', field: '#79a84b' };
  connections.filter((connection) => connection.edge_segments.length > 1).forEach((connection) => {
    const points = connection.edge_segments.map((segment) => {
      const card = container.querySelector(`.segment-${segment}`);
      if (!card) return null;
      const bounds = card.getBoundingClientRect();
      return {
        x: bounds.left - containerBounds.left + bounds.width / 2,
        y: bounds.top - containerBounds.top + bounds.height / 2,
      };
    }).filter(Boolean);
    if (points.length < 2) return;
    const hub = points.reduce((sum, point) => ({ x: sum.x + point.x / points.length, y: sum.y + point.y / points.length }), { x: 0, y: 0 });
    points.forEach((point) => {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', String(hub.x)); line.setAttribute('y1', String(hub.y));
      line.setAttribute('x2', String(point.x)); line.setAttribute('y2', String(point.y));
      line.setAttribute('stroke', colors[connection.terrain] || '#696758');
      line.setAttribute('stroke-width', '3'); line.setAttribute('stroke-linecap', 'round');
      line.setAttribute('stroke-dasharray', connection.terrain === 'field' ? '7 6' : 'none');
      line.setAttribute('opacity', '0.72');
      overlay.append(line);
    });
  });
}

function renderList() {
  const list = $('#tile-list'); list.innerHTML = '';
  tileIds.forEach((id) => {
    const tile = catalog[id]; const button = document.createElement('button');
    button.className = `tile-button ${id === currentId ? 'active' : ''}`;
    button.type = 'button'; button.setAttribute('aria-label', id); button.innerHTML = `<img src="${tile.image}" alt="">`;
    button.addEventListener('click', () => { currentId = id; render(); }); list.append(button);
  });
}
function render() {
  renderList();
  renderExtraction();
}
render();
loadExtractionData();
window.addEventListener('resize', () => {
  if (extractionData) renderConnectionLines(extractionData[currentId]?.connections || []);
});
