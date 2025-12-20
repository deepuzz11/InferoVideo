const API_BASE = "https://probable-space-pancake-x6pw65x6qw6c9px7-8000.app.github.dev";

const video = document.getElementById("video");

function loadVideo() {
  const jobId = document.getElementById("jobId").value;

  video.src = `${API_BASE}/static/${jobId}.mp4`; // optional if you expose static
  loadChapters(jobId);
  loadHighlights(jobId);
}

function loadChapters(jobId) {
  fetch(`${API_BASE}/segment?job_id=${jobId}`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById("chapters");
      list.innerHTML = "";

      fetch(`${API_BASE}/data/chapters/${jobId}.json`)
        .then(res => res.json())
        .then(chapters => {
          chapters.forEach(ch => {
            const li = document.createElement("li");
            li.innerText = ch.title;
            li.onclick = () => {
              video.currentTime = ch.start;
              video.play();
            };
            list.appendChild(li);
          });
        });
    });
}

function search() {
  const jobId = document.getElementById("jobId").value;
  const query = document.getElementById("query").value;

  fetch(`${API_BASE}/search?job_id=${jobId}&query=${query}`, {
    method: "POST"
  })
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById("searchResults");
      list.innerHTML = "";

      data.results.forEach(r => {
        const li = document.createElement("li");
        li.innerText = `${r.text.slice(0, 60)}...`;
        li.onclick = () => {
          video.currentTime = r.start;
          video.play();
        };
        list.appendChild(li);
      });
    });
}

function loadHighlights(jobId) {
  fetch(`${API_BASE}/highlight?job_id=${jobId}`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById("highlights");
      list.innerHTML = "";

      for (let i = 1; i <= data.clips; i++) {
        const li = document.createElement("li");
        li.innerText = `Highlight ${i}`;
        li.onclick = () => {
          video.src = `${API_BASE}/data/highlights/${jobId}/clip_${String(i).padStart(2, "0")}.mp4`;
          video.play();
        };
        list.appendChild(li);
      }
    });
}
