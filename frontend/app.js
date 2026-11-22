/**
 * SkillBridge Frontend Client
 * Modern JavaScript application handling Career Analysis,
 * Interactive Bento Dashboard, Skill Gap Matrix, AI Roadmap Generation,
 * and Excel Export.
 */

// API Configuration
const API_BASE_URL = (
  window.location.port === "8000"
    ? window.location.origin
    : "http://127.0.0.1:8000"
).replace(/\/$/, "");

// Global Application State
const state = {
  selectedFile: null,
  careers: [],
  selectedCareer: "",
  analysisResult: null,
  roadmapData: null,
  activeSkillFilter: "all",
  skillSearchTerm: "",
  checkedTopics: new Set(),
};

// DOM Elements
const elements = {
  systemStatus: document.getElementById("systemStatus"),
  analysisForm: document.getElementById("analysisForm"),
  careerSelect: document.getElementById("careerSelect"),
  quickChipsContainer: document.getElementById("quickChipsContainer"),
  dropzone: document.getElementById("dropzone"),
  resumeFile: document.getElementById("resumeFile"),
  dropzonePrompt: document.getElementById("dropzonePrompt"),
  selectedFileCard: document.getElementById("selectedFileCard"),
  fileNameLabel: document.getElementById("fileNameLabel"),
  fileSizeLabel: document.getElementById("fileSizeLabel"),
  fileTypeIcon: document.getElementById("fileTypeIcon"),
  removeFileBtn: document.getElementById("removeFileBtn"),
  submitBtn: document.getElementById("submitBtn"),
  submitSpinner: document.getElementById("submitSpinner"),

  stepperSection: document.getElementById("stepperSection"),
  stepperStatusText: document.getElementById("stepperStatusText"),
  step1: document.getElementById("step1"),
  step2: document.getElementById("step2"),
  step3: document.getElementById("step3"),

  dashboardSection: document.getElementById("dashboardSection"),
  metaRoleText: document.getElementById("metaRoleText"),
  metaFileText: document.getElementById("metaFileText"),
  scoreCircle: document.getElementById("scoreCircle"),
  matchPercentage: document.getElementById("matchPercentage"),
  readinessGradeBadge: document.getElementById("readinessGradeBadge"),
  readinessSummaryText: document.getElementById("readinessSummaryText"),
  matchedCount: document.getElementById("matchedCount"),
  missingCount: document.getElementById("missingCount"),
  totalRequiredCount: document.getElementById("totalRequiredCount"),

  candidateAvatar: document.getElementById("candidateAvatar"),
  candidateName: document.getElementById("candidateName"),
  candidateEmail: document.getElementById("candidateEmail"),
  candidateEducation: document.getElementById("candidateEducation"),
  candidateSummary: document.getElementById("candidateSummary"),

  skillTabs: document.getElementById("skillTabs"),
  missingTabCount: document.getElementById("missingTabCount"),
  matchedTabCount: document.getElementById("matchedTabCount"),
  skillSearchInput: document.getElementById("skillSearchInput"),
  skillsTagCloud: document.getElementById("skillsTagCloud"),
  experienceTimeline: document.getElementById("experienceTimeline"),

  roadmapStudioSection: document.getElementById("roadmapStudioSection"),
  generateRoadmapBtn: document.getElementById("generateRoadmapBtn"),
  roadmapSpinner: document.getElementById("roadmapSpinner"),
  roadmapDisplayWrapper: document.getElementById("roadmapDisplayWrapper"),
  roadmapHeading: document.getElementById("roadmapHeading"),
  exportExcelBtn: document.getElementById("exportExcelBtn"),
  roadmapTotalWeeks: document.getElementById("roadmapTotalWeeks"),
  roadmapTotalMilestones: document.getElementById("roadmapTotalMilestones"),
  roadmapTotalHours: document.getElementById("roadmapTotalHours"),
  milestonesStream: document.getElementById("milestonesStream"),

  toastContainer: document.getElementById("toastContainer"),
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
  loadCareers();
  initDropzone();
  initFormListeners();
  initFilterListeners();
  initRoadmapListeners();
});

