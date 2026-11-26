/**
 * SkillBridge Frontend Client
 * Modern JavaScript application handling Career Analysis,
 * Interactive Bento Dashboard, Skill Gap Matrix, AI Roadmap Generation,
 * and Excel Export.
 */

// API Configuration
const API_BASE_URL = (
  window.location.protocol.startsWith("http")
    ? window.location.origin
    : "http://127.0.0.1:8000"
).replace(/\/$/, "");

// Global Application State
const state = {
  selectedFile: null,
  careers: [],
  selectedCareer: "",
  activeMode: "career", // "career" | "jd"
  analysisResult: null,
  roadmapData: null,
  activeSkillFilter: "all",
  skillSearchTerm: "",
  checkedTopics: new Set(),
};

// Storage Keys for Controlled Persistence
const STORAGE_KEYS = {
  THEME: "skillbridge_theme",
  SERVER_BOOT_ID: "skillbridge_server_boot_id",
  SESSION_ANALYSIS: "skillbridge_session_analysis",
  SESSION_ROADMAP: "skillbridge_session_roadmap",
  PREFIX_TOPICS: "skillbridge_topics_",
};

function getRoadmapStorageKey(roadmap) {
  if (!roadmap || !roadmap.career) return `${STORAGE_KEYS.PREFIX_TOPICS}default`;
  const careerSlug = String(roadmap.career).toLowerCase().replace(/[^a-z0-9]+/g, "_");
  const skillsList = (roadmap.milestones || [])
    .map((m) => String(m.skill_name || "").toLowerCase().trim())
    .sort()
    .join("|");
  let hash = 0;
  for (let i = 0; i < skillsList.length; i++) {
    hash = (hash << 5) - hash + skillsList.charCodeAt(i);
    hash |= 0;
  }
  const hashStr = Math.abs(hash).toString(36);
  return `${STORAGE_KEYS.PREFIX_TOPICS}${careerSlug}_${hashStr}`;
}

function loadCompletedTopicsForRoadmap(roadmap) {
  if (!roadmap) return new Set();
  const key = getRoadmapStorageKey(roadmap);
  try {
    const raw = localStorage.getItem(key);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return new Set(parsed);
      }
    }
  } catch (err) {
    console.warn("Could not load completed topics from localStorage:", err);
  }
  return new Set();
}

function saveCompletedTopicsForRoadmap(roadmap, checkedSet) {
  if (!roadmap) return;
  const key = getRoadmapStorageKey(roadmap);
  try {
    localStorage.setItem(key, JSON.stringify(Array.from(checkedSet)));
  } catch (err) {
    console.warn("Could not save completed topics to localStorage:", err);
  }
}

function safeSessionSet(key, value) {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.warn(`Could not save ${key} to sessionStorage:`, err);
  }
}

function safeSessionGet(key) {
  try {
    const item = sessionStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  } catch (err) {
    console.warn(`Could not parse ${key} from sessionStorage:`, err);
    try {
      sessionStorage.removeItem(key);
    } catch (_) {}
    return null;
  }
}

function safeSessionRemove(key) {
  try {
    sessionStorage.removeItem(key);
  } catch (_) {}
}

