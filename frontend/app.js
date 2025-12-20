async function process() {
  const url = document.getElementById("url").value;
  await fetch(`/process?url=${url}`, { method: "POST" });
  alert("Processing started");
}