// ============================================================================
// Backend Communication & Health
// ============================================================================

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.status === "ok") {
        updateSystemStatus(true, "Backend Online");
        return;
      }
    }
    updateSystemStatus(false, "Backend Unreachable");
  } catch (err) {
    updateSystemStatus(false, "Backend Offline");
  }
}

function updateSystemStatus(isOnline, label) {
  const dot = elements.systemStatus.querySelector(".status-dot");
  const text = elements.systemStatus.querySelector(".status-label");
  dot.className = `status-dot ${isOnline ? "online" : "offline"}`;
  text.textContent = label;
}

async function loadCareers() {
  try {
    const res = await fetch(`${API_BASE_URL}/careers`);
    if (!res.ok) throw new Error("Failed to load careers");
    const data = await res.json();
    state.careers = data.careers || [];

    // Populate select
    elements.careerSelect.innerHTML =
      '<option value="" disabled selected>Select a career role...</option>';
    state.careers.forEach((career) => {
      const option = document.createElement("option");
      option.value = career;
      option.textContent = career;
      elements.careerSelect.appendChild(option);
    });

    // Wire quick chips
    elements.quickChipsContainer.querySelectorAll(".chip-btn").forEach((chip) => {
      chip.addEventListener("click", () => {
        const role = chip.getAttribute("data-role");
        if (state.careers.includes(role)) {
          elements.careerSelect.value = role;
          elements.careerSelect.dispatchEvent(new Event("change"));
          updateChipHighlights(role);
        }
      });
    });

    elements.careerSelect.addEventListener("change", (e) => {
      updateChipHighlights(e.target.value);
    });
  } catch (err) {
    showToast("Could not load career paths from backend.", "error");
  }
}

function updateChipHighlights(selectedRole) {
  elements.quickChipsContainer.querySelectorAll(".chip-btn").forEach((chip) => {
    if (chip.getAttribute("data-role") === selectedRole) {
      chip.classList.add("active");
    } else {
      chip.classList.remove("active");
    }
  });
}

// ============================================================================
// File Ingestion & Drag and Drop
// ============================================================================

function initDropzone() {
  const dropzone = elements.dropzone;
  const fileInput = elements.resumeFile;

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  elements.removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });
}

function handleFileSelected(file) {
  const validExtensions = [".pdf", ".docx"];
  const extension = "." + file.name.split(".").pop().toLowerCase();

  if (!validExtensions.includes(extension)) {
    showToast("Please select a PDF or DOCX file.", "error");
    return;
  }

  const maxBytes = 5 * 1024 * 1024;
  if (file.size > maxBytes) {
    showToast("File is too large. Maximum size is 5 MB.", "error");
    return;
  }

  state.selectedFile = file;
  elements.fileNameLabel.textContent = file.name;
  elements.fileSizeLabel.textContent = formatBytes(file.size);

  if (extension === ".pdf") {
    elements.fileTypeIcon.className = "fa-solid fa-file-pdf";
  } else {
    elements.fileTypeIcon.className = "fa-solid fa-file-word";
  }

  elements.dropzonePrompt.classList.add("hidden");
  elements.selectedFileCard.classList.remove("hidden");
}

function clearSelectedFile() {
  state.selectedFile = null;
  elements.resumeFile.value = "";
  elements.dropzonePrompt.classList.remove("hidden");
  elements.selectedFileCard.classList.add("hidden");
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// ============================================================================
// Form Submission & Analysis
// ============================================================================

function initFormListeners() {
  elements.analysisForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const career = elements.careerSelect.value;
    if (!career) {
      showToast("Please choose a target career path.", "error");
      return;
    }

    if (!state.selectedFile) {
      showToast("Please upload your resume file (PDF or DOCX).", "error");
      return;
    }

    state.selectedCareer = career;
    await runAnalysis(career, state.selectedFile);
  });
}