// DOM Elements
const elements = {
  systemStatus: document.getElementById("systemStatus"),
  analysisForm: document.getElementById("analysisForm"),
  modeCareerBtn: document.getElementById("modeCareerBtn"),
  modeJdBtn: document.getElementById("modeJdBtn"),
  careerModeWrapper: document.getElementById("careerModeWrapper"),
  jdModeWrapper: document.getElementById("jdModeWrapper"),
  jdTextInput: document.getElementById("jdTextInput"),
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
  metaJdPill: document.getElementById("metaJdPill"),
  metaJdText: document.getElementById("metaJdText"),
  scoreCircle: document.getElementById("scoreCircle"),
  matchPercentage: document.getElementById("matchPercentage"),
  readinessGradeBadge: document.getElementById("readinessGradeBadge"),
  readinessSummaryText: document.getElementById("readinessSummaryText"),
  matchedCount: document.getElementById("matchedCount"),
  missingCount: document.getElementById("missingCount"),
  totalRequiredCount: document.getElementById("totalRequiredCount"),

  // Skill Extraction & Benchmark Comparison Studio
  extractedCandidateCount: document.getElementById("extractedCandidateCount"),
  extractedCandidateTags: document.getElementById("extractedCandidateTags"),
  benchmarkColHeading: document.getElementById("benchmarkColHeading"),
  extractedRequiredCount: document.getElementById("extractedRequiredCount"),
  extractedRequiredTags: document.getElementById("extractedRequiredTags"),

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
  evidenceInspector: document.getElementById("evidenceInspector"),
  evidenceSkillName: document.getElementById("evidenceSkillName"),
  evidenceTierPill: document.getElementById("evidenceTierPill"),
  evidenceQuoteText: document.getElementById("evidenceQuoteText"),
  evidenceCloseBtn: document.getElementById("evidenceCloseBtn"),
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
  themeToggleBtn: document.getElementById("themeToggleBtn"),
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  checkBackendHealth();
  loadCareers();
  initDropzone();
  initFormListeners();
  initFilterListeners();
  initRoadmapListeners();
});

function initTheme() {
  let mode = "system";
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.THEME);
    if (saved === "light" || saved === "dark" || saved === "system") {
      mode = saved;
    }
  } catch (_) {}

  applyThemeMode(mode);

  // Wire 3-way segmented buttons if present
  const themeBtns = document.querySelectorAll(".theme-select-btn");
  themeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const selectedMode = btn.getAttribute("data-theme-mode") || "system";
      applyThemeMode(selectedMode);
      try {
        localStorage.setItem(STORAGE_KEYS.THEME, selectedMode);
      } catch (_) {}
    });
  });

  // Preserve compatibility with elements.themeToggleBtn (cycles through light -> dark -> system)
  if (elements.themeToggleBtn) {
    elements.themeToggleBtn.addEventListener("click", () => {
      let currentMode = "system";
      try {
        currentMode = localStorage.getItem(STORAGE_KEYS.THEME) || "system";
      } catch (_) {}

      let nextMode = "light";
      if (currentMode === "light") nextMode = "dark";
      else if (currentMode === "dark") nextMode = "system";
      else nextMode = "light";

      applyThemeMode(nextMode);
      try {
        localStorage.setItem(STORAGE_KEYS.THEME, nextMode);
      } catch (_) {}
    });
  }

  // Listen to OS system color-scheme changes
  if (window.matchMedia) {
    const colorSchemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      let currentMode = "system";
      try {
        currentMode = localStorage.getItem(STORAGE_KEYS.THEME) || "system";
      } catch (_) {}
      if (currentMode === "system") {
        applyThemeMode("system", false);
      }
    };
    if (colorSchemeQuery.addEventListener) {
      colorSchemeQuery.addEventListener("change", handler);
    } else if (colorSchemeQuery.addListener) {
      colorSchemeQuery.addListener(handler);
    }
  }
}

