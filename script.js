const backgroundPool = [
  "https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1501612780327-45045538702b?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1600&q=80",
  "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1600&q=80"
];

const fallbackSongs = [
  { title: "Can't Stop the Feeling!", artist: "Justin Timberlake", era: "Modern hits", mood: "Feel-good" },
  { title: "Happy", artist: "Pharrell Williams", era: "Modern hits", mood: "Feel-good" },
  { title: "Uptown Funk", artist: "Mark Ronson ft. Bruno Mars", era: "Modern hits", mood: "Party" },
  { title: "Blinding Lights", artist: "The Weeknd", era: "Modern hits", mood: "Electro" },
  { title: "Moves Like Jagger", artist: "Maroon 5 ft. Christina Aguilera", era: "Modern hits", mood: "Rock" },
  { title: "Wake Me Up", artist: "Avicii", era: "Modern hits", mood: "Dance" },
  { title: "Sugar", artist: "Maroon 5", era: "Modern hits", mood: "Pop" },
  { title: "Firework", artist: "Katy Perry", era: "Modern hits", mood: "Pop" },
  { title: "Kiss", artist: "Prince", era: "Classic pop", mood: "Pop" },
  { title: "Baby One More Time", artist: "Britney Spears", era: "Classic pop", mood: "Pop" },
  { title: "Crazy in Love", artist: "Beyoncé ft. Jay-Z", era: "Classic pop", mood: "Disco" },
  { title: "Since U Been Gone", artist: "Kelly Clarkson", era: "Classic pop", mood: "Rock" },
  { title: "Boom Boom Pow", artist: "Black Eyed Peas", era: "Electro", mood: "Party" },
  { title: "Just Can't Get Enough", artist: "Depeche Mode", era: "Classic pop", mood: "Synth" },
  { title: "Toxic", artist: "Britney Spears", era: "Classic pop", mood: "Pop" },
  { title: "Skyscraper", artist: "Demi Lovato", era: "Ballad", mood: "Power" },
  { title: "Roar", artist: "Katy Perry", era: "Empowerment", mood: "Power" },
  { title: "Bad Romance", artist: "Lady Gaga", era: "Classic pop", mood: "Pop" },
  { title: "Single Ladies", artist: "Beyoncé", era: "Modern hits", mood: "Funk" },
  { title: "Shut Up and Dance", artist: "Walk the Moon", era: "Modern hits", mood: "Party" },
  { title: "Locked Out of Heaven", artist: "Bruno Mars", era: "Modern hits", mood: "Pop" },
  { title: "Treat You Better", artist: "Shawn Mendes", era: "Modern hits", mood: "Pop" },
  { title: "Thriller", artist: "Michael Jackson", era: "Classic pop", mood: "Halloween" },
  { title: "Maniac", artist: "Michael Sembello", era: "Soundtrack", mood: "Energy" },
  { title: "Physical", artist: "Dua Lipa", era: "Modern hits", mood: "Dance" },
  { title: "Don't Start Now", artist: "Dua Lipa", era: "Modern hits", mood: "Disco" },
  { title: "Levitating", artist: "Dua Lipa", era: "Modern hits", mood: "Pop" },
  { title: "Watermelon Sugar", artist: "Harry Styles", era: "Modern hits", mood: "Pop" },
  { title: "Hype", artist: "Various Artists", era: "Dance floor", mood: "Party" },
  { title: "Dancing Queen", artist: "ABBA", era: "Classic pop", mood: "Disco" },
  { title: "Maneater", artist: "Hall & Oates", era: "Classic pop", mood: "Pop" },
  { title: "Call Me Maybe", artist: "Carly Rae Jepsen", era: "Modern hits", mood: "Pop" },
  { title: "Eye of the Tiger", artist: "Survivor", era: "Classic pop", mood: "Power" },
  { title: "SexyBack", artist: "Justin Timberlake", era: "Modern hits", mood: "R&B" },
  { title: "Wonderwall", artist: "Oasis", era: "Classic pop", mood: "Rock" },
  { title: "When I Was Your Man", artist: "Bruno Mars", era: "Modern hits", mood: "Ballad" },
  { title: "Love Story", artist: "Taylor Swift", era: "Classic pop", mood: "Ballad" },
  { title: "Teenage Dream", artist: "Katy Perry", era: "Modern hits", mood: "Pop" },
  { title: "Take On Me", artist: "A-ha", era: "Classic pop", mood: "New wave" },
  { title: "Walking on Sunshine", artist: "Katrina and the Waves", era: "Classic pop", mood: "Feel-good" },
  { title: "Blue Suede Shoes", artist: "Elvis Presley", era: "Classics", mood: "Rock" },
  { title: "Raspberry Beret", artist: "Prince", era: "Classics", mood: "Funk" },
  { title: "Funkytown", artist: "Lipps Inc.", era: "Classics", mood: "Disco" },
  { title: "Everybody Wants to Rule the World", artist: "Tears for Fears", era: "Classic pop", mood: "New wave" },
  { title: "Kiss from a Rose", artist: "Seal", era: "Ballad", mood: "Ballad" },
  { title: "Losing My Religion", artist: "R.E.M.", era: "Classic pop", mood: "Alternative" },
  { title: "All Star", artist: "Smash Mouth", era: "Classic pop", mood: "Rock" },
  { title: "Conga", artist: "Miami Sound Machine", era: "Classics", mood: "Latin" },
  { title: "I Wanna Dance with Somebody", artist: "Whitney Houston", era: "Classics", mood: "Pop" },
  { title: "You Shook Me All Night Long", artist: "AC/DC", era: "Classics", mood: "Rock" }
];

