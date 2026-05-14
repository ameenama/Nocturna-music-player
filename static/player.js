// ── Nocturna Sidebar Player JS ──

const audio = document.getElementById('sidebarAudio');
let playlist = [];
let currentIndex = 0;
let isCollapsed = false;
let hasEverPlayed = false;

// ── Show / hide sidebar ──────────────────────────────────────────────────────

function showSidebar() {
    const sidebar = document.getElementById('playerSidebar');
    sidebar.classList.add('visible');
    sidebar.classList.remove('collapsed');
    document.body.classList.add('player-open');
    isCollapsed = false;
    hasEverPlayed = true;
}

function togglePlayer() {
    const sidebar = document.getElementById('playerSidebar');
    isCollapsed = !isCollapsed;
    if (isCollapsed) {
        sidebar.classList.remove('visible');
        sidebar.classList.add('collapsed');
    } else {
        sidebar.classList.add('visible');
        sidebar.classList.remove('collapsed');
    }
}

// ── Play a track ─────────────────────────────────────────────────────────────

function playTrack(audioUrl, trackName, artistName, imageUrl) {
    const sidebar = document.getElementById('playerSidebar');
    sidebar.classList.add('visible');
    sidebar.classList.remove('collapsed');
    isCollapsed = false;

    audio.src = audioUrl;
    audio.volume = getVolume();
    audio.play();

    document.getElementById('sidebarTrackName').textContent = trackName;
    document.getElementById('sidebarArtistName').textContent = artistName;

    const artImg = document.getElementById('sidebarArt');
    const placeholder = document.getElementById('artPlaceholder');

    if (imageUrl) {
        artImg.src = imageUrl;
        artImg.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        artImg.style.display = 'none';
        placeholder.style.display = 'flex';
    }

    showPauseIcon();
    updateQueueHighlight();
}

// ── Register a playlist so Prev/Next work ────────────────────────────────────
// Call this from each page after building the track list.
// Each item: { audio, name, artist, image }

function setPlaylist(tracks, startIndex) {
    playlist = tracks;
    currentIndex = startIndex || 0;
    renderQueue();
}

function addToPlaylist(track) {
    playlist.push(track);
    renderQueue();
}

// ── Controls ─────────────────────────────────────────────────────────────────

function togglePlay() {
    if (!audio.src) return;
    if (audio.paused) { audio.play(); showPauseIcon(); }
    else              { audio.pause(); showPlayIcon(); }
}

function prevTrack() {
    if (!playlist.length) return;
    currentIndex = (currentIndex - 1 + playlist.length) % playlist.length;
    const t = playlist[currentIndex];
    playTrack(t.audio, t.name, t.artist, t.image);
}

function nextTrack() {
    if (!playlist.length) return;
    currentIndex = (currentIndex + 1) % playlist.length;
    const t = playlist[currentIndex];
    playTrack(t.audio, t.name, t.artist, t.image);
}

function showPlayIcon() {
    document.getElementById('playIcon').style.display  = 'block';
    document.getElementById('pauseIcon').style.display = 'none';
}

function showPauseIcon() {
    document.getElementById('playIcon').style.display  = 'none';
    document.getElementById('pauseIcon').style.display = 'block';
}

// ── Progress ─────────────────────────────────────────────────────────────────

audio.addEventListener('timeupdate', function () {
    if (!audio.duration) return;
    const pct = (audio.currentTime / audio.duration) * 100;
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressDot').style.left  = pct + '%';
    document.getElementById('currentTime').textContent = formatTime(audio.currentTime);
    document.getElementById('totalTime').textContent   = formatTime(audio.duration);
});

audio.addEventListener('ended',  nextTrack);
audio.addEventListener('pause',  showPlayIcon);
audio.addEventListener('play',   showPauseIcon);

function seekAudio(e) {
    const bar  = document.getElementById('progressBar');
    const rect = bar.getBoundingClientRect();
    const pct  = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
    if (audio.duration) audio.currentTime = pct * audio.duration;
}

// ── Volume ────────────────────────────────────────────────────────────────────

function getVolume() {
    const fill = document.getElementById('volumeFill');
    return parseFloat(fill.style.width) / 100 || 0.8;
}

function setVolume(e) {
    const bar  = document.getElementById('volumeBar');
    const rect = bar.getBoundingClientRect();
    const pct  = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
    audio.volume = pct;
    document.getElementById('volumeFill').style.width = (pct * 100) + '%';
    document.getElementById('volumeDot').style.left   = (pct * 100) + '%';
}

// ── Queue rendering ───────────────────────────────────────────────────────────

function renderQueue() {
    const queueEl = document.getElementById('playerQueue');
    if (!queueEl) return;
    queueEl.innerHTML = '';
    const upcoming = playlist.slice(currentIndex + 1, currentIndex + 4);
    upcoming.forEach((t, i) => {
        const realIndex = currentIndex + 1 + i;
        const item = document.createElement('div');
        item.className = 'queue-item';
        item.innerHTML = `
            <img class="queue-thumb" src="${t.image || ''}" alt="" onerror="this.style.display='none'">
            <div class="queue-info">
                <div class="queue-name">${t.name}</div>
                <div class="queue-artist">${t.artist}</div>
            </div>
        `;
        item.onclick = () => {
            currentIndex = realIndex;
            const tr = playlist[currentIndex];
            playTrack(tr.audio, tr.name, tr.artist, tr.image);
        };
        queueEl.appendChild(item);
    });
}

function updateQueueHighlight() {
    renderQueue();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTime(secs) {
    if (isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
}
const API_KEY = "AIzaSyB2xqyFBY8SV9zrdD7oKwzyR0r4YJS6P5E";
let ytPlayer;

function onYouTubeIframeAPIReady() {
    ytPlayer = new YT.Player('youtube-player', {
        height: '0',
        width: '0',
        videoId: '',
        playerVars: {
            autoplay: 1
        }
    });
}

function playYouTubeSong(videoId) {
    ytPlayer.loadVideoById(videoId);
}
async function searchYouTube(songName) {

    const API_KEY = "YOUR_API_KEY";

    const response = await fetch(
        `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${songName}&type=video&videoCategoryId=10&maxResults=1&key=${API_KEY}`
    );

    const data = await response.json();

    if (data.items.length > 0) {
        const videoId = data.items[0].id.videoId;

        playYouTubeSong(videoId);
    }
}