function applyThemeMode(mode, save = true) {
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = mode === "dark" || (mode === "system" && prefersDark);

  document.documentElement.classList.toggle("dark-mode", isDark);
  document.body.classList.toggle("dark-mode", isDark);

  // Update segmented buttons
  const themeBtns = document.querySelectorAll(".theme-select-btn");
  themeBtns.forEach((btn) => {
    if (btn.getAttribute("data-theme-mode") === mode) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // Update legacy themeToggleBtn icon & label for backward compatibility
  if (elements.themeToggleBtn) {
    const icon = elements.themeToggleBtn.querySelector(".theme-toggle-icon");
    const label = elements.themeToggleBtn.querySelector(".theme-toggle-label");
    if (icon) {
      if (mode === "system") {
        icon.className = "fa-solid fa-desktop theme-toggle-icon";
      } else {
        icon.className = isDark ? "fa-solid fa-moon theme-toggle-icon" : "fa-solid fa-sun theme-toggle-icon";
      }
    }
    if (label) {
      if (mode === "system") {
        label.textContent = "System";
      } else {
        label.textContent = isDark ? "Dark" : "Light";
      }
    }
  }
}

function applyTheme(isDark) {
  applyThemeMode(isDark ? "dark" : "light");
}

function initRestoredState() {
  const savedAnalysis = safeSessionGet(STORAGE_KEYS.SESSION_ANALYSIS);
  if (savedAnalysis && typeof savedAnalysis === "object") {
    state.analysisResult = savedAnalysis;
    state.selectedCareer = savedAnalysis.career || "";
    renderDashboard(savedAnalysis);

    const savedRoadmap = safeSessionGet(STORAGE_KEYS.SESSION_ROADMAP);
    if (savedRoadmap && typeof savedRoadmap === "object") {
      state.roadmapData = savedRoadmap;
      state.checkedTopics = loadCompletedTopicsForRoadmap(savedRoadmap);
      renderRoadmap(savedRoadmap);
    }
  }
}

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

        // Server Restart vs Normal Page Refresh Detection
        if (data.boot_id) {
          const lastBootId = safeSessionGet(STORAGE_KEYS.SERVER_BOOT_ID);
          if (!lastBootId) {
            safeSessionSet(STORAGE_KEYS.SERVER_BOOT_ID, data.boot_id);
            initRestoredState();
          } else if (lastBootId !== data.boot_id) {
            // New server instance detected (server was restarted)!
            // Clear previous session data for a 100% fresh start
            safeSessionRemove(STORAGE_KEYS.SESSION_ANALYSIS);
            safeSessionRemove(STORAGE_KEYS.SESSION_ROADMAP);
            safeSessionSet(STORAGE_KEYS.SERVER_BOOT_ID, data.boot_id);
            if (elements.dashboardSection) elements.dashboardSection.classList.add("hidden");
            if (elements.roadmapDisplayWrapper) elements.roadmapDisplayWrapper.classList.add("hidden");
          } else {
            // Same server instance (normal page refresh) -> preserve active analysis!
            initRestoredState();
          }
        } else {
          initRestoredState();
        }
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
  // Mode switcher listeners
  if (elements.modeCareerBtn && elements.modeJdBtn) {
    elements.modeCareerBtn.addEventListener("click", () => {
      state.activeMode = "career";
      elements.modeCareerBtn.classList.add("active");
      elements.modeJdBtn.classList.remove("active");
      elements.careerModeWrapper.classList.remove("hidden");
      elements.jdModeWrapper.classList.add("hidden");
    });

    elements.modeJdBtn.addEventListener("click", () => {
      state.activeMode = "jd";
      elements.modeJdBtn.classList.add("active");
      elements.modeCareerBtn.classList.remove("active");
      elements.jdModeWrapper.classList.remove("hidden");
      elements.careerModeWrapper.classList.add("hidden");
    });
  }

  elements.analysisForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    let career = elements.careerSelect.value;
    let jobDescription = null;

    if (state.activeMode === "jd") {
      jobDescription = (elements.jdTextInput?.value || "").trim();
      if (!jobDescription || jobDescription.length < 30) {
        showToast("Please paste a meaningful Job Description (at least 30 characters).", "error");
        return;
      }
      career = career || "Custom Target Role";
    } else {
      if (!career) {
        showToast("Please choose a target career path.", "error");
        return;
      }
    }

    if (!state.selectedFile) {
      showToast("Please upload your resume file (PDF or DOCX).", "error");
      return;
    }

    state.selectedCareer = career;
    await runAnalysis(career, state.selectedFile, jobDescription);
  });
}

