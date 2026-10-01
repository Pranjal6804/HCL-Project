// Base API URL
const API_BASE = "http://127.0.0.1:5000";

// =========================================================
// 🎬 CINEMATIC HERO SLIDER DATASET & CONTROLLER
// =========================================================
const HERO_SLIDES = [
  {
    title: "Inception",
    year: "2010",
    rating: "⭐ 8.8",
    duration: "2h 28m",
    genres: ["Sci-Fi", "Action", "Mind-Bending"],
    primaryGenre: "Sci-Fi",
    description: "A skilled thief who steals corporate secrets through dream-sharing technology is offered a chance to have his criminal history erased as payment for the inverse task: planting an idea into the mind of a CEO.",
    backdrop: "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg",
    trailerId: "YoHD9XEInc0",
    accentColor: "rgba(0, 240, 255, 0.16)"
  },
  {
    title: "The Dark Knight",
    year: "2008",
    rating: "⭐ 9.0",
    duration: "2h 32m",
    genres: ["Action", "Crime", "Thriller"],
    primaryGenre: "Action",
    description: "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
    backdrop: "https://upload.wikimedia.org/wikipedia/en/1/1c/The_Dark_Knight_%282008_film%29.jpg",
    trailerId: "EXeTwQWrcwY",
    accentColor: "rgba(59, 130, 246, 0.16)"
  },
  {
    title: "Interstellar",
    year: "2014",
    rating: "⭐ 8.7",
    duration: "2h 49m",
    genres: ["Sci-Fi", "Adventure", "Drama"],
    primaryGenre: "Adventure",
    description: "When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft along with a team of researchers to find a new planet for humans.",
    backdrop: "https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg",
    trailerId: "zSWdZVtXT7E",
    accentColor: "rgba(168, 85, 247, 0.16)"
  },
  {
    title: "The Matrix",
    year: "1999",
    rating: "⭐ 8.7",
    duration: "2h 16m",
    genres: ["Sci-Fi", "Action", "Cyberpunk"],
    primaryGenre: "Cyberpunk",
    description: "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth--the life he knows is the elaborate deception of an evil cyber-intelligence.",
    backdrop: "https://upload.wikimedia.org/wikipedia/en/d/db/The_Matrix.png",
    trailerId: "vKQi3bBA1y8",
    accentColor: "rgba(16, 185, 129, 0.16)"
  },
  {
    title: "Pulp Fiction",
    year: "1994",
    rating: "⭐ 8.9",
    duration: "2h 34m",
    genres: ["Crime", "Drama", "Cult Classic"],
    primaryGenre: "Crime",
    description: "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption in Los Angeles.",
    backdrop: "https://upload.wikimedia.org/wikipedia/en/3/3b/Pulp_Fiction_%281994%29_poster.jpg",
    trailerId: "s7EdQ4FqbhY",
    accentColor: "rgba(245, 158, 11, 0.16)"
  },
  {
    title: "Electric Heart",
    year: "2020",
    rating: "⭐ 7.8",
    duration: "1h 45m",
    genres: ["Drama", "Indie Music", "Romance"],
    primaryGenre: "Indie Music",
    description: "An evocative musical journey exploring deep romantic resonance, sound design obsession, and acoustic discovery between two independent musicians.",
    backdrop: "https://upload.wikimedia.org/wikipedia/en/e/ee/EDposter1984.jpg",
    trailerId: "YoHD9XEInc0",
    accentColor: "rgba(0, 240, 255, 0.18)"
  }
];

let heroCurrentIndex = 0;
let heroSlideTimer = null;
let watchlist = JSON.parse(localStorage.getItem("cinepulse_watchlist") || "[]");
let userRatings = JSON.parse(localStorage.getItem("cinepulse_user_ratings") || "[]");
let currentHybridMode = "hybrid";
let activeModalMovie = null;
let currentRecommendations = [];
let currentAnchorQuery = "Inception";

// Hero DOM Elements
const heroBackdropContainer = document.getElementById("hero-backdrop-container");
const heroIndicatorsContainer = document.getElementById("hero-indicators");
const heroTitle = document.getElementById("hero-title");
const heroRating = document.getElementById("hero-rating");
const heroYear = document.getElementById("hero-year");
const heroDuration = document.getElementById("hero-duration");
const heroDescription = document.getElementById("hero-description");
const heroGenrePrimary = document.getElementById("hero-genre-primary");
const heroTagsRow = document.getElementById("hero-tags-row");
const ambientGlow = document.getElementById("ambient-glow");
const watchlistCountElem = document.getElementById("watchlist-count");
const favIcon = document.getElementById("fav-icon");
const favText = document.getElementById("fav-text");

