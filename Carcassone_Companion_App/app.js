const palette = [
  { name: "Blue", color: "#3976bb" },
  { name: "Red", color: "#be463e" },
  { name: "Yellow", color: "#d7a320" },
  { name: "Green", color: "#468354" },
  { name: "Black", color: "#323232" },
  { name: "Pink", color: "#cf6f99" },
];

const defaultState = () => ({
  players: palette.slice(0, 2).map((player, index) => ({ ...player, id: `player-${index}` })),
  features: [],
  tiles: [],
});

let state = loadState();
const $ = (selector) => document.querySelector(selector);
let uploadedImage = null;
let imageBounds = null;
let calibrationPoints = [];
let edgeStrength = null;
let edgeOverlayVisible = false;

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem("carcassonne-companion"));
    return saved ? { ...defaultState(), ...saved, tiles: saved.tiles || [] } : defaultState();
  } catch {
    return defaultState();
  }
}

function saveState() {
  localStorage.setItem("carcassonne-companion", JSON.stringify(state));
}

function scoreFeature(feature) {
  if (feature.type === "city") return feature.amount + feature.bonus;
  if (feature.type === "road") return feature.amount;
  if (feature.type === "monastery") return 1 + feature.amount;
  return feature.amount * 3;
}

function ruleFor(type) {
  return {
    city: { amount: "City tiles", bonus: "Pennants / shields", help: "Incomplete city: 1 point per tile and 1 per pennant." },
    road: { amount: "Road tiles", bonus: "Not used", help: "Incomplete road: 1 point per tile." },
    monastery: { amount: "Adjacent tiles", bonus: "Not used", help: "Incomplete monastery: 1 point for the monastery plus 1 for each adjacent tile (0–8)." },
    farm: { amount: "Completed cities", bonus: "Not used", help: "Farmer: 3 points for every completed city touching this field." },
  }[type];
}

function renderPlayers() {
  const list = $("#player-list");
  list.innerHTML = "";
  const template = $("#player-template");
  state.players.forEach((player) => {
    const row = template.content.firstElementChild.cloneNode(true);
    row.style.setProperty("--player-color", player.color);
    const input = row.querySelector(".player-name");
    input.value = player.name;
    input.addEventListener("input", () => { player.name = input.value || "Unnamed player"; saveState(); renderOwners(); renderScores(); });
    const remove = row.querySelector(".remove-player");
    remove.disabled = state.players.length <= 1;
    remove.addEventListener("click", () => {
      state.players = state.players.filter((item) => item.id !== player.id);
      state.features.forEach((feature) => { feature.owners = feature.owners.filter((id) => id !== player.id); });
      saveState(); render();
    });
    list.append(row);
  });
}

function renderOwners() {
  const container = $("#owner-options");
  container.innerHTML = "";
  state.players.forEach((player, index) => {
    const label = document.createElement("label");
    label.className = "owner-option";
    label.style.setProperty("--player-color", player.color);
    label.innerHTML = `<input type="checkbox" name="owners" value="${player.id}" ${index === 0 ? "checked" : ""}><span class="player-dot"></span><span>${escapeHtml(player.name)}</span>`;
    container.append(label);
  });
}

function renderForm() {
  const type = $("#feature-type").value;
  const rule = ruleFor(type);
  $("#amount-label").childNodes[0].nodeValue = `${rule.amount} `;
  $("#bonus-label").childNodes[0].nodeValue = `${rule.bonus} `;
  $("#feature-bonus").disabled = type !== "city";
  $("#feature-amount").max = type === "monastery" ? 8 : "";
  $("#rule-help").textContent = rule.help;
}

function renderScores() {
  const totals = Object.fromEntries(state.players.map((player) => [player.id, 0]));
  state.features.forEach((feature) => feature.owners.forEach((id) => { if (id in totals) totals[id] += scoreFeature(feature); }));
  $("#scoreboard").innerHTML = state.players.map((player) => `<div class="score"><div class="score-name"><span class="player-dot" style="--player-color:${player.color}"></span>${escapeHtml(player.name)}</div><div class="score-points">${totals[player.id]}</div></div>`).join("");
  $("#empty-state").hidden = state.features.length > 0;
}