async function runAnalysis(career, file) {
  // Toggle UI Loading
  elements.submitBtn.disabled = true;
  elements.submitSpinner.classList.remove("hidden");
  elements.submitBtn.querySelector(".btn-text").classList.add("hidden");

  // Show Stepper
  elements.stepperSection.classList.remove("hidden");
  elements.dashboardSection.classList.add("hidden");
  elements.roadmapDisplayWrapper.classList.add("hidden");
  setStepperStep(1, "Extracting text from resume...");

  const formData = new FormData();
  formData.append("career", career);
  formData.append("file", file);

  try {
    const stepperTimer1 = setTimeout(() => {
      setStepperStep(2, "Extracting profile with Groq AI...");
    }, 1200);

    const stepperTimer2 = setTimeout(() => {
      setStepperStep(3, "Matching competencies against role benchmark...");
    }, 2800);

    const response = await fetch(`${API_BASE_URL}/career-agent/analyze`, {
      method: "POST",
      body: formData,
    });

    clearTimeout(stepperTimer1);
    clearTimeout(stepperTimer2);

    if (!response.ok) {
      let errorDetail = "Analysis request failed";
      try {
        const err = await response.json();
        errorDetail = err.detail || errorDetail;
      } catch (_) {}
      throw new Error(errorDetail);
    }

    const data = await response.json();
    state.analysisResult = data;
    renderDashboard(data);
    showToast("Career diagnostic complete!", "success");

    // Scroll smoothly to results
    setTimeout(() => {
      elements.dashboardSection.scrollIntoView({ behavior: "smooth" });
    }, 200);

  } catch (err) {
    showToast(err.message || "Failed to analyze resume.", "error");
  } finally {
    elements.submitBtn.disabled = false;
    elements.submitSpinner.classList.add("hidden");
    elements.submitBtn.querySelector(".btn-text").classList.remove("hidden");
    elements.stepperSection.classList.add("hidden");
  }
}

function setStepperStep(stepNumber, statusText) {
  elements.stepperStatusText.textContent = statusText;
  [elements.step1, elements.step2, elements.step3].forEach((el, index) => {
    if (index + 1 < stepNumber) {
      el.className = "step-item completed";
    } else if (index + 1 === stepNumber) {
      el.className = "step-item active";
    } else {
      el.className = "step-item";
    }
  });
}

// ============================================================================
// Dashboard Rendering (Bento Grid)
// ============================================================================