// Initialize Hero Slider DOM
function initHeroSlider() {
  if (!heroBackdropContainer) return;

  heroBackdropContainer.innerHTML = `
    <div class="hero-backdrop-track" id="hero-backdrop-track">
      ${HERO_SLIDES.map((slide, idx) => `
        <div class="hero-slide-bg ${idx === 0 ? 'active' : ''}" id="hero-bg-${idx}" style="background-image: url('${slide.backdrop}');"></div>
      `).join("")}
    </div>
  `;

  if (heroIndicatorsContainer) {
    heroIndicatorsContainer.innerHTML = HERO_SLIDES.map((_, idx) => `
      <div class="hero-bar-item ${idx === 0 ? 'active' : ''}" onclick="goToHeroSlide(${idx})"></div>
    `).join("");
  }

  updateHeroContent(0);
  updateWatchlistBadge();
  startHeroTimer();
}

function updateHeroContent(index) {
  const movie = HERO_SLIDES[index];
  if (!movie) return;

  // Apply smooth 2-second sliding effect on the background poster track
  const track = document.getElementById("hero-backdrop-track");
  if (track) {
    track.style.transform = `translateX(-${index * 100}%)`;
  }

  heroTitle.style.opacity = 0;
  heroDescription.style.opacity = 0;

  setTimeout(() => {
    heroTitle.textContent = movie.title;
    heroRating.textContent = movie.rating;
    heroYear.textContent = movie.year;
    heroDuration.textContent = movie.duration;
    heroGenrePrimary.textContent = movie.primaryGenre;
    heroDescription.textContent = movie.description;

    heroTagsRow.innerHTML = movie.genres
      .map(g => `<span class="hero-tag">${g}</span>`)
      .join("");

    if (ambientGlow) {
      ambientGlow.style.background = `radial-gradient(circle, ${movie.accentColor} 0%, rgba(168, 85, 247, 0.08) 50%, transparent 75%)`;
    }

    const isFav = watchlist.some(item => item.title.toLowerCase() === movie.title.toLowerCase());
    if (favIcon && favText) {
      favIcon.textContent = isFav ? "♥" : "♡";
      favIcon.style.color = isFav ? "#ec4899" : "";
      favText.textContent = isFav ? "Saved" : "Watchlist";
    }

    heroTitle.style.opacity = 1;
    heroDescription.style.opacity = 1;
  }, 220);

  HERO_SLIDES.forEach((_, idx) => {
    const bgElem = document.getElementById(`hero-bg-${idx}`);
    if (bgElem) {
      if (idx === index) bgElem.classList.add("active");
      else bgElem.classList.remove("active");
    }
  });

  const indicators = document.querySelectorAll(".hero-bar-item");
  indicators.forEach((bar, idx) => {
    if (idx === index) bar.classList.add("active");
    else bar.classList.remove("active");
  });
}

function nextHeroSlide() {
  heroCurrentIndex = (heroCurrentIndex + 1) % HERO_SLIDES.length;
  updateHeroContent(heroCurrentIndex);
}

function prevHeroSlide() {
  heroCurrentIndex = (heroCurrentIndex - 1 + HERO_SLIDES.length) % HERO_SLIDES.length;
  updateHeroContent(heroCurrentIndex);
}

function goToHeroSlide(index) {
  heroCurrentIndex = index;
  updateHeroContent(heroCurrentIndex);
  resetHeroTimer();
}

function startHeroTimer() {
  clearInterval(heroSlideTimer);
  heroSlideTimer = setInterval(nextHeroSlide, 5500);
}

function resetHeroTimer() {
  clearInterval(heroSlideTimer);
  heroSlideTimer = setInterval(nextHeroSlide, 5500);
}

const heroSection = document.getElementById("hero");
if (heroSection) {
  heroSection.addEventListener("mouseenter", () => clearInterval(heroSlideTimer));
  heroSection.addEventListener("mouseleave", () => startHeroTimer());
}