// Remote image load timeout (milliseconds). If a remote image doesn't finish
// loading within this time, the code falls back to the local `image_url_local`.
const REMOTE_IMAGE_TIMEOUT_MS = 4000;

let songs = [];
const songGrid = document.getElementById("songGrid");
const searchInput = document.getElementById("searchInput");
const tagRow = document.getElementById("tagRow");
const shuffleBg = document.getElementById("shuffleBg");

window.__debugLastError = null;
window.addEventListener('error', event => {
  window.__debugLastError = event.message || String(event.error);
  const banner = document.getElementById('debugBanner');
  if (banner) {
    banner.textContent = `Debug error: ${window.__debugLastError}`;
    banner.classList.add('visible');
  }
});

let activeFilter = "All";

let currentAudio = null;
let currentPlayBtn = null;

function togglePreview(song, btn) {
  if (currentAudio && !currentAudio.paused) {
    if (currentPlayBtn === btn) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      btn.textContent = "▶";
      btn.classList.remove("playing");
      currentAudio = null;
      currentPlayBtn = null;
      return;
    }
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentPlayBtn.textContent = "▶";
    currentPlayBtn.classList.remove("playing");
  }
  const audio = new Audio(song.preview_url_local);
  audio.play();
  btn.textContent = "⏹";
  btn.classList.add("playing");
  audio.addEventListener("ended", () => {
    btn.textContent = "▶";
    btn.classList.remove("playing");
    currentAudio = null;
    currentPlayBtn = null;
  });
  currentAudio = audio;
  currentPlayBtn = btn;
}

function applyBackground() {
  const image = backgroundPool[Math.floor(Math.random() * backgroundPool.length)];
  document.body.style.backgroundImage = `linear-gradient(135deg, rgba(20, 20, 48, 0.58), rgba(28, 20, 46, 0.64)), url(${image})`;
}

function eraFromYear(year) {
  const y = parseInt(year, 10);
  if (Number.isNaN(y)) return "Other";
  return y < 1960 ? "1950s & earlier" : `${Math.floor(y / 10) * 10}s`;
}

function normalizeSongs(data) {
  if (!Array.isArray(data)) {
    return [];
  }

  return data.map(song => ({
    title: song.title || "Untitled song",
    artist: song.artist || "Unknown artist",
    era: song.era || eraFromYear(song.year),
    mood: song.mood || "Unknown",
    album_title: song.album_title || null,
    image_url: song.image_url || null,
    image_url_local: song.image_url_local || null,
    preview_url_local: song.preview_url_local || null,
    game: song.game || "Unknown game",
    year: song.year || null,
    searchText: [song.title, song.artist, song.game, song.year, song.album_title]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
  }));
}