function renderDashboard(data) {
  elements.dashboardSection.classList.remove("hidden");

  // Meta pills
  elements.metaRoleText.textContent = data.career || state.selectedCareer;
  elements.metaFileText.textContent = data.filename || state.selectedFile?.name || "Resume";

  const percentage = data.match_percentage || 0;
  const matched = data.matched_skills || [];
  const missing = data.missing_skills || [];
  const required = data.required_skills || [];
  const profile = data.profile || {};

  // Score Ring Animation
  elements.matchPercentage.textContent = `${percentage}%`;
  const circumference = 2 * Math.PI * 50; // r=50 -> ~314.16
  const strokeOffset = circumference - (circumference * percentage) / 100;
  elements.scoreCircle.style.strokeDasharray = `${circumference}`;
  elements.scoreCircle.style.strokeDashoffset = `${strokeOffset}`;

  // Qualitative Grade
  if (percentage >= 75) {
    elements.readinessGradeBadge.textContent = "High Match — Strong Foundation";
    elements.readinessGradeBadge.style.color = "var(--accent-emerald)";
    elements.readinessSummaryText.textContent =
      "Your demonstrated skills strongly align with this career benchmark. Minor targeted upskilling will make you an exceptional candidate.";
    elements.scoreCircle.style.stroke = "var(--accent-emerald)";
  } else if (percentage >= 45) {
    elements.readinessGradeBadge.textContent = "Moderate Fit — Bridgeable Gap";
    elements.readinessGradeBadge.style.color = "var(--accent-amber)";
    elements.readinessSummaryText.textContent =
      "You have key foundational abilities, but key industry-standard tools or frameworks are missing. Complete the roadmap below to close the gap.";
    elements.scoreCircle.style.stroke = "var(--accent-amber)";
  } else {
    elements.readinessGradeBadge.textContent = "Foundational Growth Needed";
    elements.readinessGradeBadge.style.color = "var(--accent-rose)";
    elements.readinessSummaryText.textContent =
      "A significant skill delta exists for this role. Follow the tailored curriculum to systematically build and demonstrate these competencies.";
    elements.scoreCircle.style.stroke = "var(--accent-cyan)";
  }

  // Counters
  elements.matchedCount.textContent = matched.length;
  elements.missingCount.textContent = missing.length;
  elements.totalRequiredCount.textContent = required.length;

  elements.matchedTabCount.textContent = matched.length;
  elements.missingTabCount.textContent = missing.length;

  // Candidate Snapshot
  const fullName = profile.full_name || "Candidate";
  elements.candidateName.textContent = fullName;
  elements.candidateEmail.textContent = profile.email || "Email not specified";

  // Initials Avatar
  const initials = fullName
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase() || "JS";
  elements.candidateAvatar.textContent = initials;

  // Education
  elements.candidateEducation.innerHTML = "";
  const educationItems = profile.education || [];
  if (educationItems.length > 0) {
    educationItems.forEach((edu) => {
      const span = document.createElement("span");
      span.className = "pill-item";
      span.textContent = edu;
      elements.candidateEducation.appendChild(span);
    });
  } else {
    elements.candidateEducation.innerHTML = '<span class="text-muted">No education listed</span>';
  }

  // Summary
  elements.candidateSummary.textContent =
    profile.summary || "No professional overview extracted from resume.";

  // Projects & Experience Timeline
  renderExperience(profile.experience, profile.projects);

  // Render Skill Cloud
  renderSkillsCloud();
}

function renderExperience(experience = [], projects = []) {
  elements.experienceTimeline.innerHTML = "";
  const combined = [];

  experience.forEach((item) => {
    combined.push({
      title: "Experience Highlight",
      desc: item,
      icon: "fa-briefcase",
    });
  });

  projects.forEach((item) => {
    combined.push({
      title: "Project Highlight",
      desc: item,
      icon: "fa-code",
    });
  });

  if (combined.length === 0) {
    elements.experienceTimeline.innerHTML =
      '<p class="text-muted" style="padding: 1rem;">No prior projects or experience extracted.</p>';
    return;
  }

  combined.forEach((item) => {
    const card = document.createElement("div");
    card.className = "timeline-card";
    card.innerHTML = `
      <div class="timeline-title">
        <i class="fa-solid ${item.icon}" style="color: var(--accent-cyan); margin-right: 0.4rem;"></i>
        ${escapeHtml(item.title)}
      </div>
      <p class="timeline-desc">${escapeHtml(item.desc)}</p>
    `;
    elements.experienceTimeline.appendChild(card);
  });
}

// ============================================================================
// Skill Cloud & Filtering
// ============================================================================

function initFilterListeners() {
  elements.skillTabs.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      elements.skillTabs.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeSkillFilter = btn.getAttribute("data-filter");
      renderSkillsCloud();
    });
  });

  elements.skillSearchInput.addEventListener("input", (e) => {
    state.skillSearchTerm = e.target.value.trim().toLowerCase();
    renderSkillsCloud();
  });
}

