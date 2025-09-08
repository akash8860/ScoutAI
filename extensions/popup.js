// popup.js
// Set backend URL (local while testing)
const backendURL = "http://127.0.0.1:8000"; // change when deployed

// DOM
const urlInput = document.getElementById("url");
const cityInput = document.getElementById("city");
const modeInput = document.getElementById("mode");
const scrapeBtn = document.getElementById("scrape");
const statusEl = document.getElementById("status");
const plansContainer = document.getElementById("plans_container");
const quotaText = document.getElementById("quota_text");

const overlay = document.getElementById("overlay");
const loginUser = document.getElementById("login_user");
const loginSubmit = document.getElementById("login_submit");
const loginCancel = document.getElementById("login_cancel");

// Local key for stored username (simple)
const USER_KEY = "scoutai_username";

// Default behaviour: free quota assumed 10 for frontend messaging if server not available
const DEFAULT_FREE_LIMIT = 10;

// Utility to read stored username
function getStoredUsername() {
  try {
    return localStorage.getItem(USER_KEY);
  } catch (e) {
    return null;
  }
}
function storeUsername(u) {
  try {
    localStorage.setItem(USER_KEY, u);
  } catch (e) {}
}

// Fetch quota from backend /quota
async function fetchQuota(username) {
  if (!username) return null;
  try {
    const res = await fetch(`${backendURL}/quota`, {
      method: "GET",
      headers: { "Authorization": "Bearer " + username }
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data;
  } catch (err) {
    console.warn("quota fetch error", err);
    return null;
  }
}

// Update quota UI and enable/disable button
function renderQuota(q) {
  if (!q) {
    quotaText.textContent = `Plan: free • 0/${DEFAULT_FREE_LIMIT} scrapes`;
    plansContainer.style.display = "block";
    scrapeBtn.disabled = false;
    return;
  }
  const used = q.used ?? 0;
  const limit = q.limit ?? DEFAULT_FREE_LIMIT;
  quotaText.textContent = `Plan: ${q.tier} • ${used}/${limit} scrapes`;
  plansContainer.style.display = "block";
  scrapeBtn.disabled = used >= limit;
}

// Show login overlay
function showLogin() {
  overlay.style.display = "flex";
  loginUser.focus();
}

// Hide login overlay
function hideLogin() {
  overlay.style.display = "none";
  loginUser.value = "";
}

// Main action: start scrape
async function startScrapeFlow() {
  const url = urlInput.value.trim();
  const city = cityInput.value.trim() || "none";
  const mode = modeInput.value;

  if (!url) {
    alert("Please enter a URL.");
    return;
  }

  let username = getStoredUsername();
  if (!username) {
    // First-time: prompt to login
    showLogin();
    // After login overlay continues with the flow (loginSubmit handler)
    return;
  }

  // Ensure we show plan/quota UI before scavenging
  statusEl.textContent = "Checking quota...";
  const quota = await fetchQuota(username);
  renderQuota(quota);

  // If quota exhausted, show message
  if (quota && (quota.used ?? 0) >= (quota.limit ?? DEFAULT_FREE_LIMIT)) {
    statusEl.textContent = "Free monthly quota exhausted — sponsor to upgrade.";
    return;
  }

  // Proceed to call /scrape
  statusEl.textContent = "Initializing scrape...";
  scrapeBtn.disabled = true;
  try {
    const res = await fetch(`${backendURL}/scrape`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + username
      },
      body: JSON.stringify({ url, city, mode })
    });

    if (res.status === 403) {
      const d = await res.json().catch(()=>({}));
      statusEl.textContent = d.detail || "Quota exceeded. Sponsor to upgrade.";
      // refresh quota UI
      const newQ = await fetchQuota(username);
      renderQuota(newQ);
      scrapeBtn.disabled = false;
      return;
    }

    if (!res.ok) {
      const text = await res.text().catch(()=>"");
      statusEl.textContent = "Scrape failed: " + (text || res.status);
      scrapeBtn.disabled = false;
      return;
    }

    const json = await res.json();
    statusEl.textContent = json.details || "Scrape finished";
    // update quota display after success
    const updated = await fetchQuota(username);
    renderQuota(updated);
    // optionally open download
    setTimeout(()=> window.open(`${backendURL}/download`, "_blank"), 900);
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Connection failed. Is backend running?";
  } finally {
    scrapeBtn.disabled = false;
  }
}

// Login overlay submit handler: saves username and resumes scrape if needed
loginSubmit.addEventListener("click", async () => {
  const username = loginUser.value.trim();
  if (!username) { alert("Enter your GitHub username."); return; }
  storeUsername(username);
  hideLogin();

  // After saving username, show quota info and continue
  statusEl.textContent = "Fetching quota...";
  const quota = await fetchQuota(username);
  renderQuota(quota);
  statusEl.textContent = "Ready — press Start Scraping again to begin.";
});

// Cancel login
loginCancel.addEventListener("click", () => {
  hideLogin();
  statusEl.textContent = "Login cancelled. Scrape paused.";
});

// If user presses Start while logged out, the overlay will appear. We also allow them to press "Start" again after login.
scrapeBtn.addEventListener("click", async () => {
  // If overlay currently visible, ignore (login handles)
  if (overlay.style.display === "flex") return;
  // Try to start scrape flow; if no username, overlay shown
  const username = getStoredUsername();
  if (!username) {
    showLogin();
    return;
  }
  // proceed
  await startScrapeFlow();
});

// On load, if username stored, fetch quota and show plan info
document.addEventListener("DOMContentLoaded", async () => {
  const username = getStoredUsername();
  if (username) {
    statusEl.textContent = "Checking quota...";
    const quota = await fetchQuota(username);
    renderQuota(quota);
    statusEl.textContent = "Ready";
  } else {
    // hide plans until user logs in/initiates
    plansContainer.style.display = "none";
  }
});
