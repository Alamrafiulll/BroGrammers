const storiesData = [
  {
    name: "Aisha Rahman",
    role: "AI Consultant",
    degree: "B.Eng AI",
    achievement: "Built an AI study buddy adopted by 3 faculties and reduced help-desk load by 22%.",
    achievements: ["AI & Machine Learning", "Campus Automation", "Student Success"],
    rating: "4.9",
    impact: "18k students reached",
    img: "/static/img/aisha.jpg"
  },
  {
    name: "Kelvin Lim",
    role: "Robotics Engineer",
    degree: "MSc Robotics",
    achievement: "Led MMU robotics team to a regional win with an autonomous delivery bot.",
    achievements: ["ROS / Navigation", "Hardware Lead", "Competition Winner"],
    rating: "4.8",
    impact: "6 awards",
    img:"/static/img/kelvin.jpg",
  },
  {
    name: "Mei Tan",
    role: "Energy Systems Analyst",
    degree: "BSc Physics",
    achievement: "Published on sustainable energy grids with MMU Lab; piloted a microgrid twin.",
    achievements: ["Energy Grids", "Data Modeling", "Sustainability"],
    rating: "4.85",
    impact: "2 journals",
    img: "/static/img/mei.jpg",
  },
  {
    name: "Amir Hassan",
    role: "IoT Product Lead",
    degree: "B.Eng IoT",
    achievement: "Deployed a smart campus dashboard with live sensors across 5 buildings.",
    achievements: ["IoT / Edge", "Product Strategy", "Smart Campus"],
    rating: "4.92",
    impact: "5 buildings live",
    img: "/static/img/hasan.jpg",
  },
];

let cachedMentors = [];
let cachedProjects = [];
let studentProfileState = null;

const select = (q) => document.querySelector(q);
const selectAll = (q) => Array.from(document.querySelectorAll(q));

async function fileToBase64(file) {
  if (!file) return null;
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function hasApprovedMentor(requests = []) {
  return requests.some(
    (req) =>
      (req.request_type === "mentor" || req.type === "mentor") &&
      (req.status || "").toLowerCase() === "accepted"
  );
}

function setStudentAvatar(data) {
  const avatar = select("#studentAvatar");
  if (!avatar) return;
  const img = avatar.querySelector("img");
  const initialEl = avatar.querySelector(".student-avatar-initial");
  const name = data?.student_name || data?.name || "";
  const email = data?.email || "";
  const initial = (name || email || "S").trim().charAt(0).toUpperCase() || "S";
  const photo = data?.photo_url || data?.photo || data?.photo_data;
  const hasPhoto = !!photo;
  if (img) {
    if (hasPhoto) {
      img.src = photo;
      img.classList.remove("hidden");
      avatar.classList.add("has-photo");
    } else {
      img.src = "";
      img.classList.add("hidden");
      avatar.classList.remove("has-photo");
    }
  }
  if (initialEl) {
    if (hasPhoto) {
      initialEl.textContent = "";
      initialEl.style.display = "none";
      initialEl.style.opacity = "0";
      initialEl.style.visibility = "hidden";
    } else {
      initialEl.textContent = initial;
      initialEl.style.display = "block";
      initialEl.style.opacity = "1";
      initialEl.style.visibility = "visible";
    }
  }
  avatar.setAttribute("data-initial", initial);
}

async function ensureStudentSession(email, password, studentName, photoData) {
  const res = await fetch("/api/student/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      student_name: studentName,
      photo_data: photoData,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || data.status || "Login required");
  }
  setStudentAvatar(data);
  return data;
}

function authGuardMessage(targetEl, message) {
  if (targetEl) {
    targetEl.textContent = message;
  } else {
    alert(message);
  }
}

function studentAuthed() {
  return !!(studentProfileState && studentProfileState.email);
}

function requireStudent(message = "Please register/login via the Join form to continue.") {
  if (studentAuthed()) return true;
  authGuardMessage(null, message);
  return false;
}

async function preloadStudentSession() {
  try {
    const res = await fetch("/api/student/requests", { method: "GET" });
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.email) {
      studentProfileState = { email: data.email, student_name: data.student_name, photo_url: data.photo_url, requests: data.requests };
      setStudentAvatar(studentProfileState);
    }
  } catch (_) {
    /* ignore preload errors */
  }
}

