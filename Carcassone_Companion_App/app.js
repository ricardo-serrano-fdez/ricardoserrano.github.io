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
});

let state = loadState();
const $ = (selector) => document.querySelector(selector);
let uploadedImage = null;
let imageBounds = null;
let calibrationPoints = [];

function loadState() {
  try {
    return JSON.parse(localStorage.getItem("carcassonne-companion")) || defaultState();
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
  updateCalibrationMessage();
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
  }
}

function clearPhoto() {
  uploadedImage = null; imageBounds = null; calibrationPoints = [];
  $("#board-photo").value = "";
  $("#photo-workspace").hidden = true;
  $("#clear-photo").hidden = true;
}

function isHeic(file) {
  return /image\/(heic|heif)/i.test(file.type) || /\.hei[cf]$/i.test(file.name);
}

function showPhotoFile(file) {
  const reader = new FileReader();
  reader.addEventListener("load", () => {
    uploadedImage = new Image();
    uploadedImage.addEventListener("load", () => {
      calibrationPoints = [];
      $("#photo-workspace").hidden = false;
      $("#clear-photo").hidden = false;
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
  if (!uploadedImage || calibrationPoints.length === 4) return;
  const rect = event.currentTarget.getBoundingClientRect();
  calibrationPoints.push({ x: (event.clientX - rect.left) * (event.currentTarget.width / rect.width), y: (event.clientY - rect.top) * (event.currentTarget.height / rect.height) });
  drawPhoto();
});
$("#reset-calibration").addEventListener("click", () => { calibrationPoints = []; drawPhoto(); });
$("#clear-photo").addEventListener("click", clearPhoto);

render();
