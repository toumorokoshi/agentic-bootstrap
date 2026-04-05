/**
 * TaskFlow Dashboard Module
 * Handles the main dashboard view, task rendering, and user interactions.
 */

const API_BASE_URL = "http://localhost:5000/api";
const REFRESH_INTERVAL_MS = 30000;
const MAX_RECENT_TASKS = 15;
const ANIMATION_DURATION_MS = 200;
const DEBOUNCE_DELAY_MS = 300;

// Task priority labels and colors
const PRIORITY_CONFIG = {
  1: { label: "Low", color: "#94A3B8", icon: "arrow-down" },
  2: { label: "Medium", color: "#3B82F6", icon: "minus" },
  3: { label: "High", color: "#F59E0B", icon: "arrow-up" },
  4: { label: "Critical", color: "#EF4444", icon: "alert-triangle" },
};

// Status display configuration
const STATUS_CONFIG = {
  open: { label: "Open", color: "#6B7280", bgColor: "#F3F4F6" },
  in_progress: { label: "In Progress", color: "#3B82F6", bgColor: "#EFF6FF" },
  review: { label: "In Review", color: "#8B5CF6", bgColor: "#F5F3FF" },
  done: { label: "Done", color: "#10B981", bgColor: "#ECFDF5" },
  archived: { label: "Archived", color: "#9CA3AF", bgColor: "#F9FAFB" },
};