function updateProjectGate() {
  const form = select("#studentProjectForm");
  const guard = select("#studentProjectGuard");
  if (!form) return;
  const submit = form.querySelector('button[type="submit"]');
  const approved = hasApprovedMentor(studentProfileState?.requests || []);
  if (submit) {
    submit.disabled = !approved;
    submit.textContent = approved ? "Submit for approval" : "Awaiting mentor approval";
  }
  if (guard) {
    guard.textContent = approved
      ? "Mentor approved. You can submit a project for mentor review."
      : "You need an approved mentor before submitting a project idea.";
  }
}

function mentorAvatar(mentor) {
  const img = mentor.photo || mentor.image || mentor.img;
  const initials = (mentor.name || "MM")
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();
  if (img) {
    return `
      <div class="mentor-photo has-photo">
        <img src="${img}" alt="${mentor.name || "Mentor photo"}">
      </div>`;
  }
  return `
    <div class="mentor-photo">
      <span>${initials}</span>
    </div>`;
}

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
    const pending = mentor.pending_requests ?? 0;
    const total = mentor.total_requests ?? pending;
    const card = document.createElement("article");
    card.className = "mentor-card tilt-card";
    card.style.transitionDelay = `${index * 70}ms`;
    card.innerHTML = `
      ${mentorAvatar(mentor)}
      <div class="mentor-info">
        <h4>${mentor.name || "STEM Mentor"}</h4>
        <p class="mentor-meta">${mentor.field || "Mentor"} - ${mentor.research_area || "Research"}</p>
      </div>
      <p class="mentor-desc">${mentor.description || "Ready to guide your project."}</p>
      <p class="mentor-meta">Requests: ${pending} pending / ${total} total</p>
      <button class="cta-button primary glow full mentor-cta" data-mentor="${mentor.name}" data-mentor-id="${mentor.id}">Connect Now</button>
    `;
    container.appendChild(card);
  });
}

function renderMentorGrid(mentors) {
  const container = select("#mentorGrid");
  if (!container) return;
  container.classList.add("mentor-grid");
  container.innerHTML = "";
  mentors.forEach((mentor, index) => {
    const pending = mentor.pending_requests ?? 0;
    const total = mentor.total_requests ?? pending;
    const card = document.createElement("article");
    card.className = "mentor-card tilt-card";
    card.style.transitionDelay = `${index * 80}ms`;
    card.innerHTML = `
      ${mentorAvatar(mentor)}
      <div class="mentor-info">
        <h4>${mentor.name || "STEM Mentor"}</h4>
        <p class="mentor-meta">${mentor.field || "Mentor"} - ${mentor.research_area || "Research"}</p>
      </div>
      <p class="mentor-desc">${mentor.description || "Ready to guide your project."}</p>
      <p class="mentor-meta">Requests: ${pending} pending / ${total} total</p>
      <button class="cta-button primary glow full mentor-cta" data-mentor="${mentor.name}" data-mentor-id="${mentor.id}" data-requires-student="true">Connect Now</button>
    `;
    container.appendChild(card);
  });
}

function renderProjects(projects) {
  const container = select("#projectGrid");
  if (!container) return;
  container.innerHTML = "";
  projects.forEach((project, index) => {
    const available = project.available ?? project.team_size ?? 0;
    const capacity = project.capacity ?? project.team_size ?? "N/A";
    const isFull = project.is_full || (available !== null && available <= 0);
    const card = document.createElement("article");
    card.className = "project-card tilt-card";
    card.style.transitionDelay = `${index * 60}ms`;
    card.innerHTML = `
      <h4>${project.title}</h4>
      <p class="mentor-meta">${project.category || "Project"}</p>
      <p>${project.description || ""}</p>
      <p class="mentor-meta">Team size: ${capacity}</p>
      <p class="mentor-meta">${available > 0 ? `${available} slots left` : "Team is full"}</p>
      <button class="cta-button outline full" data-project="${project.title}" data-project-id="${project.id}" data-requires-student="true" ${isFull ? "disabled" : ""}>${isFull ? "Full" : "Join Team"}</button>
    `;
    container.appendChild(card);
  });
}

function populateJoinMentorSelect() {
  const selectEl = select("#joinMentor");
  if (!selectEl) return;
  const currentValue = selectEl.value;
  selectEl.innerHTML = `<option value="">No preference</option>`;
  cachedMentors.forEach((mentor) => {
    const opt = document.createElement("option");
    opt.value = mentor.id;
    opt.textContent = mentor.name;
    selectEl.appendChild(opt);
  });
  if (currentValue) selectEl.value = currentValue;
}