function renderFeatures() {
  const list = $("#feature-list");
  list.innerHTML = "";
  state.features.forEach((feature, index) => {
    const points = scoreFeature(feature);
    const ownerNames = feature.owners.map((id) => state.players.find((player) => player.id === id)?.name).filter(Boolean).join(", ");
    const rule = ruleFor(feature.type);
    const detail = feature.type === "city" ? `${feature.amount} tiles, ${feature.bonus} pennants` : `${feature.amount} ${rule.amount.toLowerCase()}`;
    const item = document.createElement("li");
    item.className = "feature";
    item.innerHTML = `<div><div class="feature-title">${feature.type[0].toUpperCase() + feature.type.slice(1)}</div><div class="feature-detail">${detail} · ${escapeHtml(ownerNames)}</div></div><div class="feature-points">${points} each</div><button class="delete-feature" aria-label="Remove ${feature.type}" type="button">×</button>`;
    item.querySelector("button").addEventListener("click", () => { state.features.splice(index, 1); saveState(); renderScores(); renderFeatures(); });
    list.append(item);
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
}

function render() { renderPlayers(); renderOwners(); renderForm(); renderScores(); renderFeatures(); }

function drawPhoto() {
  const canvas = $("#board-canvas");
  const context = canvas.getContext("2d");
  if (!uploadedImage) return;
  const maximumWidth = 700;
  const scale = Math.min(maximumWidth / uploadedImage.naturalWidth, 1);
  canvas.width = Math.round(uploadedImage.naturalWidth * scale);
  canvas.height = Math.round(uploadedImage.naturalHeight * scale);
  imageBounds = { scale, width: canvas.width, height: canvas.height };
  context.drawImage(uploadedImage, 0, 0, canvas.width, canvas.height);
  if (edgeOverlayVisible && edgeStrength) drawEdgeOverlay(context, canvas.width, canvas.height);
  if (calibrationPoints.length) {
    context.lineWidth = 3;
    context.strokeStyle = "#2e6652";
    context.fillStyle = "#fffdf7";
    context.beginPath();
    calibrationPoints.forEach((point, index) => {
      if (index === 0) context.moveTo(point.x, point.y);
      else context.lineTo(point.x, point.y);
    });
    if (calibrationPoints.length === 4) context.closePath();
    context.stroke();
    calibrationPoints.forEach((point, index) => {
      context.beginPath(); context.arc(point.x, point.y, 8, 0, Math.PI * 2); context.fill(); context.stroke();
      context.fillStyle = "#2e6652"; context.font = "700 14px system-ui"; context.fillText(String(index + 1), point.x - 4, point.y + 5); context.fillStyle = "#fffdf7";
    });
  }
  if (calibrationPoints.length === 4) {
    state.tiles.forEach((tile, index) => {
      const point = tileImagePoint(tile);
      if (!point) return;
      context.beginPath();
      context.arc(point.x, point.y, 11, 0, Math.PI * 2);
      context.fillStyle = "#d7a320";
      context.fill();
      context.lineWidth = 2;
      context.strokeStyle = "#28281e";
      context.stroke();
      context.fillStyle = "#28281e";
      context.font = "700 11px system-ui";
      context.textAlign = "center";
      context.fillText(String(index + 1), point.x, point.y + 4);
      context.textAlign = "start";
    });
  }
  updateCalibrationMessage();
}

function drawEdgeOverlay(context, width, height) {
  const overlay = context.createImageData(width, height);
  for (let index = 0; index < edgeStrength.length; index += 1) {
    const alpha = Math.round(edgeStrength[index] * 190);
    if (!alpha) continue;
    overlay.data[index * 4] = 34;
    overlay.data[index * 4 + 1] = 211;
    overlay.data[index * 4 + 2] = 153;
    overlay.data[index * 4 + 3] = alpha;
  }
  context.putImageData(overlay, 0, 0);
}

function updateCalibrationMessage() {
  const status = $("#calibration-status");
  const result = $("#calibration-result");
  if (!uploadedImage) return;
  if (calibrationPoints.length < 4) {
    const corners = ["top-left", "top-right", "bottom-right", "bottom-left"];
    status.textContent = `Click the ${corners[calibrationPoints.length]} corner of one clearly visible tile.`;
    result.textContent = `${calibrationPoints.length} of 4 corners selected`;
  } else {
    status.textContent = "Reference tile captured. Its perspective is ready for the next board-mapping step.";
    result.textContent = "Calibration complete";
    $("#mapping-controls").hidden = false;
    updateMappingMessage();
  }
}

function calibrationMatrix() {
  if (calibrationPoints.length !== 4) return null;
  const source = [[0, 0], [1, 0], [1, 1], [0, 1]];
  const rows = [];
  calibrationPoints.forEach((point, index) => {
    const [u, v] = source[index];
    rows.push([u, v, 1, 0, 0, 0, -point.x * u, -point.x * v, point.x]);
    rows.push([0, 0, 0, u, v, 1, -point.y * u, -point.y * v, point.y]);
  });
  const solution = solveLinearSystem(rows);
  return solution ? [[solution[0], solution[1], solution[2]], [solution[3], solution[4], solution[5]], [solution[6], solution[7], 1]] : null;
}

function solveLinearSystem(rows) {
  const matrix = rows.map((row) => row.slice());
  for (let column = 0; column < 8; column += 1) {
    let pivot = column;
    for (let row = column + 1; row < 8; row += 1) if (Math.abs(matrix[row][column]) > Math.abs(matrix[pivot][column])) pivot = row;
    if (Math.abs(matrix[pivot][column]) < 1e-9) return null;
    [matrix[column], matrix[pivot]] = [matrix[pivot], matrix[column]];
    const divisor = matrix[column][column];
    for (let item = column; item < 9; item += 1) matrix[column][item] /= divisor;
    for (let row = 0; row < 8; row += 1) {
      if (row === column) continue;
      const factor = matrix[row][column];
      for (let item = column; item < 9; item += 1) matrix[row][item] -= factor * matrix[column][item];
    }
  }
  return matrix.map((row) => row[8]);
}

function invert3x3(matrix) {
  const [a, b, c] = matrix[0]; const [d, e, f] = matrix[1]; const [g, h, i] = matrix[2];
  const determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
  if (Math.abs(determinant) < 1e-9) return null;
  return [[(e * i - f * h) / determinant, (c * h - b * i) / determinant, (b * f - c * e) / determinant], [(f * g - d * i) / determinant, (a * i - c * g) / determinant, (c * d - a * f) / determinant], [(d * h - e * g) / determinant, (b * g - a * h) / determinant, (a * e - b * d) / determinant]];
}

function transformPoint(matrix, x, y) {
  const denominator = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2];
  if (Math.abs(denominator) < 1e-9) return null;
  return { x: (matrix[0][0] * x + matrix[0][1] * y + matrix[0][2]) / denominator, y: (matrix[1][0] * x + matrix[1][1] * y + matrix[1][2]) / denominator };
}

function mapBoardToImage(x, y) {
  const matrix = calibrationMatrix();
  return matrix ? transformPoint(matrix, x, y) : null;
}

function mapImageToBoard(x, y) {
  const matrix = calibrationMatrix();
  const inverse = matrix && invert3x3(matrix);
  return inverse ? transformPoint(inverse, x, y) : null;
}

function tileImagePoint(tile) {
  const canvas = $("#board-canvas");
  if (Number.isFinite(tile.imageX) && Number.isFinite(tile.imageY)) return { x: tile.imageX * canvas.width, y: tile.imageY * canvas.height };
  return mapBoardToImage(tile.x + 0.5, tile.y + 0.5);
}

function updateMappingMessage() {
  if (calibrationPoints.length !== 4) return;
  const count = state.tiles.length;
  $("#tile-map-result").textContent = count === 1 ? "1 tile marked · click its marker to remove it" : `${count} tiles marked · click a yellow marker to remove it`;
}

function clearPhoto() {
  uploadedImage = null; imageBounds = null; calibrationPoints = []; edgeStrength = null; edgeOverlayVisible = false;
  $("#board-photo").value = "";
  $("#photo-workspace").hidden = true;
  $("#clear-photo").hidden = true;
  $("#mapping-controls").hidden = true;
  $("#toggle-edges").disabled = true;
  $("#toggle-edges").textContent = "Show edge overlay";
  $("#auto-calibrate").disabled = true;
}

function calculateSobelEdges() {
  const canvas = $("#board-canvas");
  const { width, height } = canvas;
  const context = canvas.getContext("2d");
  context.drawImage(uploadedImage, 0, 0, width, height);
  const pixels = context.getImageData(0, 0, width, height).data;
  const gray = new Float32Array(width * height);
  for (let index = 0; index < gray.length; index += 1) {
    const offset = index * 4;
    gray[index] = pixels[offset] * 0.299 + pixels[offset + 1] * 0.587 + pixels[offset + 2] * 0.114;
  }
  const magnitude = new Float32Array(width * height);
  const values = [];
  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const top = (y - 1) * width + x; const middle = y * width + x; const bottom = (y + 1) * width + x;
      const gx = -gray[top - 1] + gray[top + 1] - 2 * gray[middle - 1] + 2 * gray[middle + 1] - gray[bottom - 1] + gray[bottom + 1];
      const gy = gray[top - 1] + 2 * gray[top] + gray[top + 1] - gray[bottom - 1] - 2 * gray[bottom] - gray[bottom + 1];
      const value = Math.hypot(gx, gy);
      magnitude[middle] = value;
      values.push(value);
    }
  }
  values.sort((a, b) => a - b);
  const threshold = values[Math.floor(values.length * 0.86)] || 1;
  const maximum = values[values.length - 1] || threshold + 1;
  edgeStrength = new Float32Array(magnitude.length);
  for (let index = 0; index < magnitude.length; index += 1) edgeStrength[index] = Math.max(0, Math.min(1, (magnitude[index] - threshold) / (maximum - threshold)));
}

