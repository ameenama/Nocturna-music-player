// ── Nocturna Sidebar Player ──

const audio = document.getElementById('sidebarAudio');
let playlist = [];
let currentIndex = 0;
let isCollapsed = true;
let ytPlayer = null;
let currentMode = 'jamendo'; // 'jamendo' or 'youtube'

// ── YouTube IFrame API ────────────────────────────────────────────────────────

function onYouTubeIframeAPIReady() {
    ytPlayer = new YT.Player('yt-iframe', {
        height: '160',
        width: '200',
        videoId: '',
        playerVars: {
            autoplay: 1,
            controls: 0,
            modestbranding: 1,
            rel: 0,
            showinfo: 0
        },
        events: {
            onReady: function(e) {
                console.log('YouTube player ready');
            },
            onStateChange: function(e) {
                if (e.data === YT.PlayerState.PLAYING) showPauseIcon();
                if (e.data === YT.PlayerState.PAUSED) showPlayIcon();
                if (e.data === YT.PlayerState.ENDED) nextTrack();
            }
        }
    });
}

// ── Show / hide sidebar ───────────────────────────────────────────────────────

function showSidebar() {
    const sidebar = document.getElementById('playerSidebar');
    sidebar.classList.add('visible');
    sidebar.classList.remove('collapsed');
    isCollapsed = false;
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

// ── Play Jamendo track ────────────────────────────────────────────────────────

function playTrack(audioUrl, trackName, artistName, imageUrl) {
    currentMode = 'jamendo';
    showSidebar();

    // Stop YouTube if playing
    if (ytPlayer && ytPlayer.stopVideo) ytPlayer.stopVideo();

    // Show Jamendo art, hide YouTube (defensive: some pages don't include YouTube/Jamendo wrapper ids)
    const ytWrap = document.getElementById('ytPlayerWrap');
    if (ytWrap) ytWrap.style.display = 'none';

    const jamendoControls = document.getElementById('jamendoControls');
    if (jamendoControls) jamendoControls.style.display = 'flex';

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

    document.getElementById('sidebarTrackName').textContent = trackName;
    document.getElementById('sidebarArtistName').textContent = artistName;

    audio.src = audioUrl;
    audio.volume = getVolume();
    audio.play();
    showPauseIcon();
    updateQueueHighlight();
}

let ytProgressTimer = null;

// ── Play YouTube track ────────────────────────────────────────────────────────

function playYouTubeTrack(videoId, title, channel, thumbnail) {
    currentMode = 'youtube';
    showSidebar();

    // Stop Jamendo audio
    audio.pause();
    audio.src = '';

    // Stop Jamendo progress-driven updates
    // (Jamendo already drives progress with timeupdate; YouTube will use a timer)
    if (ytProgressTimer) {
        clearInterval(ytProgressTimer);
        ytProgressTimer = null;
    }

    // Ensure required DOM exists (player.html includes all of these)
    const trackNameEl = document.getElementById('sidebarTrackName');
    const artistNameEl = document.getElementById('sidebarArtistName');
    if (trackNameEl) trackNameEl.textContent = title;
    if (artistNameEl) artistNameEl.textContent = channel;

    const sidebarArt = document.getElementById('sidebarArt');
    const artPlaceholder = document.getElementById('artPlaceholder');
    const ytWrap = document.getElementById('ytPlayerWrap');
    const jamendoControls = document.getElementById('jamendoControls');

    if (ytWrap) ytWrap.style.display = 'block';
    if (jamendoControls) jamendoControls.style.display = 'none';

    // Thumbnail: show when available (user requested: visible in player sidebar in YouTube mode)
    // If no thumbnail, keep placeholder visible.
    if (sidebarArt) {
        if (thumbnail) {
            sidebarArt.src = thumbnail;
            sidebarArt.style.display = 'block';
            if (artPlaceholder) artPlaceholder.style.display = 'none';
        } else {
            sidebarArt.style.display = 'none';
            if (artPlaceholder) artPlaceholder.style.display = 'flex';
        }
    }

    showPauseIcon();

    const load = () => {
        if (ytPlayer && typeof ytPlayer.loadVideoById === 'function') {
            ytPlayer.loadVideoById(videoId);
            return true;
        }
        return false;
    };

    if (!load()) {
        const interval = setInterval(() => {
            if (load()) clearInterval(interval);
        }, 300);
    }

    // Progress (YouTube only)
    const updateProgress = () => {
        if (!ytPlayer) return;
        const cur = ytPlayer.getCurrentTime ? ytPlayer.getCurrentTime() : 0;
        const dur = ytPlayer.getDuration ? ytPlayer.getDuration() : 0;

        if (cur !== undefined && !isNaN(cur)) {
            const fillPct = dur && dur > 0 ? (cur / dur) * 100 : 0;
            const progressFill = document.getElementById('progressFill');
            const progressDot = document.getElementById('progressDot');
            const currentTime = document.getElementById('currentTime');
            const totalTime = document.getElementById('totalTime');

            if (progressFill) progressFill.style.width = Math.min(Math.max(fillPct, 0), 100) + '%';
            if (progressDot) progressDot.style.left = Math.min(Math.max(fillPct, 0), 100) + '%';
            if (currentTime) currentTime.textContent = formatTime(cur);
            if (totalTime) totalTime.textContent = dur && dur > 0 ? formatTime(dur) : '0:00';
        }
    };

    // Poll while YouTube is active (simple + robust)
    ytProgressTimer = setInterval(updateProgress, 250);
}

// ── Playlist ──────────────────────────────────────────────────────────────────

function setPlaylist(tracks, startIndex) {
    playlist = tracks;
    currentIndex = startIndex || 0;
    renderQueue();
}

function addToPlaylist(track) {
    playlist.push(track);
    renderQueue();
}

// ── Controls ──────────────────────────────────────────────────────────────────

function togglePlay() {
    if (currentMode === 'youtube') {
        if (!ytPlayer) return;
        const state = ytPlayer.getPlayerState();
        if (state === YT.PlayerState.PLAYING) {
            ytPlayer.pauseVideo();
            showPlayIcon();
        } else {
            ytPlayer.playVideo();
            showPauseIcon();
        }
    } else {
        if (!audio.src) return;
        if (audio.paused) {
            audio.play();
            showPauseIcon();
        } else {
            audio.pause();
            showPlayIcon();
        }
    }
}

function prevTrack() {
    if (!playlist.length) return;
    currentIndex = (currentIndex - 1 + playlist.length) % playlist.length;
    const t = playlist[currentIndex];
    // For now, queue navigation is Jamendo-only since tracks in queue are Jamendo objects.
    playTrack(t.audio, t.name, t.artist, t.image);
}


function nextTrack() {
    if (!playlist.length) return;
    currentIndex = (currentIndex + 1) % playlist.length;
    const t = playlist[currentIndex];
    playTrack(t.audio, t.name, t.artist, t.image);
}

function showPlayIcon() {
    document.getElementById('playIcon').style.display = 'block';
    document.getElementById('pauseIcon').style.display = 'none';
}

function showPauseIcon() {
    document.getElementById('playIcon').style.display = 'none';
    document.getElementById('pauseIcon').style.display = 'block';
}

// ── Progress (Jamendo only) ───────────────────────────────────────────────────

audio.addEventListener('timeupdate', function() {
    if (!audio.duration) return;
    const pct = (audio.currentTime / audio.duration) * 100;
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('progressDot').style.left = pct + '%';
    document.getElementById('currentTime').textContent = formatTime(audio.currentTime);
    document.getElementById('totalTime').textContent = formatTime(audio.duration);
});

audio.addEventListener('ended', nextTrack);
audio.addEventListener('pause', showPlayIcon);
audio.addEventListener('play', showPauseIcon);

function seekAudio(e) {
    const bar = document.getElementById('progressBar');
    const rect = bar.getBoundingClientRect();
    const pct = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
    if (audio.duration) audio.currentTime = pct * audio.duration;
}

// ── Volume ────────────────────────────────────────────────────────────────────

function getVolume() {
    const fill = document.getElementById('volumeFill');
    return parseFloat(fill.style.width) / 100 || 0.8;
}

function setVolume(e) {
    const bar = document.getElementById('volumeBar');
    const rect = bar.getBoundingClientRect();
    const pct = Math.min(Math.max((e.clientX - rect.left) / rect.width, 0), 1);
    audio.volume = pct;
    if (ytPlayer && ytPlayer.setVolume) ytPlayer.setVolume(pct * 100);
    document.getElementById('volumeFill').style.width = (pct * 100) + '%';
    document.getElementById('volumeDot').style.left = (pct * 100) + '%';
}

// ── Queue ─────────────────────────────────────────────────────────────────────

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

function updateQueueHighlight() { renderQueue(); }

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatTime(secs) {
    if (isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
}
/* duplicate playYouTubeTrack removed (merged into the earlier definition) */
async function loadPodcasts() {

    const response = await fetch(
        '/podcast-search?query=trending podcasts'
    );

    const data = await response.json();

    console.log(data);

    displayPodcasts(data.results);
}
function displayPodcasts(podcasts) {

    const container = document.getElementById('podcast-container');

    container.innerHTML = '';

    podcasts.forEach(podcast => {

        container.innerHTML += `

            <div class="podcast-card">

                <img src="${podcast.image}" width="180">

                <h3>${podcast.title_original}</h3>

                <p>${podcast.publisher_original}</p>

            </div>

        `;
    });
}
window.addEventListener('DOMContentLoaded', () => {

    loadPodcasts();

});
container.innerHTML += `

<div class="podcast-card"
     onclick="playPodcast('${podcast.id}')">

    <img src="${podcast.image}" class="podcast-image">

    <h3>${podcast.title_original}</h3>

    <p>${podcast.publisher_original}</p>

</div>

`;
async function playPodcast(podcastId) {

    const response = await fetch(
        `/podcast-episodes/${podcastId}`
    );

    const data = await response.json();

     console.log("CLICKED:", podcastId);

    if (data.episodes && data.episodes.length > 0) {

        const firstEpisode = data.episodes[0];

        const audioUrl = firstEpisode.audio;

        const player = document.getElementById('podcast-player');

        player.src = audioUrl;

        player.play();
    }
}