async function refreshMentorUI() {
  cachedMentors = await fetchJSON("/mentors");
  updateStats(cachedMentors, cachedProjects);
  renderMentors(cachedMentors);
  renderMentorGrid(cachedMentors);
  populateJoinMentorSelect();
  bindMentorButtons();
  setupTilt();
  setupReveal();
  return cachedMentors;
}

function renderStories() {
  const track = select("#storiesTrack");
  if (!track) return;
  track.innerHTML = "";
  const loopData = [...storiesData, ...storiesData];
  loopData.forEach((story) => {
    const card = document.createElement("div");
    card.className = "story-card";
    const achievementsList = (story.achievements || [])
      .map((item) => `<li>${item}</li>`)
      .join("");
    card.innerHTML = `
      <div class="story-ribbon">Alumni</div>
      <div class="story-top">
        <div class="story-avatar">
          <img src="${story.img}" alt="${story.name}">
          <span class="story-badge">*</span>
        </div>
      </div>
      <div class="story-info">
        <h4>${story.name}</h4>
        <p class="story-role">${story.role || story.degree}</p>
        <p class="story-degree">${story.degree || ""}</p>
      </div>
      <p class="story-body">${story.achievement}</p>
      <ul class="story-achievements">${achievementsList}</ul>
    `;
    track.appendChild(card);
  });
}