function renderSkillsCloud() {
  if (!state.analysisResult) return;

  const matched = state.analysisResult.matched_skills || [];
  const missing = state.analysisResult.missing_skills || [];
  elements.skillsTagCloud.innerHTML = "";

  const allSkills = [
    ...matched.map((s) => ({ name: s, type: "matched" })),
    ...missing.map((s) => ({ name: s, type: "missing" })),
  ];

  const filtered = allSkills.filter((item) => {
    if (state.activeSkillFilter === "matched" && item.type !== "matched") return false;
    if (state.activeSkillFilter === "missing" && item.type !== "missing") return false;
    if (state.skillSearchTerm && !item.name.toLowerCase().includes(state.skillSearchTerm)) {
      return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    elements.skillsTagCloud.innerHTML =
      '<p class="text-muted" style="padding: 1rem;">No skills matching your filter.</p>';
    return;
  }

  filtered.forEach((skill) => {
    const span = document.createElement("span");
    span.className = `skill-pill ${skill.type}`;
    const icon = skill.type === "matched" ? "fa-check" : "fa-plus";
    span.innerHTML = `<i class="fa-solid ${icon}"></i> ${escapeHtml(skill.name)}`;
    elements.skillsTagCloud.appendChild(span);
  });
}

// ============================================================================
// Roadmap Generation & Excel Export
// ============================================================================

function initRoadmapListeners() {
  elements.generateRoadmapBtn.addEventListener("click", async () => {
    if (!state.analysisResult) return;

    const missingSkills = state.analysisResult.missing_skills || [];
    if (missingSkills.length === 0) {
      showToast("You already possess all required skills for this role!", "info");
      return;
    }

    elements.generateRoadmapBtn.disabled = true;
    elements.roadmapSpinner.classList.remove("hidden");
    elements.generateRoadmapBtn.querySelector(".btn-text").classList.add("hidden");

    try {
      const response = await fetch(`${API_BASE_URL}/roadmap/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          career: state.analysisResult.career,
          missing_skills: missingSkills,
          student_skills: state.analysisResult.profile?.skills || [],
        }),
      });

      if (!response.ok) {
        let errDetail = "Failed to generate roadmap";
        try {
          const err = await response.json();
          errDetail = err.detail || errDetail;
        } catch (_) {}
        throw new Error(errDetail);
      }

      const roadmap = await response.json();
      state.roadmapData = roadmap;
      renderRoadmap(roadmap);
      showToast("Personalized roadmap generated with verified resources!", "success");

      setTimeout(() => {
        elements.roadmapDisplayWrapper.scrollIntoView({ behavior: "smooth" });
      }, 200);

    } catch (err) {
      showToast(err.message || "Roadmap generation failed.", "error");
    } finally {
      elements.generateRoadmapBtn.disabled = false;
      elements.roadmapSpinner.classList.add("hidden");
      elements.generateRoadmapBtn.querySelector(".btn-text").classList.remove("hidden");
    }
  });

  // Export to Excel
  elements.exportExcelBtn.addEventListener("click", async () => {
    if (!state.roadmapData) return;

    try {
      elements.exportExcelBtn.disabled = true;
      elements.exportExcelBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating Excel...';

      const response = await fetch(`${API_BASE_URL}/roadmap/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.roadmapData),
      });

      if (!response.ok) throw new Error("Excel export failed");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const careerSlug = (state.roadmapData.career || "Career").replace(/\s+/g, "_");
      a.download = `${careerSlug}_Learning_Roadmap.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showToast("Roadmap spreadsheet downloaded successfully!", "success");
    } catch (err) {
      showToast("Could not export roadmap spreadsheet.", "error");
    } finally {
      elements.exportExcelBtn.disabled = false;
      elements.exportExcelBtn.innerHTML = '<i class="fa-solid fa-file-excel"></i> Export Roadmap (.xlsx)';
    }
  });
}

function renderRoadmap(roadmap) {
  elements.roadmapDisplayWrapper.classList.remove("hidden");
  elements.roadmapHeading.textContent = `Learning Roadmap — ${roadmap.career}`;

  const milestones = roadmap.milestones || [];
  elements.roadmapTotalWeeks.textContent = roadmap.total_estimated_weeks || milestones.length * 2;
  elements.roadmapTotalMilestones.textContent = milestones.length;

  const totalHours = milestones.reduce((sum, m) => sum + (m.estimated_hours || 10), 0);
  elements.roadmapTotalHours.textContent = `${totalHours} hrs`;

  elements.milestonesStream.innerHTML = "";

  milestones.forEach((m, index) => {
    const card = document.createElement("div");
    card.className = "milestone-card";

    // Difficulty badge class
    const diff = (m.difficulty || "Beginner").toLowerCase();
    let diffClass = "badge-diff-beginner";
    if (diff.includes("intermediate")) diffClass = "badge-diff-intermediate";
    if (diff.includes("advanced")) diffClass = "badge-diff-advanced";

    // Topics list
    const topicsHtml = (m.topics_to_learn || [])
      .map((topic, tIdx) => {
        const topicId = `topic-${index}-${tIdx}`;
        const isChecked = state.checkedTopics.has(topicId);
        return `
          <li class="topic-item ${isChecked ? "completed" : ""}" data-topic-id="${topicId}">
            <input type="checkbox" class="topic-checkbox" ${isChecked ? "checked" : ""} />
            <span>${escapeHtml(topic)}</span>
          </li>
        `;
      })
      .join("");

    // Resources cards
    const resourcesHtml = (m.resources || [])
      .map((res) => {
        const isFree = res.is_free !== false;
        return `
          <a href="${escapeHtml(res.url || "#")}" target="_blank" rel="noopener noreferrer" class="resource-card">
            <div class="resource-info">
              <span class="resource-title">${escapeHtml(res.title || m.skill_name + " Resource")}</span>
              <div class="resource-meta">
                <span><i class="fa-solid fa-tag"></i> ${escapeHtml(res.resource_type || "Guide")}</span>
                <span class="${isFree ? "resource-badge-free" : "resource-badge-paid"}">
                  ${isFree ? "Free" : "Paid"}
                </span>
              </div>
            </div>
            <i class="fa-solid fa-arrow-up-right-from-square resource-ext-icon"></i>
          </a>
        `;
      })
      .join("");

    card.innerHTML = `
      <div class="milestone-header">
        <div class="milestone-skill-row">
          <div class="milestone-number">${index + 1}</div>
          <h4 class="milestone-skill-title">${escapeHtml(m.skill_name)}</h4>
        </div>
        <div class="milestone-badges">
          <span class="badge badge-timeline"><i class="fa-regular fa-clock"></i> ${escapeHtml(m.week_label || "Week " + (index + 1))}</span>
          <span class="badge badge-hours"><i class="fa-solid fa-bolt"></i> ${m.estimated_hours || 10} hrs</span>
          <span class="badge ${diffClass}"><i class="fa-solid fa-signal"></i> ${escapeHtml(m.difficulty || "Beginner")}</span>
        </div>
      </div>

      <div class="milestone-body">
        <div class="topics-box">
          <div class="box-title"><i class="fa-solid fa-list-check"></i> Core Topics to Master</div>
          <ul class="topics-list">
            ${topicsHtml || '<li class="text-muted">No subtopics defined.</li>'}
          </ul>
        </div>

        <div class="project-box">
          <div class="box-title"><i class="fa-solid fa-laptop-code"></i> Hands-On Proof Project</div>
          <p class="project-text">${escapeHtml(m.hands_on_project || "Build a working prototype demonstrating " + m.skill_name + " functionality.")}</p>
        </div>
      </div>

      <div class="resources-section">
        <div class="resources-title"><i class="fa-solid fa-compass"></i> Curated Learning Resources</div>
        <div class="resources-grid">
          ${resourcesHtml || '<p class="text-muted">No external links found.</p>'}
        </div>
      </div>
    `;

    // Add interactivity to checklist
    card.querySelectorAll(".topic-item").forEach((item) => {
      const checkbox = item.querySelector(".topic-checkbox");
      const topicId = item.getAttribute("data-topic-id");

      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          item.classList.add("completed");
          state.checkedTopics.add(topicId);
        } else {
          item.classList.remove("completed");
          state.checkedTopics.delete(topicId);
        }
      });
    });

    elements.milestonesStream.appendChild(card);
  });
}

// ============================================================================
// Utilities
// ============================================================================

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  let icon = "fa-circle-info";
  if (type === "success") icon = "fa-circle-check";
  if (type === "error") icon = "fa-circle-exclamation";

  toast.innerHTML = `
    <i class="fa-solid ${icon}"></i>
    <span>${escapeHtml(message)}</span>
  `;

  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(15px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