function triggerHeroRecommendation() {
  const currentMovie = HERO_SLIDES[heroCurrentIndex];
  if (!currentMovie) return;

  const movieInput = document.getElementById("movie-input");
  if (movieInput) {
    movieInput.value = currentMovie.title;
  }

  fetchRecommendations(currentMovie.title, currentHybridMode);

  const discoverSection = document.getElementById("discover");
  if (discoverSection) {
    discoverSection.scrollIntoView({ behavior: "smooth" });
  }
}

function toggleHeroWatchlist() {
  const currentMovie = HERO_SLIDES[heroCurrentIndex];
  if (!currentMovie) return;

  const existingIdx = watchlist.findIndex(item => item.title.toLowerCase() === currentMovie.title.toLowerCase());
  if (existingIdx >= 0) {
    watchlist.splice(existingIdx, 1);
    showToast(`Removed "${currentMovie.title}" from Watchlist`);
  } else {
    watchlist.push({
      title: currentMovie.title,
      clean_title: currentMovie.title,
      year: currentMovie.year,
      poster_url: currentMovie.backdrop,
      genres: currentMovie.genres.join("|")
    });
    showToast(`Added "${currentMovie.title}" to Watchlist! ⭐`);
  }

  localStorage.setItem("cinepulse_watchlist", JSON.stringify(watchlist));
  updateWatchlistBadge();
  updateHeroContent(heroCurrentIndex);
}

function updateWatchlistBadge() {
  if (watchlistCountElem) {
    watchlistCountElem.textContent = watchlist.length;
  }
}

// =========================================================
// 🎬 TRAILER MODAL CONTROLLER
// =========================================================
const trailerModal = document.getElementById("trailer-modal");
const trailerIframe = document.getElementById("trailer-iframe");
const trailerTitle = document.getElementById("trailer-title");

function openTrailerModal() {
  const currentMovie = HERO_SLIDES[heroCurrentIndex];
  if (!currentMovie || !trailerModal) return;

  trailerTitle.textContent = `${currentMovie.title} (${currentMovie.year}) — Official Trailer`;
  trailerIframe.src = `https://www.youtube.com/embed/${currentMovie.trailerId}?autoplay=1&rel=0`;
  trailerModal.classList.remove("hidden");
}

function closeTrailerModal() {
  if (!trailerModal) return;
  trailerModal.classList.add("hidden");
  trailerIframe.src = "";
}

if (trailerModal) {
  trailerModal.addEventListener("click", (e) => {
    if (e.target === trailerModal) closeTrailerModal();
  });
}

