const API_BASE = "https://probable-space-pancake-x6pw65x6qw6c9px7-8000.app.github.dev";
const video = document.getElementById("video");

function loadVideo() {
  const jobId = document.getElementById("jobId").value.trim();
  if (!jobId) {
    alert("Please enter a Job ID");
    return;
  }

  video.src = `${API_BASE}/data/videos/${jobId}.mp4`;
  video.load();

  loadChapters(jobId);
  loadHighlights(jobId);
}

function loadChapters(jobId) {
  const list = document.getElementById("chapters");
  list.innerHTML = "<li class='placeholder'>Loading chapters…</li>";

  fetch(`${API_BASE}/data/chapters/${jobId}.json`)
    .then(res => res.json())
    .then(chapters => {
      list.innerHTML = "";

      if (!chapters.length) {
        list.innerHTML = "<li class='placeholder'>No chapters found</li>";
        return;
      }

      chapters.forEach(ch => {
        const li = document.createElement("li");
        li.textContent = ch.title;
        li.dataset.start = ch.start;

        li.onclick = () => {
          video.currentTime = ch.start;
          video.play();
        };

        list.appendChild(li);
      });
    });
}

function search() {
  const jobId = document.getElementById("jobId").value.trim();
  const query = document.getElementById("query").value.trim();
  if (!query) return;

  const list = document.getElementById("searchResults");
  list.innerHTML = "<li class='placeholder'>Searching…</li>";

  fetch(`${API_BASE}/search?job_id=${jobId}&query=${query}`, {
    method: "POST"
  })
    .then(res => res.json())
    .then(data => {
      list.innerHTML = "";

      if (!data.results.length) {
        list.innerHTML = "<li class='placeholder'>No results found</li>";
        return;
      }

      data.results.forEach(r => {
        const li = document.createElement("li");
        li.textContent = r.text.slice(0, 90) + "…";
        li.onclick = () => {
          video.currentTime = r.start;
          video.play();
        };
        list.appendChild(li);
      });
    });
}

function loadHighlights(jobId) {
  const list = document.getElementById("highlights");
  list.innerHTML = "<li class='placeholder'>Generating highlights…</li>";

  fetch(`${API_BASE}/highlight?job_id=${jobId}`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
      list.innerHTML = "";

      if (!data.clips) {
        list.innerHTML = "<li class='placeholder'>No highlights found</li>";
        return;
      }

      for (let i = 1; i <= data.clips; i++) {
        const li = document.createElement("li");
        li.textContent = `▶ Highlight ${i}`;
        li.onclick = () => {
          video.src = `${API_BASE}/data/highlights/${jobId}/clip_${String(i).padStart(2, "0")}.mp4`;
          video.play();
        };
        list.appendChild(li);
      }
    });
}

/* Highlight active chapter while video plays */
video.ontimeupdate = () => {
  document.querySelectorAll("#chapters li").forEach(li => {
    const start = Number(li.dataset.start);
    li.classList.toggle("active", video.currentTime >= start);
  });
};