function sampleEdge(x, y) {
  const canvas = $("#board-canvas");
  const roundedX = Math.round(x); const roundedY = Math.round(y);
  if (!edgeStrength || roundedX < 0 || roundedY < 0 || roundedX >= canvas.width || roundedY >= canvas.height) return 0;
  return edgeStrength[roundedY * canvas.width + roundedX];
}

function squareEdgeScore(centerX, centerY, size, angle) {
  const cosine = Math.cos(angle); const sine = Math.sin(angle); const half = size / 2;
  const corner = (x, y) => ({ x: centerX + x * cosine - y * sine, y: centerY + x * sine + y * cosine });
  const corners = [corner(-half, -half), corner(half, -half), corner(half, half), corner(-half, half)];
  let score = 0; const samples = 28;
  for (let side = 0; side < 4; side += 1) {
    const start = corners[side]; const end = corners[(side + 1) % 4];
    for (let sample = 0; sample < samples; sample += 1) {
      const ratio = sample / (samples - 1);
      score += sampleEdge(start.x + (end.x - start.x) * ratio, start.y + (end.y - start.y) * ratio);
    }
  }
  return score / (samples * 4);
}

function detectReferenceTile() {
  const canvas = $("#board-canvas");
  const minDimension = Math.min(canvas.width, canvas.height);
  let best = null;
  const test = (x, y, size, degrees) => {
    const angle = degrees * Math.PI / 180;
    const score = squareEdgeScore(x, y, size, angle);
    if (!best || score > best.score) best = { x, y, size, degrees, score };
  };
  for (let size = minDimension * 0.09; size <= minDimension * 0.26; size += minDimension * 0.025) {
    for (let y = size; y < canvas.height - size; y += Math.max(18, size * 0.32)) {
      for (let x = size; x < canvas.width - size; x += Math.max(18, size * 0.32)) {
        for (let degrees = -20; degrees <= 20; degrees += 5) test(x, y, size, degrees);
      }
    }
  }
  if (!best) return null;
  for (let size = best.size - 12; size <= best.size + 12; size += 4) {
    for (let y = best.y - 16; y <= best.y + 16; y += 4) {
      for (let x = best.x - 16; x <= best.x + 16; x += 4) {
        for (let degrees = best.degrees - 4; degrees <= best.degrees + 4; degrees += 2) test(x, y, size, degrees);
      }
    }
  }
  const radians = best.degrees * Math.PI / 180; const cosine = Math.cos(radians); const sine = Math.sin(radians); const half = best.size / 2;
  const rotate = (x, y) => ({ x: best.x + x * cosine - y * sine, y: best.y + x * sine + y * cosine });
  return { points: [rotate(-half, -half), rotate(half, -half), rotate(half, half), rotate(-half, half)], confidence: best.score };
}