async function runAnalysis(career, file, jobDescription = null) {
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
  if (jobDescription) {
    formData.append("job_description", jobDescription);
  }

  try {
    const stepperTimer1 = setTimeout(() => {
      setStepperStep(2, "Extracting profile with Groq AI...");
    }, 1200);

    const stepperTimer2 = setTimeout(() => {
      const step3Msg = jobDescription
        ? "Extracting required skills from JD & analyzing skill gap..."
        : "Matching competencies against role benchmark...";
      setStepperStep(3, step3Msg);
    }, 2800);

    const response = await fetch(`${API_BASE_URL}/career-agent/analyze`, {
      method: "POST",
      body: formData,
    });

    clearTimeout(stepperTimer1);
    clearTimeout(stepperTimer2);

    if (!response.ok) {
      let errorDetail = `Analysis failed (${response.status})`;
      try {
        const err = await response.json();
        errorDetail = formatApiError(err, errorDetail);
      } catch (_) {
        errorDetail = `Analysis failed with status ${response.status} (${response.statusText || "Server Error"})`;
      }
      throw new Error(errorDetail);
    }

    const data = await response.json();
    state.analysisResult = data;
    safeSessionSet(STORAGE_KEYS.SESSION_ANALYSIS, data);
    try {
      sessionStorage.removeItem(STORAGE_KEYS.SESSION_ROADMAP);
    } catch (_) {}
    state.roadmapData = null;
    elements.roadmapDisplayWrapper.classList.add("hidden");
    renderDashboard(data);
    showToast("Career diagnostic complete!", "success");

    // Scroll smoothly to results
    setTimeout(() => {
      elements.dashboardSection.scrollIntoView({ behavior: "smooth" });
    }, 200);

  } catch (err) {
    showToast(getErrorMessage(err, "Failed to analyze resume."), "error");
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

  if (data.jd_analysis && elements.metaJdPill) {
    elements.metaJdPill.classList.remove("hidden");
    const seniority = data.jd_analysis.seniority_level ? ` • ${data.jd_analysis.seniority_level}` : "";
    elements.metaJdText.textContent = `Job Description${seniority}`;
  } else if (elements.metaJdPill) {
    elements.metaJdPill.classList.add("hidden");
  }

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
    elements.readinessGradeBadge.style.color = "var(--tint-green-text)";
    elements.readinessSummaryText.textContent =
      "Your demonstrated experience aligns well with this role's requirements. Targeted upskilling in a few areas will strengthen your candidacy.";
    elements.scoreCircle.style.stroke = "var(--accent-emerald)";
  } else if (percentage >= 45) {
    elements.readinessGradeBadge.textContent = "Moderate Fit — Bridgeable Gap";
    elements.readinessGradeBadge.style.color = "var(--tint-amber-text)";
    elements.readinessSummaryText.textContent =
      "You have foundational competencies, but several industry-expected tools or frameworks are missing. The learning roadmap below addresses each gap.";
    elements.scoreCircle.style.stroke = "var(--accent-amber)";
  } else {
    elements.readinessGradeBadge.textContent = "Significant Growth Needed";
    elements.readinessGradeBadge.style.color = "var(--tint-amber-text)";
    elements.readinessSummaryText.textContent =
      "A meaningful skill delta exists for this role. Follow the structured curriculum below to systematically build and demonstrate these competencies.";
    elements.scoreCircle.style.stroke = "var(--accent-indigo)";
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

  // Skill Extraction & Benchmark Comparison Studio
  renderExtractionComparison(data);

  // Render Skill Cloud
  renderSkillsCloud();
}

function renderExtractionComparison(data) {
  if (!elements.extractedCandidateTags || !elements.extractedRequiredTags) return;

  const candidateSkills = (data.profile && Array.isArray(data.profile.skills)) ? data.profile.skills : [];
  const requiredSkills = Array.isArray(data.required_skills) ? data.required_skills : [];
  const matchedSkills = Array.isArray(data.matched_skills) ? data.matched_skills : [];

  // Create a lowercase set for fast matching comparison
  const matchedSet = new Set(matchedSkills.map((s) => String(s).toLowerCase().trim()));

  // 1. Candidate Extracted Skills Column
  if (elements.extractedCandidateCount) {
    elements.extractedCandidateCount.textContent = `${candidateSkills.length} ${candidateSkills.length === 1 ? "skill" : "skills"}`;
  }
  elements.extractedCandidateTags.innerHTML = "";

  if (candidateSkills.length === 0) {
    elements.extractedCandidateTags.innerHTML =
      '<div class="extraction-empty-state"><i class="fa-solid fa-circle-info"></i> No specific skills were extracted from this resume.</div>';
  } else {
    candidateSkills.forEach((skill) => {
      const isMatched = matchedSet.has(String(skill).toLowerCase().trim());
      const tag = document.createElement("span");
      tag.className = `extraction-tag ${isMatched ? "matched" : ""}`;
      tag.title = isMatched ? "Matches target benchmark requirement" : "Demonstrated candidate competency";

      const iconHtml = isMatched
        ? '<i class="fa-solid fa-check"></i> '
        : '<i class="fa-solid fa-id-badge"></i> ';

      tag.innerHTML = `${iconHtml}${escapeHtml(skill)}`;
      elements.extractedCandidateTags.appendChild(tag);
    });
  }

  // 2. Required / Benchmark Skills Column
  const isJd = Boolean(data.jd_analysis);
  if (elements.benchmarkColHeading) {
    elements.benchmarkColHeading.textContent = isJd ? "Job Description Requirements" : "Role Benchmark Requirements";
  }

  if (elements.extractedRequiredCount) {
    elements.extractedRequiredCount.textContent = `${requiredSkills.length} ${requiredSkills.length === 1 ? "skill" : "skills"}`;
  }
  elements.extractedRequiredTags.innerHTML = "";

  if (requiredSkills.length === 0) {
    elements.extractedRequiredTags.innerHTML =
      '<div class="extraction-empty-state"><i class="fa-solid fa-circle-info"></i> No required benchmark skills found.</div>';
  } else {
    requiredSkills.forEach((skill) => {
      const isMatched = matchedSet.has(String(skill).toLowerCase().trim());
      const tag = document.createElement("span");
      tag.className = `extraction-tag ${isMatched ? "matched" : "missing"}`;
      tag.title = isMatched ? "Fulfilled by candidate" : "Missing gap to bridge";

      const iconHtml = isMatched
        ? '<i class="fa-solid fa-check"></i> '
        : '<i class="fa-solid fa-triangle-exclamation"></i> ';

      tag.innerHTML = `${iconHtml}${escapeHtml(skill)}`;
      elements.extractedRequiredTags.appendChild(tag);
    });
  }
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

  if (elements.evidenceCloseBtn) {
    elements.evidenceCloseBtn.addEventListener("click", () => {
      if (elements.evidenceInspector) {
        elements.evidenceInspector.classList.add("hidden");
      }
      elements.skillsTagCloud.querySelectorAll(".skill-pill").forEach((p) => p.classList.remove("selected"));
    });
  }
}

function renderSkillsCloud() {
  if (!state.analysisResult) return;

  const matched = state.analysisResult.matched_skills || [];
  const missing = state.analysisResult.missing_skills || [];
  const assessments = state.analysisResult.proficiency_assessments || [];

  // Map proficiency assessment details by normalized skill name
  const profMap = new Map();
  assessments.forEach((item) => {
    if (item && item.skill) {
      profMap.set(item.skill.toLowerCase().trim(), item);
    }
  });

  elements.skillsTagCloud.innerHTML = "";
  if (elements.evidenceInspector) {
    elements.evidenceInspector.classList.add("hidden");
  }

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

    let badgeHtml = "";
    const prof = profMap.get(skill.name.toLowerCase().trim());

    if (skill.type === "matched" && prof) {
      const tier = (prof.evidence_tier || "mentioned").toLowerCase();
      let tierLabel = "Listed";
      let tierIcon = "fa-list-ul";

      if (tier === "professional") {
        tierLabel = "Work";
        tierIcon = "fa-briefcase";
      } else if (tier === "project") {
        tierLabel = "Project";
        tierIcon = "fa-code";
      } else if (tier === "internship") {
        tierLabel = "Intern";
        tierIcon = "fa-user-graduate";
      } else if (tier === "academic") {
        tierLabel = "Course";
        tierIcon = "fa-book-open";
      }

      badgeHtml = `<span class="evidence-badge tier-${tier}"><i class="fa-solid ${tierIcon}"></i> ${tierLabel}</span>`;
      span.title = `Evidence: ${prof.confidence || 'confirmed'} in ${tierLabel}. Click to inspect exact quote.`;
    } else if (skill.type === "missing") {
      span.title = `Click to inspect skill gap details.`;
    }

    span.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(skill.name)}</span> ${badgeHtml}`;

    span.addEventListener("click", () => {
      elements.skillsTagCloud.querySelectorAll(".skill-pill").forEach((p) => p.classList.remove("selected"));
      span.classList.add("selected");
      showEvidenceInspector(skill.name, prof, skill.type);
    });

    elements.skillsTagCloud.appendChild(span);
  });
}

function showEvidenceInspector(skillName, prof, skillType) {
  if (!elements.evidenceInspector) return;

  elements.evidenceSkillName.textContent = skillName;

  if (skillType === "matched" && prof) {
    const tier = (prof.evidence_tier || "mentioned").toLowerCase();
    const conf = (prof.confidence || "confirmed").toUpperCase();

    let tierHuman = "Skills Inventory Listing";
    if (tier === "professional") tierHuman = "Employment History";
    else if (tier === "project") tierHuman = "Practical Project Implementation";
    else if (tier === "internship") tierHuman = "Internship Experience";
    else if (tier === "academic") tierHuman = "Academic Coursework";

    elements.evidenceTierPill.textContent = `${conf} • ${tierHuman}`;
    elements.evidenceTierPill.style.color = (tier === "professional" || tier === "project") ? "var(--tint-green-text)" : "var(--tint-indigo-text)";
    elements.evidenceQuoteText.textContent = prof.supporting_evidence
      ? `"${prof.supporting_evidence}"`
      : "Verified across candidate profile credentials.";
  } else if (skillType === "matched") {
    elements.evidenceTierPill.textContent = "MATCHED COMPETENCY";
    elements.evidenceTierPill.style.color = "var(--tint-green-text)";
    elements.evidenceQuoteText.textContent = "Demonstrated across candidate resume credentials.";
  } else {
    elements.evidenceTierPill.textContent = "TARGET SKILL GAP";
    elements.evidenceTierPill.style.color = "var(--tint-amber-text)";
    elements.evidenceQuoteText.textContent = "This required competency was not identified in your resume. Review the generated learning roadmap below for structured study milestones and curated resources.";
  }

  elements.evidenceInspector.classList.remove("hidden");
  elements.evidenceInspector.scrollIntoView({ behavior: "smooth", block: "nearest" });
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
        let errDetail = `Roadmap generation failed (${response.status})`;
        try {
          const err = await response.json();
          errDetail = formatApiError(err, errDetail);
        } catch (_) {
          errDetail = `Roadmap generation failed with status ${response.status} (${response.statusText || "Server Error"})`;
        }
        throw new Error(errDetail);
      }

      const roadmap = await response.json();
      state.roadmapData = roadmap;
      state.checkedTopics = loadCompletedTopicsForRoadmap(roadmap);
      safeSessionSet(STORAGE_KEYS.SESSION_ROADMAP, roadmap);
      renderRoadmap(roadmap);
      showToast("Personalized roadmap generated with verified resources!", "success");

      setTimeout(() => {
        elements.roadmapDisplayWrapper.scrollIntoView({ behavior: "smooth" });
      }, 200);

    } catch (err) {
      showToast(getErrorMessage(err, "Roadmap generation failed."), "error");
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

      // Deep copy roadmapData and enrich each milestone with completed_topics
      const exportPayload = {
        ...state.roadmapData,
        milestones: (state.roadmapData.milestones || []).map((m) => {
          const completedForMilestone = (m.topics_to_learn || []).filter((topic) =>
            state.checkedTopics.has(`${m.skill_name}:::${topic}`)
          );
          return {
            ...m,
            completed_topics: completedForMilestone,
          };
        }),
      };

      const response = await fetch(`${API_BASE_URL}/roadmap/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(exportPayload),
      });

      if (!response.ok) {
        let errDetail = `Excel export failed (${response.status})`;
        try {
          const err = await response.json();
          errDetail = formatApiError(err, errDetail);
        } catch (_) {}
        throw new Error(errDetail);
      }

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
      showToast(getErrorMessage(err, "Could not export roadmap spreadsheet."), "error");
    } finally {
      elements.exportExcelBtn.disabled = false;
      elements.exportExcelBtn.innerHTML = '<i class="fa-solid fa-file-excel"></i> Export Roadmap (.xlsx)';
    }
  });
}

