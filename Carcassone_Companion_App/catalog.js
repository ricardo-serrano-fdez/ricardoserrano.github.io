const tileIds = ['IMG_2949', 'IMG_2950', 'IMG_2951', 'IMG_2952', 'IMG_2953', 'IMG_2954', 'IMG_2955', 'IMG_2956', 'IMG_2957', 'IMG_2958', 'IMG_2959', 'IMG_2960', 'IMG_2961', 'IMG_2962', 'IMG_2963', 'IMG_2964', 'IMG_2965', 'IMG_2966', 'IMG_2967', 'IMG_2968', 'IMG_2969', 'IMG_2970', 'IMG_2971', 'IMG_2972', 'IMG_2973', 'IMG_2974', 'IMG_2975', 'IMG_2976', 'IMG_2977', 'IMG_2978', 'IMG_2979', 'IMG_2980', 'IMG_2981', 'IMG_2982', 'IMG_2983', 'IMG_2984', 'IMG_2985', 'IMG_2986', 'IMG_2987', 'IMG_2988', 'IMG_2989', 'IMG_2990', 'IMG_2991', 'IMG_2992', 'IMG_2993', 'IMG_2994', 'IMG_2995', 'IMG_2996', 'IMG_2997', 'IMG_2998', 'IMG_2999', 'IMG_3001', 'IMG_3002', 'IMG_3003', 'IMG_3004', 'IMG_3005', 'IMG_3006', 'IMG_3007', 'IMG_3008', 'IMG_3009', 'IMG_3010', 'IMG_3011', 'IMG_3012', 'IMG_3014', 'IMG_3015', 'IMG_3016', 'IMG_3017', 'IMG_3018', 'IMG_3019', 'IMG_3020', 'IMG_3021', 'IMG_3022'];
const key = 'carcassonne-zman-2014-catalog';
const defaults = Object.fromEntries(tileIds.map((id) => [id, { id, image: `tile_library_z-man_2014/crops/${id}.jpg`, edges: { north: 'field', east: 'field', south: 'field', west: 'field' }, shields: 0, monastery: false, cityGroups: '', roadGroups: '', fieldGroups: '' }]));
let catalog = { ...defaults, ...JSON.parse(localStorage.getItem(key) || '{}') };
let currentId = tileIds[0];
const $ = (selector) => document.querySelector(selector);

function renderList() {
  const list = $('#tile-list'); list.innerHTML = '';
  tileIds.forEach((id) => {
    const tile = catalog[id]; const button = document.createElement('button');
    button.className = `tile-button ${id === currentId ? 'active' : ''} ${isComplete(tile) ? 'done' : ''}`;
    button.type = 'button'; button.setAttribute('aria-label', id); button.innerHTML = `<img src="${tile.image}" alt="">`;
    button.addEventListener('click', () => { saveCurrent(); currentId = id; render(); }); list.append(button);
  });
}
function isComplete(tile) { return Boolean(tile.cityGroups || tile.roadGroups || tile.monastery || tile.shields || Object.values(tile.edges).some((edge) => edge !== 'field')); }
function render() {
  const tile = catalog[currentId]; $('#tile-image').src = tile.image; $('#tile-title').textContent = currentId;
  ['north','east','south','west'].forEach((side) => { $(`[name="${side}"]`).value = tile.edges[side]; });
  $('#tile-form').shields.value = tile.shields; $('#tile-form').monastery.checked = tile.monastery;
  $('#tile-form').cityGroups.value = tile.cityGroups; $('#tile-form').roadGroups.value = tile.roadGroups; $('#tile-form').fieldGroups.value = tile.fieldGroups;
  renderList(); const completed = tileIds.filter((id) => isComplete(catalog[id])).length; $('#progress').textContent = `${completed} of ${tileIds.length} tiles reviewed`;
}
function saveCurrent() {
  const form = $('#tile-form'); const data = new FormData(form); const tile = catalog[currentId];
  tile.edges = Object.fromEntries(['north','east','south','west'].map((side) => [side, data.get(side)]));
  tile.shields = Number(data.get('shields')); tile.monastery = data.get('monastery') === 'on'; tile.cityGroups = data.get('cityGroups').trim(); tile.roadGroups = data.get('roadGroups').trim(); tile.fieldGroups = data.get('fieldGroups').trim();
  localStorage.setItem(key, JSON.stringify(catalog));
}
$('#tile-form').addEventListener('submit', (event) => { event.preventDefault(); saveCurrent(); $('#save-status').textContent = `${currentId} saved.`; render(); });
$('#export-catalog').addEventListener('click', () => { saveCurrent(); const blob = new Blob([JSON.stringify(Object.values(catalog), null, 2)], { type: 'application/json' }); const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: 'carcassonne-zman-2014-catalog.json' }); link.click(); URL.revokeObjectURL(link.href); });
render();