function isHeic(file) {
  return /image\/(heic|heif)/i.test(file.type) || /\.hei[cf]$/i.test(file.name);
}

function showPhotoFile(file) {
  const reader = new FileReader();
  reader.addEventListener("load", () => {
    uploadedImage = new Image();
    uploadedImage.addEventListener("load", () => {
      calibrationPoints = []; edgeStrength = null; edgeOverlayVisible = false;
      $("#photo-workspace").hidden = false;
      $("#clear-photo").hidden = false;
      $("#toggle-edges").disabled = false;
      $("#auto-calibrate").disabled = false;
      drawPhoto();
    });
    uploadedImage.addEventListener("error", () => {
      $("#photo-instructions").textContent = "This image could not be read. Please choose a different photo.";
    });
    uploadedImage.src = reader.result;
  });
  reader.readAsDataURL(file);
}

$("#add-player").addEventListener("click", () => {
  const next = palette[state.players.length % palette.length];
  state.players.push({ ...next, name: next.name, id: `player-${crypto.randomUUID()}` });
  saveState(); render();
});
$("#feature-type").addEventListener("change", renderForm);
$("#feature-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const owners = form.getAll("owners");
  if (!owners.length) { $("#rule-help").textContent = "Select at least one player who has a meeple on this construction."; return; }
  const type = form.get("type");
  state.features.push({ type, amount: Number(form.get("amount")), bonus: type === "city" ? Number(form.get("bonus")) : 0, owners });
  saveState(); event.currentTarget.reset(); renderOwners(); renderForm(); renderScores(); renderFeatures();
});
$("#reset-game").addEventListener("click", () => { if (confirm("Clear all players and constructions?")) { state = defaultState(); saveState(); render(); } });
$("#board-photo").addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  if (!isHeic(file)) { showPhotoFile(file); return; }
  $("#photo-instructions").textContent = "Converting the HEIC photo locally…";
  try {
    if (typeof window.heic2any !== "function") throw new Error("HEIC converter did not load");
    const converted = await window.heic2any({ blob: file, toType: "image/jpeg", quality: 0.92 });
    showPhotoFile(Array.isArray(converted) ? converted[0] : converted);
    $("#photo-instructions").textContent = "HEIC converted locally for analysis. Now choose a reference tile.";
  } catch (error) {
    $("#photo-instructions").textContent = "The HEIC photo could not be converted. Check your connection, then try again, or export it as JPEG from Photos.";
  }
});
$("#board-canvas").addEventListener("click", (event) => {
  if (!uploadedImage) return;
  const rect = event.currentTarget.getBoundingClientRect();
  const x = (event.clientX - rect.left) * (event.currentTarget.width / rect.width);
  const y = (event.clientY - rect.top) * (event.currentTarget.height / rect.height);
  if (calibrationPoints.length < 4) calibrationPoints.push({ x, y });
  else {
    const closestIndex = state.tiles.findIndex((tile) => {
      const point = tileImagePoint(tile);
      return point && Math.hypot(point.x - x, point.y - y) < 20;
    });
    if (closestIndex >= 0) state.tiles.splice(closestIndex, 1);
    else state.tiles.push({ id: crypto.randomUUID(), imageX: x / event.currentTarget.width, imageY: y / event.currentTarget.height });
    saveState(); updateMappingMessage();
  }
  drawPhoto();
});
$("#reset-calibration").addEventListener("click", () => { calibrationPoints = []; $("#mapping-controls").hidden = true; drawPhoto(); });
$("#clear-photo").addEventListener("click", clearPhoto);
$("#undo-tile").addEventListener("click", () => { state.tiles.pop(); saveState(); drawPhoto(); updateMappingMessage(); });
$("#clear-tiles").addEventListener("click", () => { state.tiles = []; saveState(); drawPhoto(); updateMappingMessage(); });
$("#toggle-edges").addEventListener("click", () => {
  if (!edgeStrength) calculateSobelEdges();
  edgeOverlayVisible = !edgeOverlayVisible;
  $("#toggle-edges").textContent = edgeOverlayVisible ? "Hide edge overlay" : "Show edge overlay";
  drawPhoto();
});
$("#auto-calibrate").addEventListener("click", () => {
  if (!uploadedImage) return;
  if (state.tiles.length && !confirm("Auto-detection will replace the grid reference. Clear mapped tiles first, or continue and remap them?")) return;
  calculateSobelEdges();
  edgeOverlayVisible = true;
  $("#toggle-edges").textContent = "Hide edge overlay";
  const candidate = detectReferenceTile();
  if (!candidate) { $("#photo-instructions").textContent = "No confident tile was found. Use the four manual corner clicks instead."; drawPhoto(); return; }
  calibrationPoints = candidate.points;
  $("#photo-instructions").textContent = `Automatic edge detection found a candidate tile (edge score ${Math.round(candidate.confidence * 100)}). Check the green outline; reset and click manually if it is wrong.`;
  drawPhoto();
});

render();