class TaskDashboard {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.tasks = [];
    this.projects = [];
    this.currentFilter = "all";
    this.searchQuery = "";
    this.sortField = "created_at";
    this.sortOrder = "desc";
    this.refreshTimer = null;
    this.isLoading = false;
    this.selectedProjectId = null;
    this.viewMode = "list";
    this.pageSize = 20;
    this.currentPage = 1;
  }

  async initialize() {
    this.renderSkeleton();
    await this.loadProjects();
    await this.loadTasks();
    this.attachEventListeners();
    this.startAutoRefresh();
    console.log("Dashboard initialized successfully");
  }

  renderSkeleton() {
    this.container.innerHTML = `
      <div class="dashboard-header">
        <h1 class="dashboard-title">My Tasks</h1>
        <div class="dashboard-actions">
          <input type="text" id="task-search" placeholder="Search tasks..." class="search-input" />
          <select id="status-filter" class="filter-select">
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="review">In Review</option>
            <option value="done">Done</option>
          </select>
          <select id="project-filter" class="filter-select">
            <option value="all">All Projects</option>
          </select>
          <button id="new-task-btn" class="btn btn-primary">New Task</button>
          <button id="toggle-view-btn" class="btn btn-secondary">Board View</button>
        </div>
      </div>
      <div class="dashboard-stats" id="stats-container"></div>
      <div class="task-list" id="task-container">
        <div class="loading-spinner">Loading tasks...</div>
      </div>
      <div class="pagination" id="pagination-container"></div>
    `;
  }

  async loadProjects() {
    try {
      const response = await fetch(`${API_BASE_URL}/projects`);
      if (!response.ok) throw new Error("Failed to load projects");
      const data = await response.json();
      this.projects = data.data.projects;
      this.renderProjectFilter();
    } catch (error) {
      console.error("Error loading projects:", error.message);
      this.showNotification("Failed to load projects", "error");
    }
  }

  async loadTasks() {
    if (this.isLoading) return;
    this.isLoading = true;

    try {
      let url = `${API_BASE_URL}/projects/${this.selectedProjectId || 1}/tasks`;
      url += `?sort_by=${this.sortField}&order=${this.sortOrder}`;
      url += `&page=${this.currentPage}&per_page=${this.pageSize}`;

      if (this.currentFilter !== "all") {
        url += `&status=${this.currentFilter}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to load tasks");
      const data = await response.json();
      this.tasks = data.data.tasks;
      this.renderTasks();
      this.renderStats();
      this.renderPagination(data.data.total);
    } catch (error) {
      console.error("Error loading tasks:", error.message);
      this.showNotification("Failed to load tasks", "error");
    } finally {
      this.isLoading = false;
    }
  }

  renderTasks() {
    const container = document.getElementById("task-container");
    if (this.tasks.length === 0) {
      container.innerHTML = '<div class="empty-state">No tasks found. Create one to get started!</div>';
      return;
    }

    const filteredTasks = this.filterTasks(this.tasks);
    container.innerHTML = filteredTasks.map((task) => this.renderTaskCard(task)).join("");
  }

  renderTaskCard(task) {
    const priority = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG[2];
    const status = STATUS_CONFIG[task.status] || STATUS_CONFIG.open;
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString() : "No due date";
    const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== "done";

    return `
      <div class="task-card ${isOverdue ? "task-overdue" : ""}" data-task-id="${task.task_id}">
        <div class="task-priority" style="background-color: ${priority.color}" title="${priority.label}"></div>
        <div class="task-content">
          <h3 class="task-title">${this.escapeHtml(task.title)}</h3>
          <p class="task-description">${this.escapeHtml(task.description || "")}</p>
          <div class="task-meta">
            <span class="task-status" style="color: ${status.color}; background-color: ${status.bgColor}">${status.label}</span>
            <span class="task-due ${isOverdue ? "overdue" : ""}">${dueDate}</span>
            <span class="task-assignee">${task.assignee ? task.assignee.display_name : "Unassigned"}</span>
            ${task.tags.map((tag) => `<span class="task-tag">${this.escapeHtml(tag)}</span>`).join("")}
          </div>
        </div>
        <div class="task-actions">
          <button class="btn-icon" onclick="dashboard.editTask(${task.task_id})" title="Edit task">✏️</button>
          <button class="btn-icon" onclick="dashboard.deleteTask(${task.task_id})" title="Delete task">🗑️</button>
        </div>
      </div>
    `;
  }

  renderStats() {
    const container = document.getElementById("stats-container");
    const total = this.tasks.length;
    const open = this.tasks.filter((t) => t.status === "open").length;
    const inProgress = this.tasks.filter((t) => t.status === "in_progress").length;
    const done = this.tasks.filter((t) => t.status === "done").length;
    const overdue = this.tasks.filter(
      (t) => t.due_date && new Date(t.due_date) < new Date() && t.status !== "done"
    ).length;

    container.innerHTML = `
      <div class="stat-card"><span class="stat-value">${total}</span><span class="stat-label">Total Tasks</span></div>
      <div class="stat-card"><span class="stat-value">${open}</span><span class="stat-label">Open</span></div>
      <div class="stat-card"><span class="stat-value">${inProgress}</span><span class="stat-label">In Progress</span></div>
      <div class="stat-card"><span class="stat-value">${done}</span><span class="stat-label">Completed</span></div>
      <div class="stat-card ${overdue > 0 ? "stat-warning" : ""}"><span class="stat-value">${overdue}</span><span class="stat-label">Overdue</span></div>
    `;
  }

  renderProjectFilter() {
    const select = document.getElementById("project-filter");
    if (!select) return;
    this.projects.forEach((project) => {
      const option = document.createElement("option");
      option.value = project.project_id;
      option.textContent = project.name;
      select.appendChild(option);
    });
  }

  renderPagination(total) {
    const container = document.getElementById("pagination-container");
    const totalPages = Math.ceil(total / this.pageSize);
    if (totalPages <= 1) {
      container.innerHTML = "";
      return;
    }

    let html = '<div class="pagination-controls">';
    html += `<button class="btn btn-sm" ${this.currentPage <= 1 ? "disabled" : ""} onclick="dashboard.goToPage(${this.currentPage - 1})">Previous</button>`;
    html += `<span class="page-info">Page ${this.currentPage} of ${totalPages}</span>`;
    html += `<button class="btn btn-sm" ${this.currentPage >= totalPages ? "disabled" : ""} onclick="dashboard.goToPage(${this.currentPage + 1})">Next</button>`;
    html += "</div>";
    container.innerHTML = html;
  }

  filterTasks(tasks) {
    let filtered = tasks;
    if (this.searchQuery) {
      const query = this.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (t) => t.title.toLowerCase().includes(query) || (t.description && t.description.toLowerCase().includes(query))
      );
    }
    return filtered;
  }

  attachEventListeners() {
    const searchInput = document.getElementById("task-search");
    if (searchInput) {
      searchInput.addEventListener("input", this.debounce((e) => {
        this.searchQuery = e.target.value;
        this.renderTasks();
      }, DEBOUNCE_DELAY_MS));
    }

    const statusFilter = document.getElementById("status-filter");
    if (statusFilter) {
      statusFilter.addEventListener("change", (e) => {
        this.currentFilter = e.target.value;
        this.currentPage = 1;
        this.loadTasks();
      });
    }

    const projectFilter = document.getElementById("project-filter");
    if (projectFilter) {
      projectFilter.addEventListener("change", (e) => {
        this.selectedProjectId = e.target.value === "all" ? null : parseInt(e.target.value);
        this.currentPage = 1;
        this.loadTasks();
      });
    }

    const newTaskBtn = document.getElementById("new-task-btn");
    if (newTaskBtn) {
      newTaskBtn.addEventListener("click", () => this.showCreateTaskModal());
    }

    const toggleViewBtn = document.getElementById("toggle-view-btn");
    if (toggleViewBtn) {
      toggleViewBtn.addEventListener("click", () => this.toggleViewMode());
    }
  }

  startAutoRefresh() {
    this.refreshTimer = setInterval(() => this.loadTasks(), REFRESH_INTERVAL_MS);
  }

  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  async editTask(taskId) {
    console.log(`Editing task ${taskId}`);
    // TODO: Implement edit modal
  }

  async deleteTask(taskId) {
    if (!confirm("Are you sure you want to delete this task?")) return;

    try {
      const task = this.tasks.find((t) => t.task_id === taskId);
      const projectId = task ? task.project_id : this.selectedProjectId || 1;
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks/${taskId}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete task");
      this.tasks = this.tasks.filter((t) => t.task_id !== taskId);
      this.renderTasks();
      this.renderStats();
      this.showNotification("Task deleted successfully", "success");
    } catch (error) {
      console.error("Error deleting task:", error.message);
      this.showNotification("Failed to delete task", "error");
    }
  }

  showCreateTaskModal() {
    console.log("Opening create task modal");
    // TODO: Implement create modal
  }

  toggleViewMode() {
    this.viewMode = this.viewMode === "list" ? "board" : "list";
    const btn = document.getElementById("toggle-view-btn");
    if (btn) {
      btn.textContent = this.viewMode === "list" ? "Board View" : "List View";
    }
    this.renderTasks();
  }

  goToPage(page) {
    this.currentPage = page;
    this.loadTasks();
  }

  showNotification(message, type = "info") {
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }

  escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  debounce(func, delay) {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
  }

  destroy() {
    this.stopAutoRefresh();
    this.container.innerHTML = "";
  }
}

// Initialize dashboard when DOM is ready
let dashboard;
document.addEventListener("DOMContentLoaded", () => {
  dashboard = new TaskDashboard("app");
  dashboard.initialize();
});
