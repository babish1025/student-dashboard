const uploadForm  = document.getElementById("uploadForm");
const fileInput   = document.getElementById("fileInput");
const totalCount  = document.getElementById("totalCount");
const catSection  = document.getElementById("categorySection");
const tableCont   = document.getElementById("tableContainer");
const tableTitle  = document.getElementById("tableTitle");
const globalSearch= document.getElementById("globalSearch");
const menuBtn     = document.getElementById("menuBtn");
const sidePanel   = document.getElementById("sidePanel");
const closePanel  = document.getElementById("closePanel");
const searchName  = document.getElementById("searchName");
const searchRoll  = document.getElementById("searchRoll");

menuBtn.onclick   = () => sidePanel.classList.remove("hidden");
closePanel.onclick= () => sidePanel.classList.add("hidden");

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData();
  fd.append("file", fileInput.files[0]);
  const res = await fetch("/upload", { method: "POST", body: fd });
  const data = await res.json();
  if (data.error) return alert(data.error);
  renderCategories(data.categories);
  renderTable(data.columns, data.rows, "Uploaded Data");
  totalCount.textContent = data.total;
});

function renderCategories(cats) {
  catSection.innerHTML = "";
  Object.entries(cats).forEach(([label, info]) => {
    const card = document.createElement("div");
    card.className = "cat-card";
    card.innerHTML = `<h3>${label}</h3>` + Object.entries(info.values)
      .map(([v,c]) => `<div class="val" data-cat="${label}" data-val="${v}">
                        <span>${v}</span><span>${c}</span></div>`)
      .join("");
    catSection.appendChild(card);
  });
  document.querySelectorAll(".val").forEach(el => {
    el.onclick = async () => {
      const r = await fetch(`/filter?category=${encodeURIComponent(el.dataset.cat)}&value=${encodeURIComponent(el.dataset.val)}`);
      const d = await r.json();
      renderTable(d.columns, d.rows, `${el.dataset.cat}: ${el.dataset.val}`);
      totalCount.textContent = d.total;
    };
  });
}

function renderTable(cols, rows, title) {
  tableTitle.textContent = `${title} (${rows.length})`;
  if (!rows.length) { tableCont.innerHTML = "<p>No records.</p>"; return; }
  let html = "<table><thead><tr>" + cols.map(c=>`<th>${c}</th>`).join("") + "</tr></thead><tbody>";
  rows.forEach(r => {
    html += "<tr>" + cols.map(c=>`<td>${r[c] ?? ""}</td>`).join("") + "</tr>";
  });
  html += "</tbody></table>";
  tableCont.innerHTML = html;
}

let t;
function debounced(fn){ clearTimeout(t); t = setTimeout(fn, 250); }

async function runSearch(q, field) {
  const r = await fetch(`/search?q=${encodeURIComponent(q)}&field=${field}`);
  const d = await r.json();
  renderTable(d.columns, d.rows, `Search: ${q || "(all)"}`);
  totalCount.textContent = d.total;
}

globalSearch.addEventListener("input", e => debounced(()=>runSearch(e.target.value, "all")));
searchName.addEventListener("input",  e => debounced(()=>runSearch(e.target.value, "name")));
searchRoll.addEventListener("input",  e => debounced(()=>runSearch(e.target.value, "rollno")));