// =========================================================
// 🔘 HYBRID RECOMMENDER TOGGLE CONTROLLER
// =========================================================
function setHybridMode(mode) {
  currentHybridMode = mode;
  const buttons = document.querySelectorAll("#hybrid-mode-toggle .segment-btn");
  buttons.forEach(btn => {
    if (btn.getAttribute("data-mode") === mode) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  const modeLabels = {
    content: "Mode: Content Similar (TF-IDF + KNN)",
    hybrid: "Mode: Hybrid Blend (0.55 Content + 0.45 SVD)",
    crowd: "Mode: Viewer Crowd Taste (SVD Collaborative)"
  };

  const modeIndicator = document.getElementById("current-mode-indicator");
  if (modeIndicator) {
    modeIndicator.textContent = modeLabels[mode] || "Mode: Hybrid";
  }

  showToast(`Switched to ${modeLabels[mode]}`);

  // Re-run recommendation if movie active
  if (currentAnchorQuery) {
    fetchRecommendations(currentAnchorQuery, mode);
  }
}

// =========================================================
// 🎭 MOOD-BASED RECOMMENDER CONTROLLER
// =========================================================
async function selectMood(moodKey, btnElem) {
  const pills = document.querySelectorAll(".mood-pill");
  pills.forEach(p => p.classList.remove("active"));
  if (btnElem) btnElem.classList.add("active");

  const loader = document.getElementById("loader");
  const loaderText = document.getElementById("loader-text");
  const resultsSection = document.getElementById("results-section");
  const movieGrid = document.getElementById("movie-grid");
  const queryBanner = document.getElementById("query-banner");
  const errorMessage = document.getElementById("error-message");
  const resultsCount = document.getElementById("results-count");
  const resultsSubtitle = document.getElementById("results-subtitle");

  errorMessage.classList.add("hidden");
  resultsSection.classList.add("hidden");
  queryBanner.classList.add("hidden");
  if (loaderText) loaderText.textContent = `Curating ${moodKey.replace(/_/g, ' ')} cinematic selections...`;
  loader.classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/mood?mood=${encodeURIComponent(moodKey)}`);
    const data = await res.json();
    loader.classList.add("hidden");

    if (!res.ok || !data.movies || data.movies.length === 0) {
      showError(`No titles found matching mood "${moodKey}".`);
      return;
    }

    currentRecommendations = data.movies.map(m => ({
      ...m,
      match_score: "Mood Pick",
      score_numeric: 95.0,
      shared_themes: data.genres,
      xai_explanation: `Curated for your "${moodKey.replace(/_/g, ' ')}" mood based on matching tonal genres (${data.genres.join(", ")}).`
    }));

    if (resultsSubtitle) resultsSubtitle.textContent = `Curated for mood: ${moodKey.replace(/_/g, ' ').toUpperCase()}`;
    resultsCount.textContent = `${data.movies.length} mood picks`;

    movieGrid.innerHTML = currentRecommendations.map((m, idx) => renderCardHtml(m, idx)).join("");
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    loader.classList.add("hidden");
    showError("Could not connect to Mood Engine. Make sure app.py is running on port 5000.");
  }
}

// =========================================================
// 🍿 NETFLIX / HBO MAX STYLE HORIZONTAL ROW CAROUSELS
// =========================================================
async function loadCuratedCategories() {
  try {
    const res = await fetch(`${API_BASE}/api/categories`);
    if (!res.ok) return;
    const catalog = await res.json();

    renderTrackItems("cult-classics-track", catalog.cult_classics || []);
    renderTrackItems("mind-bending-track", catalog.mind_bending || []);
    renderTrackItems("sci-fi-track", catalog.sci_fi || []);
    renderTrackItems("animated-track", catalog.animated || []);
  } catch (err) {
    console.error("Failed to load curated categories:", err);
  }
}

function renderTrackItems(trackId, movies) {
  const track = document.getElementById(trackId);
  if (!track) return;

  track.innerHTML = movies.map(m => {
    const titleEscaped = m.title.replace(/'/g, "\\'");
    const fallbackSvg = `/api/poster-image?title=${encodeURIComponent(titleEscaped)}`;
    const posterSrc = m.poster || fallbackSvg;
    return `
      <div class="carousel-card" onclick="selectMovie('${titleEscaped}')">
        <div class="carousel-poster-box">
          <img 
            src="${posterSrc}" 
            alt="${m.title}" 
            loading="lazy" 
            referrerpolicy="no-referrer" 
            onerror="this.onerror=null; this.src='${fallbackSvg}';" 
          />
        </div>
        <div class="carousel-info">
          <span class="c-title">${m.title}</span>
          <div class="c-meta">
            <span>⭐ Curated</span>
            <span>${m.year || ''}</span>
          </div>
          <span class="c-genres">${(m.genres || '').replace(/\|/g, ' &bull; ')}</span>
        </div>
      </div>
    `;
  }).join("");
}

function scrollCarousel(trackId, direction) {
  const track = document.getElementById(trackId);
  if (!track) return;
  const scrollDistance = 480;
  track.scrollBy({ left: direction * scrollDistance, behavior: "smooth" });
}

// =========================================================
// ⭐ INTERACTIVE 5-STAR RATING & TASTE VECTOR ENGINE
// =========================================================
function highlightStars(val) {
  const stars = document.querySelectorAll("#modal-star-picker .star-btn");
  stars.forEach(s => {
    const starVal = parseInt(s.getAttribute("data-val"));
    if (starVal <= val) s.classList.add("hover");
    else s.classList.remove("hover");
  });
}

function resetStarsHighlight() {
  const stars = document.querySelectorAll("#modal-star-picker .star-btn");
  stars.forEach(s => s.classList.remove("hover"));
  updateModalStarsVisual();
}

function updateModalStarsVisual() {
  if (!activeModalMovie) return;
  const cleanTitle = activeModalMovie.clean_title || activeModalMovie.title;
  const existing = userRatings.find(r => r.title.toLowerCase() === cleanTitle.toLowerCase());
  const ratingStatus = document.getElementById("modal-rating-status");
  const stars = document.querySelectorAll("#modal-star-picker .star-btn");

  stars.forEach(s => {
    const starVal = parseInt(s.getAttribute("data-val"));
    if (existing && starVal <= existing.rating) {
      s.classList.add("active");
    } else {
      s.classList.remove("active");
    }
  });

  if (ratingStatus) {
    ratingStatus.textContent = existing 
      ? `Rated ${existing.rating} ★ (Taste vector updated)` 
      : "Click a star to rate";
  }
}

async function submitModalRating(stars) {
  if (!activeModalMovie) return;
  const cleanTitle = activeModalMovie.clean_title || activeModalMovie.title;

  const existingIdx = userRatings.findIndex(r => r.title.toLowerCase() === cleanTitle.toLowerCase());
  if (existingIdx >= 0) {
    userRatings[existingIdx].rating = stars;
  } else {
    userRatings.push({ title: cleanTitle, rating: stars });
  }

  localStorage.setItem("cinepulse_user_ratings", JSON.stringify(userRatings));
  updateModalStarsVisual();
  showToast(`Saved ${stars}★ rating for "${cleanTitle}"! Taste vector updated.`);
  await refreshTasteProfileVector();
}

async function refreshTasteProfileVector() {
  const tasteSection = document.getElementById("taste-profile-section");
  const tasteTrack = document.getElementById("taste-profile-track");
  const ratedCounterPill = document.getElementById("rated-counter-pill");

  if (userRatings.length === 0) {
    if (tasteSection) tasteSection.classList.add("hidden");
    return;
  }

  if (ratedCounterPill) {
    ratedCounterPill.textContent = `${userRatings.length} Film${userRatings.length > 1 ? 's' : ''} Rated`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/taste-profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ratings: userRatings })
    });

    const data = await res.json();
    if (!res.ok || !data.recommendations || data.recommendations.length === 0) {
      return;
    }

    if (tasteTrack) {
      tasteTrack.innerHTML = data.recommendations.map(m => {
        const cleanTitle = m.clean_title.replace(/'/g, "\\'");
        const fallbackSvg = `/api/poster-image?title=${encodeURIComponent(cleanTitle)}`;
        const posterSrc = m.poster_url || fallbackSvg;
        return `
          <div class="carousel-card" onclick="selectMovie('${cleanTitle}')">
            <div class="carousel-poster-box">
              <img 
                src="${posterSrc}" 
                alt="${m.title}" 
                loading="lazy" 
                referrerpolicy="no-referrer" 
                onerror="this.onerror=null; this.src='${fallbackSvg}';" 
              />
            </div>
            <div class="carousel-info">
              <span class="c-title">${m.clean_title}</span>
              <div class="c-meta">
                <span style="color:#00f0ff;font-weight:700;">⚡ ${m.match_score}</span>
                <span>${m.year || ''}</span>
              </div>
              <span class="c-genres">${(m.genres || '').replace(/\|/g, ' &bull; ')}</span>
            </div>
          </div>
        `;
      }).join("");
    }

    if (tasteSection) tasteSection.classList.remove("hidden");
  } catch (err) {
    console.error("Taste profile calculation failed:", err);
  }
}

function clearRatings() {
  userRatings = [];
  localStorage.removeItem("cinepulse_user_ratings");
  const tasteSection = document.getElementById("taste-profile-section");
  if (tasteSection) tasteSection.classList.add("hidden");
  updateModalStarsVisual();
  showToast("Your personal taste ratings have been reset.");
}

// =========================================================
// 🔍 AI SEARCH & RECOMMENDATION ENGINE
// =========================================================
const movieInput = document.getElementById("movie-input");
const searchBtn = document.getElementById("search-btn");
const suggestionsList = document.getElementById("suggestions");
const resultsSection = document.getElementById("results-section");
const movieGrid = document.getElementById("movie-grid");
const queryBanner = document.getElementById("query-banner");
const targetMovieTitle = document.getElementById("target-movie-title");
const targetPosterThumb = document.getElementById("target-poster-thumb");
const targetGenresWrap = document.getElementById("target-genres-wrap");
const targetDirectorCast = document.getElementById("target-director-cast");
const resultsCount = document.getElementById("results-count");
const resultsLatencyBadge = document.getElementById("results-latency-badge");
const loader = document.getElementById("loader");
const loaderText = document.getElementById("loader-text");
const errorMessage = document.getElementById("error-message");
const apiStatus = document.getElementById("api-status");

// Detail Modal Elements
const modal = document.getElementById("movie-modal");
const modalPoster = document.getElementById("modal-poster");
const modalTitle = document.getElementById("modal-title");
const modalGenres = document.getElementById("modal-genres");
const modalMatchBadge = document.getElementById("modal-match-badge");
const modalYearPill = document.getElementById("modal-year-pill");
const modalBarFill = document.getElementById("modal-bar-fill");
const modalScorePct = document.getElementById("modal-score-pct");
const modalContentSub = document.getElementById("modal-content-sub");
const modalCrowdSub = document.getElementById("modal-crowd-sub");
const modalWhyText = document.getElementById("modal-why-text");
const modalXaiTags = document.getElementById("modal-xai-tags");
const modalDirectorBlock = document.getElementById("modal-director-block");
const modalExploreBtn = document.getElementById("modal-explore-btn");
const modalWatchlistBtn = document.getElementById("modal-watchlist-btn");

let debounceTimer = null;

// API Health Check
async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      apiStatus.textContent = `Engine Online (${data.movies_count.toLocaleString()} films &bull; Hybrid)`;
      apiStatus.style.color = "#00f0ff";
    } else {
      throw new Error();
    }
  } catch (err) {
    apiStatus.textContent = "Offline (run python app.py)";
    apiStatus.style.color = "#ec4899";
  }
}

// Live Autocomplete
if (movieInput) {
  movieInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = movieInput.value.trim();

    if (q.length < 2) {
      suggestionsList.classList.add("hidden");
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(q)}`);
        const movies = await res.json();

        if (movies.length === 0) {
          suggestionsList.classList.add("hidden");
          return;
        }

        suggestionsList.innerHTML = movies
          .map(
            (m) => `
            <li onclick="selectMovie('${m.clean_title.replace(/'/g, "\\'")}')">
              <span class="title">${m.title}</span>
              <span class="genre">${(m.genres || "").replace(/\|/g, ", ")}</span>
            </li>
          `
          )
          .join("");

        suggestionsList.classList.remove("hidden");
      } catch (e) {
        console.error("Autocomplete failed:", e);
      }
    }, 160);
  });
}

