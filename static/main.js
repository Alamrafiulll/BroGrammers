const storiesData = [
  { name: "Aisha Rahman", degree: "B.Eng AI", achievement: "Built a campus AI study buddy adopted by 3 faculties.", img: "https://via.placeholder.com/120?text=AR" },
  { name: "Kelvin Lim", degree: "MSc Robotics", achievement: "Led MMU robotics team to a regional win.", img: "https://via.placeholder.com/120?text=KL" },
  { name: "Mei Tan", degree: "BSc Physics", achievement: "Published on sustainable energy grids with MMU Lab.", img: "https://via.placeholder.com/120?text=MT" },
  { name: "Amir Hassan", degree: "B.Eng IoT", achievement: "Deployed a live smart campus dashboard prototype.", img: "https://via.placeholder.com/120?text=AH" }
];

const select = (q) => document.querySelector(q);
const selectAll = (q) => Array.from(document.querySelectorAll(q));

async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error("Fetch failed", err);
    return [];
  }
}

function hideLoader() {
  const loader = select("#loadingScreen");
  setTimeout(() => loader?.classList.add("hide"), 1200);
}

function setupTypewriter() {
  const el = select("#typewriter");
  if (!el) return;
  const text = el.textContent.trim();
  el.textContent = "";
  let idx = 0;
  const interval = setInterval(() => {
    el.textContent = text.slice(0, idx);
    idx += 1;
    if (idx > text.length) clearInterval(interval);
  }, 45);
}

function updateStats(mentors, projects) {
  const statM = select("#statMentors");
  const statP = select("#statProjects");
  if (statM) statM.textContent = `${mentors.length} Mentors`;
  if (statP) statP.textContent = `${projects.length} Projects`;
}

function renderMentors(mentors) {
  const container = select("#mentorStack");
  if (!container) return;
  container.innerHTML = "";
  mentors.forEach((mentor, index) => {
    const card = document.createElement("article");
    card.className = "mentor-card tilt-card";
    card.style.transitionDelay = `${index * 70}ms`;
    card.innerHTML = `
      <div class="mentor-top">
        <div class="mentor-avatar">${(mentor.name || "M").slice(0, 2)}</div>
        <div>
          <h4>${mentor.name}</h4>
          <p class="mentor-meta">${mentor.field || "STEM Mentor"} · ${mentor.research_area || "Research"}</p>
        </div>
      </div>
      <p>${mentor.description || "Ready to guide your project."}</p>
      <button class="cta-button primary glow full" data-mentor="${mentor.name}">Connect Now</button>
    `;
    container.appendChild(card);
  });
}

function renderProjects(projects) {
  const container = select("#projectGrid");
  if (!container) return;
  container.innerHTML = "";
  projects.forEach((project, index) => {
    const card = document.createElement("article");
    card.className = "project-card tilt-card";
    card.style.transitionDelay = `${index * 60}ms`;
    card.innerHTML = `
      <h4>${project.title}</h4>
      <p class="mentor-meta">${project.category || "Project"}</p>
      <p>${project.description || ""}</p>
      <p class="mentor-meta">Team size: ${project.team_size || "N/A"}</p>
      <button class="cta-button outline full" data-project="${project.title}">Join Team</button>
    `;
    container.appendChild(card);
  });
}

function renderStories() {
  const track = select("#storiesTrack");
  if (!track) return;
  track.innerHTML = "";
  storiesData.forEach((story) => {
    const card = document.createElement("div");
    card.className = "story-card";
    card.innerHTML = `
      <img src="${story.img}" alt="${story.name}">
      <h4>${story.name}</h4>
      <p class="mentor-meta">${story.degree}</p>
      <p>${story.achievement}</p>
    `;
    track.appendChild(card);
  });
}

function setupStoryNav() {
  const track = select("#storiesTrack");
  const prev = select(".story-nav.prev");
  const next = select(".story-nav.next");
  if (!track || !prev || !next) return;
  prev.addEventListener("click", () => (track.scrollLeft -= 260));
  next.addEventListener("click", () => (track.scrollLeft += 260));
}