function loadImageWithTimeout(url, timeout) {
  return new Promise((resolve, reject) => {
    if (!url) return reject(new Error('no url'));
    const img = new Image();
    let finished = false;
    const timer = setTimeout(() => {
      if (finished) return;
      finished = true;
      // timeout -> reject so caller can use local fallback
      try { img.src = ''; } catch (e) {}
      reject(new Error('timeout'));
    }, timeout);

    img.onload = () => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve(url);
    };
    img.onerror = () => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      reject(new Error('error'));
    };

    // Kick off load
    img.src = url;
  });
}

function renderTags() {
  const eras = [...new Set(songs.map(song => song.era))].sort();
  tagRow.innerHTML = "";

  ["All", ...eras].forEach(era => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `tag ${activeFilter === era ? "active" : ""}`;
    button.textContent = era;
    button.addEventListener("click", () => {
      activeFilter = era;
      renderTags();
      renderSongs();
    });
    tagRow.appendChild(button);
  });
}

function renderSongs() {
  const term = searchInput.value.toLowerCase().trim();
  const filtered = songs.filter(song => {
    const matchesFilter = activeFilter === "All" || song.era === activeFilter;
    const matchesQuery = !term || [song.title, song.artist, song.game, song.year]
      .filter(Boolean)
      .some(value => String(value).toLowerCase().includes(term));
    return matchesFilter && matchesQuery;
  });

  songGrid.innerHTML = "";

  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No songs match that search yet. Try another keyword or era.";
    songGrid.appendChild(empty);
    return;
  }

  filtered.forEach(song => {
    const card = document.createElement("article");
    card.className = "song-card";

    if (song.image_url || song.image_url_local) {
      card.classList.add("has-image");
      const art = document.createElement("div");
      art.className = "song-art";
      const img = document.createElement("img");
      img.alt = `Album art for ${song.title}`;

      // Prefer remote image, but fall back to local copy if remote fails
      const remote = song.image_url;
      const local = song.image_url_local;

      if (remote && local) {
        // Try remote with a short timeout, otherwise use local copy
        loadImageWithTimeout(remote, REMOTE_IMAGE_TIMEOUT_MS).then(src => {
          img.src = src;
        }).catch(() => {
          img.src = local;
        });
      } else if (remote) {
        img.src = remote;
      } else if (local) {
        img.src = local;
      }

      art.appendChild(img);

      if (song.preview_url_local) {
        card.classList.add("has-preview");
        const playBtn = document.createElement("button");
        playBtn.className = "play-btn";
        playBtn.textContent = "▶";
        playBtn.setAttribute("aria-label", `Preview ${song.title}`);
        playBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          togglePreview(song, playBtn);
        });
        art.appendChild(playBtn);
      }

      card.appendChild(art);
    }

    const content = document.createElement("div");
    content.className = "song-content";

    const title = document.createElement("h3");
    title.textContent = song.title;

    const note = document.createElement("p");
    note.textContent = `${song.artist} • ${song.album_title || song.mood}`;

    const meta = document.createElement("div");
    meta.className = "song-meta";

    const era = document.createElement("span");
    era.textContent = song.era;

    const album = document.createElement("span");
    album.textContent = song.album_title || song.mood;

    const game = document.createElement("span");
    game.textContent = song.game;

    const year = document.createElement("span");
    year.textContent = song.year ? String(song.year) : "Year unavailable";

    meta.append(era, album, game, year);
    content.append(title, note, meta);
    card.appendChild(content);
    songGrid.appendChild(card);
  });
}

async function loadSongs() {
  try {
    const response = await fetch("songs.json", { cache: "no-store" });

    if (!response.ok) {
      throw new Error(`Failed to load songs.json: ${response.status}`);
    }

    const data = await response.json();
    songs = normalizeSongs(data);

    if (!songs.length) {
      throw new Error("songs.json is empty");
    }
  } catch (error) {
    console.warn("Using fallback song data:", error);
    songs = normalizeSongs(fallbackSongs);
  }

  renderTags();
  renderSongs();
}

searchInput.addEventListener("input", renderSongs);
shuffleBg.addEventListener("click", applyBackground);

function showDebugBanner(message) {
  const banner = document.getElementById("debugBanner");
  if (banner) {
    banner.textContent = message;
    banner.classList.add("visible");
  }
}

applyBackground();
loadSongs().then(() => {
  showDebugBanner("Debug: script.js v3 loaded — songs ready.");
}).catch(() => {
  showDebugBanner("Debug: script.js v3 loaded — failed to load songs.");
});