function renderRoadmap(roadmap) {
  elements.roadmapDisplayWrapper.classList.remove("hidden");
  elements.roadmapHeading.textContent = `Learning Roadmap — ${roadmap.career}`;

  // Make sure completed topics are loaded for this specific roadmap
  state.checkedTopics = loadCompletedTopicsForRoadmap(roadmap);

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
        const topicKey = `${m.skill_name}:::${topic}`;
        const isChecked = state.checkedTopics.has(topicKey) || state.checkedTopics.has(`topic-${index}-${tIdx}`);
        return `
          <li class="topic-item ${isChecked ? "completed" : ""}" data-topic-key="${escapeHtml(topicKey)}">
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

    // Add interactivity to checklist with persistence
    card.querySelectorAll(".topic-item").forEach((item) => {
      const checkbox = item.querySelector(".topic-checkbox");
      const topicKey = item.getAttribute("data-topic-key");

      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          item.classList.add("completed");
          state.checkedTopics.add(topicKey);
        } else {
          item.classList.remove("completed");
          state.checkedTopics.delete(topicKey);
        }
        saveCompletedTopicsForRoadmap(roadmap, state.checkedTopics);
      });
    });

    elements.milestonesStream.appendChild(card);
  });
}

// ============================================================================
// Utilities & Error Helpers
// ============================================================================

function formatApiError(errData, fallbackMessage = "Request failed") {
  if (!errData) return fallbackMessage;

  // Case 1: Simple string detail
  if (typeof errData.detail === "string" && errData.detail.trim()) {
    return errData.detail.trim();
  }

  // Case 2: FastAPI 422 validation error array
  if (Array.isArray(errData.detail) && errData.detail.length > 0) {
    const messages = errData.detail
      .map((item) => {
        if (!item || typeof item !== "object") return null;
        const field = Array.isArray(item.loc)
          ? item.loc.filter((p) => p !== "body").join(".")
          : "";
        const msg = item.msg || "Invalid value";
        return field ? `${field}: ${msg}` : msg;
      })
      .filter(Boolean);
    if (messages.length > 0) return messages.join(" | ");
  }

  // Case 3: Error object with message property
  if (typeof errData.message === "string" && errData.message.trim()) {
    return errData.message.trim();
  }

  // Case 4: Detail is another object
  if (typeof errData.detail === "object" && errData.detail !== null) {
    try {
      return JSON.stringify(errData.detail);
    } catch (_) {}
  }

  return fallbackMessage;
}

function getErrorMessage(err, fallback = "An unexpected error occurred.") {
  if (!err) return fallback;
  if (typeof err === "string") return err;
  if (err instanceof Error) {
    if (err.name === "TypeError" && err.message.toLowerCase().includes("fetch")) {
      return "Network connection error. Check that the backend server is reachable.";
    }
    return err.message || fallback;
  }
  return fallback;
}

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
