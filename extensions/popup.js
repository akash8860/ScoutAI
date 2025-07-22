document.getElementById("scrape").addEventListener("click", async () => {
  const url = document.getElementById("url").value.trim();
  const city = document.getElementById("city").value.trim() || "none";
  const mode = document.getElementById("mode").value;

  const status = document.getElementById("status");
  const loader = document.getElementById("loader");

  status.textContent = "Initializing...";
  loader.style.display = "block";

  try {
    const res = await fetch("http://localhost:8000/scrape", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, city, mode })
    });

    const json = await res.json();

    status.textContent = "✅ " + json.details;
    loader.style.display = "none";

    // Trigger download
    setTimeout(() => {
      window.open("http://localhost:8000/download", "_blank");
    }, 1000);

  } catch (err) {
    loader.style.display = "none";
    status.textContent = "❌ Connection failed. Is the backend running?";
  }
});