function setupTilt() {
  selectAll(".tilt-card").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const rotateY = ((x / rect.width) - 0.5) * 10;
      const rotateX = ((y / rect.height) - 0.5) * -10;
      card.style.transform = `rotateY(${rotateY}deg) rotateX(${rotateX}deg) translateY(-4px)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "rotateY(0deg) rotateX(0deg)";
    });
  });
}

function setupReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("show");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );
  selectAll(".mentor-card, .project-card").forEach((el) => observer.observe(el));
}

function setupNavSpy() {
  const links = selectAll(".pill-nav a");
  const sections = selectAll("[data-section]");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          links.forEach((link) => {
            link.classList.toggle("active", link.dataset.target === id);
          });
        }
      });
    },
    { threshold: 0.5 }
  );
  sections.forEach((section) => observer.observe(section));
}

function openModal(modal) {
  modal?.classList.remove("hidden");
  modal?.setAttribute("aria-hidden", "false");
}

function closeModal(modal) {
  modal?.classList.add("hidden");
  modal?.setAttribute("aria-hidden", "true");
}

function setupModals() {
  selectAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.closest(".modal")));
  });
  selectAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal(modal);
    });
  });
}

function bindMentorButtons() {
  selectAll("[data-mentor]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = select("#mentorModal");
      const nameField = select("#mentorNameField");
      if (nameField) nameField.value = btn.dataset.mentor || "";
      openModal(modal);
    });
  });
}

function bindProjectButtons() {
  selectAll("[data-project]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = select("#projectModal");
      const titleField = select("#projectTitleField");
      if (titleField) titleField.value = btn.dataset.project || "";
      openModal(modal);
    });
  });
}

function handleMentorForm() {
  const form = select("#mentorForm");
  const status = select("#mentorStatus");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "Sending...";
    const formData = Object.fromEntries(new FormData(form).entries());
    const res = await fetch("/api/join_mentor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    status.textContent = data.message || data.status;
    if (res.ok) form.reset();
  });
}

function handleProjectForm() {
  const form = select("#projectForm");
  const status = select("#projectStatus");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "Submitting...";
    const formData = Object.fromEntries(new FormData(form).entries());
    const res = await fetch("/api/join_project", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    status.textContent = data.message || data.status;
    if (res.ok) form.reset();
  });
}

function handleJoinForm() {
  const form = select("#joinForm");
  const status = select("#joinStatus");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    status.textContent = "Sending...";
    const formData = Object.fromEntries(new FormData(form).entries());
    // Route into requests as a generic project request
    const payload = {
      project_title: `Community (${formData.role || "Participant"})`,
      student_name: formData.student_name,
      email: formData.email,
      skills: formData.role,
      intro: formData.message,
    };
    const res = await fetch("/api/join_project", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    status.textContent = data.message || data.status || "Saved.";
    if (res.ok) form.reset();
  });
}

function smoothNavClicks() {
  selectAll(".pill-nav a").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const target = select(link.getAttribute("href"));
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function addParallax() {
  document.addEventListener("mousemove", (e) => {
    const root = document.documentElement;
    const x = (e.clientX / window.innerWidth - 0.5) * 4;
    const y = (e.clientY / window.innerHeight - 0.5) * 4;
    root.style.setProperty("--parallax-x", `${x}px`);
    root.style.setProperty("--parallax-y", `${y}px`);
  });
}

async function init() {
  hideLoader();
  setupTypewriter();
  renderStories();
  setupStoryNav();
  smoothNavClicks();
  setupModals();
  handleMentorForm();
  handleProjectForm();
  handleJoinForm();
  addParallax();

  const mentors = await fetchJSON("/mentors");
  const projects = await fetchJSON("/projects");
  updateStats(mentors, projects);
  renderMentors(mentors);
  renderProjects(projects);
  setupTilt();
  setupReveal();
  bindMentorButtons();
  bindProjectButtons();
  setupNavSpy();
}

document.addEventListener("DOMContentLoaded", init);