document.addEventListener("click", (e) => {
  if (movieInput && !movieInput.contains(e.target) && suggestionsList && !suggestionsList.contains(e.target)) {
    suggestionsList.classList.add("hidden");
  }
});

function selectMovie(title) {
  if (movieInput) movieInput.value = title;
  if (suggestionsList) suggestionsList.classList.add("hidden");
  currentAnchorQuery = title;
  fetchRecommendations(title, currentHybridMode);
}

function quickSelect(title) {
  if (movieInput) movieInput.value = title;
  if (suggestionsList) suggestionsList.classList.add("hidden");
  currentAnchorQuery = title;
  fetchRecommendations(title, currentHybridMode);
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => {
    const q = movieInput.value.trim();
    if (q) {
      currentAnchorQuery = q;
      fetchRecommendations(q, currentHybridMode);
    }
  });
}

if (movieInput) {
  movieInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      suggestionsList.classList.add("hidden");
      const q = movieInput.value.trim();
      if (q) {
        currentAnchorQuery = q;
        fetchRecommendations(q, currentHybridMode);
      }
    }
  });
}

// Fetch Recommendations from Flask with Mode & XAI
async function fetchRecommendations(title, mode = "hybrid") {
  errorMessage.classList.add("hidden");
  resultsSection.classList.add("hidden");
  queryBanner.classList.add("hidden");
  if (loaderText) loaderText.textContent = `Synthesizing ${mode} similarity vectors & retrieving official artwork...`;
  loader.classList.remove("hidden");

  try {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ movie: title, top_n: 6, mode: mode })
    });

    const data = await res.json();
    loader.classList.add("hidden");

    if (!res.ok || data.error) {
      showError(data.error || `Could not find recommendations for "${title}".`);
      return;
    }

    currentRecommendations = data.recommendations || [];
    renderResults(data);
  } catch (err) {
    loader.classList.add("hidden");
    showError("Could not connect to Flask API. Make sure 'python app.py' is running on port 5000.");
  }
}

