document.getElementById("scrape").addEventListener("click", async () => {
  const url = document.getElementById("url").value.trim();
  const city = document.getElementById("city").value.trim() || "none";
  const mode = document.getElementById("mode").value;

  const status = document.getElementById("status");
  const loader = document.getElementById("loader");

  const backendURL = "https://scoutai-backend.onrender.com"; //  UPDATE HERE

  status.textContent = "Initializing...";
  loader.style.display = "block";

  try {
    const res = await fetch(`${backendURL}/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, city, mode })
    });

    const json = await res.json();

    status.textContent = " " + json.details;
    loader.style.display = "none";

    // Trigger download after 1s
    setTimeout(() => {
      window.open(`${backendURL}/download`, "_blank");
    }, 1000);

  } catch (err) {
    loader.style.display = "none";
    status.textContent = " Connection failed. Is the backend running?";
  }
});