function playStoryAnimation() {
  const track = select("#storiesTrack");
  const cards = selectAll(".story-card");
  if (!track || !cards.length) return;

  cards.forEach((card) => card.classList.remove("pop"));

  if (!("IntersectionObserver" in window)) {
    cards.forEach((card, index) => setTimeout(() => card.classList.add("pop"), index * 100));
    return;
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          cards.forEach((card, index) => {
            setTimeout(() => card.classList.add("pop"), index * 110);
          });
          obs.disconnect();
        }
      });
    },
    { threshold: 0.35 }
  );

  observer.observe(track);
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
  const cards = document.querySelectorAll(".story-card, .mentor-card, .project-card");

  cards.forEach((card) => {
    if (card.dataset.tiltBound) return;
    card.dataset.tiltBound = "1";
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const rotateY = ((x / rect.width) - 0.5) * 12; 
      const rotateX = ((y / rect.height) - 0.5) * -12;

      // Keep hover scale + add tilt
      card.style.transform = `scale(1.12) translateY(-10px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "scale(1) translateY(0) rotateY(0) rotateX(0)";
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
  selectAll(".mentor-card, .project-card").forEach((el) => {
    if (el.dataset.revealBound) return;
    el.dataset.revealBound = "1";
    observer.observe(el);
  });
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
      if (!requireStudent()) return;
      const modal = select("#mentorModal");
      const nameField = select("#mentorNameField");
      const idField = select("#mentorIdField");
      if (nameField) nameField.value = btn.dataset.mentor || "";
      if (idField) idField.value = btn.dataset.mentorId || "";
      openModal(modal);
    });
  });
}

function bindProjectButtons() {
  selectAll("[data-project]").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!requireStudent("Please register/login via the Join form before joining a project.")) return;
      const modal = select("#projectModal");
      const titleField = select("#projectTitleField");
      const idField = select("#projectIdField");
      if (titleField) titleField.value = btn.dataset.project || "";
      if (idField) idField.value = btn.dataset.projectId || "";
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
    if (status) status.textContent = "Sending...";
    const formData = Object.fromEntries(new FormData(form).entries());
    if (formData.mentor_id) formData.mentor_id = Number(formData.mentor_id);
    const res = await fetch("/api/join_mentor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    if (status) status.textContent = data.message || data.status;
    if (res.ok) {
      form.reset();
      await refreshMentorUI();
      closeModal(select("#mentorModal"));
    }
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
    if (formData.project_id) formData.project_id = Number(formData.project_id);
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
    const fd = new FormData(form);
    const formData = Object.fromEntries(fd.entries());
    const email = formData.email || "";
    const password = formData.password || "";
    if (!email || !password) {
      status.textContent = "Email and password are required.";
      return;
    }
    try {
      await ensureStudentSession(email, password, formData.student_name, null);
      status.textContent = "Registered and logged in.";
      return;
    } catch (err) {
      status.textContent = err.message;
      return;
    }
  });
}

async function fetchStudentRequests() {
  const res = await fetch("/api/student/requests");
  if (!res.ok) throw new Error("Not logged in");
  return res.json();
}

function renderStudentProfile(data) {
  const container = select("#studentProfile");
  const statusEl = select("#studentLoginStatus");
  if (!container) return;
  studentProfileState = data;
  setStudentAvatar(data);
  const allRequests = data?.requests || [];
  const requests = allRequests.filter(
    (req) => (req.status || "").toLowerCase() !== "withdrawn"
  );
  if (!data || !requests.length) {
    container.innerHTML = '<p class="muted">No requests yet for this email.</p>';
    updateProjectGate();
    return;
  }
  const approvedMentors = requests.filter(
    (req) =>
      (req.request_type === "mentor" || req.type === "mentor") &&
      (req.status || "").toLowerCase() === "accepted"
  );
  const approvedMentorNames = approvedMentors.map((req) => req.mentor_name || req.project_title || "Mentor");
  const mentorBadge = approvedMentors.length
    ? `<div class="card glass" style="margin-bottom:10px;">
        <p class="tag">Mentor approved</p>
        <p class="mentor-meta">Assigned mentor${approvedMentorNames.length > 1 ? "s" : ""}: ${approvedMentorNames.join(", ")}</p>
      </div>`
    : `<div class="card glass" style="margin-bottom:10px;">
        <p class="mentor-meta">Awaiting mentor approval. Request a mentor to unlock project submissions.</p>
      </div>`;
  const summary = `
    <div class="stats" style="margin-bottom: 10px;">
      <div class="stat-card glass">
        <p class="label">Pending requests</p>
        <h3>${data.pending ?? 0}</h3>
      </div>
      <div class="stat-card glass">
        <p class="label">Accepted</p>
        <h3>${data.accepted ?? 0}</h3>
      </div>
    </div>
  ` + mentorBadge;
  const cards = requests
    .map((req) => {
      const status = (req.status || "pending").toUpperCase();
      const typeLabel = req.request_type === "mentor" ? "Mentor request" : "Project join";
      const title = req.project_title || req.mentor_name || "Request";
      const canWithdraw = !["withdrawn", "rejected", "project_deleted"].includes(
        (req.status || "").toLowerCase()
      );
      return `
        <div class="card" data-request-id="${req.id}">
          <div class="card-header">
            <strong>${typeLabel}</strong> <span class="mentor-meta">(${status})</span>
          </div>
          <p class="mentor-meta">${title}</p>
          <p class="mentor-meta">${req.email}</p>
          <p>${req.message || req.intro || req.interest || ""}</p>
          ${
            canWithdraw
              ? `<button class="cta-button outline" data-withdraw-request="${req.id}">Withdraw</button>`
              : ""
          }
        </div>
      `;
    })
    .join("");
  container.innerHTML = summary + cards;
  if (statusEl) statusEl.textContent = "";
  updateProjectGate();
}

function handleStudentLogin() {
  const form = select("#studentLoginForm");
  const status = select("#studentLoginStatus");
  const container = select("#studentProfile");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (status) status.textContent = "Loading...";
    const payload = Object.fromEntries(new FormData(form).entries());
    const res = await fetch("/api/student/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (status) status.textContent = data.message || data.status || (res.ok ? "Loaded" : "Failed");
    if (res.ok) {
      setStudentAvatar(data);
      renderStudentProfile(data);
      updateProjectGate();
    } else if (container) {
      container.innerHTML = "";
    }
  });

  if (container) {
    container.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-withdraw-request]");
      if (!btn) return;
      const id = btn.dataset.withdrawRequest;
      if (status) status.textContent = "Withdrawing...";
      const res = await fetch(`/api/student/withdraw/${id}`, { method: "POST" });
      const data = await res.json();
      if (status) status.textContent = data.message || data.status || (res.ok ? "Removed" : "Failed");
      if (res.ok) {
        try {
          const refreshed = await fetchStudentRequests();
          renderStudentProfile(refreshed);
        } catch (_) {
          // ignore
        }
        updateProjectGate();
        cachedProjects = await fetchJSON("/projects");
        renderProjects(cachedProjects);
        bindProjectButtons();
      }
    });
  }
}

function handleStudentForms() {
  const mentorForm = select("#studentMentorForm");
  const mentorStatus = select("#studentMentorStatus");
  const projectForm = select("#studentProjectForm");
  const projectStatus = select("#studentProjectStatus");
  const profile = select("#studentProfile");
  const avatarButton = select("#studentAvatarButton");
  const avatarInput = select("#studentAvatarInput");
  const avatarStatus = select("#studentAvatarStatus");

  if (mentorForm) {
    mentorForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (mentorStatus) mentorStatus.textContent = "Sending...";
      const fd = new FormData(mentorForm);
      const payload = Object.fromEntries(fd.entries());
      const photoFile = fd.get("photo");
      if (photoFile instanceof File && photoFile.size > 0) {
        payload.photo_data = await fileToBase64(photoFile);
        payload.photo_name = photoFile.name;
      }
      if (payload.mentor_id) payload.mentor_id = Number(payload.mentor_id);
      const res = await fetch("/api/join_mentor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (mentorStatus) mentorStatus.textContent = data.message || data.status || (res.ok ? "Sent" : "Failed");
      if (res.status === 401) {
        authGuardMessage(mentorStatus, "Please register/login via the Join form before sending a mentor request.");
        return;
      }
      if (res.ok) {
        mentorForm.reset();
        if (profile) {
          try {
            const refreshed = await fetchStudentRequests();
            renderStudentProfile(refreshed);
            setStudentAvatar(refreshed);
          } catch (_) {}
        }
      }
    });
  }

  if (avatarButton && avatarInput) {
    avatarButton.addEventListener("click", () => avatarInput.click());
    avatarInput.addEventListener("change", async () => {
      if (!avatarInput.files || !avatarInput.files[0]) return;
      if (avatarStatus) avatarStatus.textContent = "Uploading...";
      const file = avatarInput.files[0];
      const payload = {
        email: studentProfileState?.email || "",
        photo_name: file.name,
        photo_data: await fileToBase64(file),
      };
      try {
        const res = await fetch("/api/student/photo", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (res.ok) {
          if (avatarStatus) avatarStatus.textContent = data.message || "Photo updated.";
          if (studentProfileState) {
            studentProfileState.photo = payload.photo_data;
            studentProfileState.photo_url = payload.photo_data;
            setStudentAvatar(studentProfileState);
          }
        } else {
          if (avatarStatus) avatarStatus.textContent = data.message || "Upload failed.";
        }
      } catch (err) {
        if (avatarStatus) avatarStatus.textContent = "Upload failed.";
      }
    });
  }

  if (projectForm) {
    projectForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!hasApprovedMentor(studentProfileState?.requests || [])) {
        if (projectStatus) projectStatus.textContent = "Awaiting mentor approval before submitting a project.";
        return;
      }
      if (projectStatus) projectStatus.textContent = "Submitting...";
      const fd = new FormData(projectForm);
      const payload = Object.fromEntries(fd.entries());
      const photoFile = fd.get("photo");
      if (photoFile instanceof File && photoFile.size > 0) {
        payload.photo_data = await fileToBase64(photoFile);
        payload.photo_name = photoFile.name;
      }
      if (payload.mentor_id) payload.mentor_id = Number(payload.mentor_id);
      const res = await fetch("/api/join_project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (projectStatus) projectStatus.textContent = data.message || data.status || (res.ok ? "Sent" : "Failed");
      if (res.status === 401) {
        authGuardMessage(projectStatus, "Please register/login via the Join form before submitting a project.");
        return;
      }
      if (res.ok) {
        projectForm.reset();
        if (profile) {
          try {
            const refreshed = await fetchStudentRequests();
            renderStudentProfile(refreshed);
            setStudentAvatar(refreshed);
          } catch (_) {}
        }
      }
    });
  }
}

function smoothNavClicks() {
  selectAll(".pill-nav a").forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href") || "";
      const isHash = href.startsWith("#");
      // Let normal navigation occur for cross-page links
      if (!isHash) return;

      e.preventDefault();
      const target = select(href);
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

function guardCreateProjectCta() {
  const cta = select("#createProjectCTA");
  if (!cta) return;
  cta.addEventListener("click", (e) => {
    if (!studentAuthed()) {
      e.preventDefault();
      authGuardMessage(null, "Please register/login via the Join form before creating a project.");
    }
  });
}

async function init() {
  hideLoader();
  setupTypewriter();
  renderStories();
  playStoryAnimation();
  setupStoryNav();
  smoothNavClicks();
  setupModals();
  handleMentorForm();
  handleProjectForm();
  handleJoinForm();
  handleStudentLogin();
  handleStudentForms();
  preloadStudentSession();
  addParallax();
  guardCreateProjectCta();
  handleMentorRegisterPage();

  cachedProjects = await fetchJSON("/projects");
  renderProjects(cachedProjects);
  bindProjectButtons();

  await refreshMentorUI();
  setupNavSpy();
}

document.addEventListener("DOMContentLoaded", init);

// ----------------------
// Mentor registration & dashboard (register page)
// ----------------------
function renderMentorDashboard(requests, container) {
  if (!container) return;
  if (!requests || !requests.length) {
    container.innerHTML = "<p class=\"muted\">No requests yet.</p>";
    return;
  }

  container.innerHTML = requests
    .map((req) => {
      const status = (req.status || "pending").toUpperCase();
      const projectType = req.interest || req.project_title || "Project idea";
      return `
        <div class="card" data-request-id="${req.id}">
          <div class="card-header">
            <strong>${req.student_name || "Student"}</strong> <span class="mentor-meta">(${status})</span>
          </div>
          <p class="mentor-meta">Project: ${projectType}</p>
          <p class="mentor-meta">Email: ${req.email || "N/A"}</p>
          <p>${req.message || req.intro || ""}</p>
          <div class="hero-actions" style="margin-top: 8px;">
            <button class="cta-button primary" data-action="accepted" data-request="${req.id}" ${req.status === "accepted" ? "disabled" : ""}>Accept</button>
            <button class="cta-button outline" data-action="rejected" data-request="${req.id}" ${req.status === "rejected" ? "disabled" : ""}>Reject</button>
          </div>
        </div>
      `;
    })
    .join("");
}

function handleMentorRegisterPage() {
  const registerForm = select("#registerForm");
  const registerStatus = select("#registerStatus");
  const loginForm = select("#mentorLoginForm");
  const loginStatus = select("#mentorLoginStatus");
  const dashboard = select("#mentorDashboard");
  const preview = select("#newMentorPreview");
  let lastLogin = null;

  if (registerForm && preview) {
    registerForm.addEventListener("input", () => {
      const data = Object.fromEntries(new FormData(registerForm).entries());
      preview.innerHTML = `
        <div class="mentor-card">
          <h4>${data.name || "Your name"}</h4>
          <p class="mentor-meta">${data.field || "Field"} - ${data.research_area || "Area"}</p>
          <p>${data.description || "How you help students..."}</p>
        </div>
      `;
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (registerStatus) registerStatus.textContent = "Submitting...";
      const fd = new FormData(registerForm);
      const payload = Object.fromEntries(fd.entries());
      const photoFile = fd.get("photo");
      if (photoFile instanceof File && photoFile.size > 0) {
        payload.photo_data = await fileToBase64(photoFile);
        payload.photo_name = photoFile.name;
      }
      const res = await fetch("/api/add_mentor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (registerStatus) registerStatus.textContent = data.message || data.status;
      if (res.ok) registerForm.reset();
    });
  }

  async function loadMentorRequests(auth) {
    const res = await fetch("/api/mentor/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(auth),
    });
    const data = await res.json();
    if (!res.ok) {
      if (loginStatus) loginStatus.textContent = data.message || "Login failed.";
      return;
    }
    if (loginStatus) loginStatus.textContent = "Logged in.";
    renderMentorDashboard(data.requests, dashboard);
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const auth = Object.fromEntries(new FormData(loginForm).entries());
      lastLogin = auth;
      if (loginStatus) loginStatus.textContent = "Loading requests...";
      const res = await fetch("/api/mentor/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(auth),
      });
      const data = await res.json();
      if (!res.ok) {
        if (loginStatus) loginStatus.textContent = data.message || "Login failed.";
        return;
      }
      if (loginStatus) loginStatus.textContent = "Redirecting to dashboard...";
      window.location = data.redirect || "/mentor/dashboard";
    });
  }

  if (dashboard) {
    dashboard.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn || !lastLogin) return;
      const requestId = btn.getAttribute("data-request");
      const action = btn.getAttribute("data-action");
      const res = await fetch(`/api/mentor/requests/${requestId}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...lastLogin, action }),
      });
      const data = await res.json();
      if (!res.ok) {
        if (loginStatus) loginStatus.textContent = data.message || "Update failed.";
        return;
      }
      if (loginStatus) loginStatus.textContent = `Request ${action}.`;
      // Refresh dashboard
      await loadMentorRequests(lastLogin);
    });
  }
}