// Helper to render individual movie cards
function renderCardHtml(m, idx) {
  const cleanTitleEscaped = (m.clean_title || m.title || "Movie").replace(/'/g, "\\'");
  const fallbackSvg = `/api/poster-image?title=${encodeURIComponent(cleanTitleEscaped)}`;
  const posterSrc = m.poster_url || fallbackSvg;

  const posterHtml = `
    <img 
      class="poster-img" 
      src="${posterSrc}" 
      alt="${m.title}" 
      loading="lazy" 
      referrerpolicy="no-referrer" 
      onerror="this.onerror=null; this.src='${fallbackSvg}';" 
    />`;

  const genreChips = (m.genres || "")
    .split("|")
    .slice(0, 3)
    .map((g) => `<span class="genre-chip">${g}</span>`)
    .join("");

  const sharedThemesHtml = (m.shared_themes && m.shared_themes.length > 0)
    ? `<div class="card-xai-row">
         ${m.shared_themes.slice(0, 3).map(tag => `<span class="card-xai-tag">${tag}</span>`).join("")}
       </div>`
    : "";

  return `
    <article class="movie-card" style="animation-delay: ${idx * 0.08}s" onclick="openModal(${idx})">
      <div class="poster-frame">
        ${posterHtml}
        <div class="neon-badge-overlay">
          <span>⚡</span>
          <span>${m.match_score}</span>
        </div>
      </div>
      <div class="card-content">
        <div>
          <h3 class="card-title">${m.clean_title}</h3>
          <span class="card-year">${m.year ? m.year : ""} ${m.director ? `&bull; Dir: ${m.director}` : ''}</span>
        </div>
        <div class="card-tags">
          ${genreChips}
        </div>
        ${sharedThemesHtml}
      </div>
    </article>
  `;
}

// Render Results Grid with Real Posters, Explainable AI, & Latency
function renderResults(data) {
  targetMovieTitle.textContent = data.clean_query || data.query;
  
  if (data.target_poster) {
    const cleanTarget = (data.clean_query || data.query || "Anchor").replace(/'/g, "\\'");
    const targetFallback = `/api/poster-image?title=${encodeURIComponent(cleanTarget)}`;
    targetPosterThumb.innerHTML = `<img src="${data.target_poster}" alt="${data.query}" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='${targetFallback}';" />`;
    targetPosterThumb.classList.remove("hidden");
  } else {
    targetPosterThumb.classList.add("hidden");
  }

  const queryGenres = (data.genres || "")
    .split("|")
    .map((g) => `<span class="neon-chip">${g}</span>`)
    .join("");
  targetGenresWrap.innerHTML = queryGenres;

  if (targetDirectorCast) {
    let creditText = "";
    if (data.director) creditText += `Directed by <strong>${data.director}</strong>`;
    if (data.cast && data.cast.length > 0) {
      creditText += ` &bull; Starring: ${data.cast.slice(0, 3).join(", ")}`;
    }
    targetDirectorCast.innerHTML = creditText;
  }

  const modeIndicator = document.getElementById("current-mode-indicator");
  if (modeIndicator) {
    modeIndicator.textContent = `Mode: ${data.mode.toUpperCase()}`;
  }

  if (resultsLatencyBadge) {
    resultsLatencyBadge.textContent = `⚡ ${data.latency_ms || 0.8}ms${data.cached ? ' (Cache Hit)' : ''}`;
  }

  resultsCount.textContent = `${data.recommendations.length} AI matches curated`;
  movieGrid.innerHTML = data.recommendations.map((m, idx) => renderCardHtml(m, idx)).join("");
  resultsSection.classList.remove("hidden");
  
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Modal Quick View with XAI & 5-Star Rating
function openModal(index) {
  const movie = currentRecommendations[index];
  if (!movie || !modal) return;

  activeModalMovie = movie;
  modalTitle.textContent = movie.title;
  modalYearPill.textContent = movie.year || "Cinema";
  modalMatchBadge.textContent = `⚡ ${movie.match_score} Overall Match`;
  modalScorePct.textContent = movie.match_score;
  modalBarFill.style.width = movie.match_score.includes("%") ? movie.match_score : "85%";

  if (modalContentSub) modalContentSub.textContent = `Content: ${movie.content_score || '85%'}`;
  if (modalCrowdSub) modalCrowdSub.textContent = `Crowd SVD: ${movie.crowd_score || '80%'}`;

  if (modalDirectorBlock) {
    let dirHtml = "";
    if (movie.director) dirHtml += `<strong>Director:</strong> ${movie.director} &bull; `;
    if (movie.cast && movie.cast.length > 0) dirHtml += `<strong>Cast:</strong> ${movie.cast.join(", ")}`;
    modalDirectorBlock.innerHTML = dirHtml;
  }

  // Explainable AI text & tags
  if (modalWhyText) {
    modalWhyText.textContent = movie.xai_explanation || 
      "Our model detected strong narrative congruence, shared thematic motifs, and matching tonal taxonomy with your selected title.";
  }

  if (modalXaiTags) {
    if (movie.shared_themes && movie.shared_themes.length > 0) {
      modalXaiTags.innerHTML = movie.shared_themes.map(t => `<span class="xai-pill">✦ ${t}</span>`).join("");
    } else {
      modalXaiTags.innerHTML = `<span class="xai-pill">✦ Narrative Tone</span><span class="xai-pill">✦ Genre Taxonomy</span>`;
    }
  }

  const cleanModalTitle = (movie.clean_title || movie.title || "Movie").replace(/'/g, "\\'");
  const modalFallback = `/api/poster-image?title=${encodeURIComponent(cleanModalTitle)}`;
  modalPoster.setAttribute("referrerpolicy", "no-referrer");
  modalPoster.onerror = function() {
    this.onerror = null;
    this.src = modalFallback;
  };
  modalPoster.src = movie.poster_url || modalFallback;
  modalPoster.style.display = "block";

  const genreChips = (movie.genres || "")
    .split("|")
    .map((g) => `<span class="neon-chip">${g}</span>`)
    .join("");
  modalGenres.innerHTML = genreChips;

  updateModalStarsVisual();
  modal.classList.remove("hidden");
}

function closeModal() {
  if (modal) modal.classList.add("hidden");
}

if (modal) {
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeModal();
    closeTrailerModal();
  }
});

// Modal Explore Button: Recommend based on clicked movie
if (modalExploreBtn) {
  modalExploreBtn.addEventListener("click", () => {
    if (activeModalMovie) {
      closeModal();
      selectMovie(activeModalMovie.clean_title || activeModalMovie.title);
    }
  });
}

// Modal Watchlist Button
if (modalWatchlistBtn) {
  modalWatchlistBtn.addEventListener("click", () => {
    if (!activeModalMovie) return;
    const clean = activeModalMovie.clean_title || activeModalMovie.title;
    const existing = watchlist.find(item => item.title.toLowerCase() === clean.toLowerCase());
    if (existing) {
      showToast(`"${clean}" is already in your Watchlist.`);
    } else {
      watchlist.push({
        title: clean,
        clean_title: clean,
        year: activeModalMovie.year || "",
        poster_url: activeModalMovie.poster_url || "",
        genres: activeModalMovie.genres || ""
      });
      localStorage.setItem("cinepulse_watchlist", JSON.stringify(watchlist));
      updateWatchlistBadge();
      showToast(`Added "${clean}" to Watchlist! ⭐`);
    }
  });
}

function openWatchlistModal() {
  if (watchlist.length === 0) {
    showToast("Your Watchlist is empty! Click 'Watchlist' on any movie to save it.");
    return;
  }
  currentRecommendations = watchlist.map(item => ({
    title: item.title,
    clean_title: item.clean_title || item.title,
    year: item.year,
    genres: item.genres,
    poster_url: item.poster_url,
    match_score: "Saved",
    shared_themes: ["Watchlist Item"],
    xai_explanation: "This title was saved directly to your personal Watchlist."
  }));
  renderResults({
    query: "My Saved Watchlist",
    clean_query: "My Saved Watchlist",
    genres: "Personal Collection",
    target_poster: null,
    director: null,
    cast: [],
    mode: "Watchlist",
    latency_ms: 0.1,
    cached: true,
    recommendations: currentRecommendations
  });
}

// Toast notification helper
function showToast(msg) {
  const toast = document.getElementById("toast-notify");
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 2800);
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorMessage.classList.remove("hidden");
}

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
  initHeroSlider();
  checkApiHealth();
  loadCuratedCategories();
  refreshTasteProfileVector();
});
