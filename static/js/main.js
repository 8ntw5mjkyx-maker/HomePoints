// ── Modals ────────────────────────────────────────────────────
function toggleModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.toggle('hidden');
}

// ── Mobile drawer ─────────────────────────────────────────────
function toggleDrawer() {
  document.getElementById('mobile-drawer')?.classList.toggle('open');
}
function closeDrawer() {
  document.getElementById('mobile-drawer')?.classList.remove('open');
}

// ── Day picker for task type ──────────────────────────────────
function toggleDayPicker(radio) {
  const opts = document.getElementById('planned-options');
  if (opts) opts.classList.toggle('hidden', radio.value !== 'planned');
}

function toggleSugDay(radio) {
  const opts = document.getElementById('sug-planned-opts');
  if (opts) opts.classList.toggle('hidden', radio.value !== 'planned');
}

// ── Icon picker ───────────────────────────────────────────────
function selectIcon(icon, el) {
  document.getElementById('selected-icon').value = icon;
  document.querySelectorAll('.icon-opt').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
}

// ── Suggested task modal ──────────────────────────────────────
function openSuggested(title, icon, points) {
  document.getElementById('sug-title').value = title;
  document.getElementById('sug-icon').value = icon;
  document.getElementById('sug-points').value = points;
  document.getElementById('sug-modal-title').textContent = icon + ' ' + title;
  toggleModal('suggested-modal');
}

// ── Auto-dismiss flash messages ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });

  // Close drawer when clicking outside
  document.addEventListener('click', (e) => {
    const drawer = document.getElementById('mobile-drawer');
    const hamburger = document.querySelector('.hamburger');
    if (drawer && drawer.classList.contains('open') &&
        !drawer.contains(e.target) && !hamburger?.contains(e.target)) {
      drawer.classList.remove('open');
    }
  });
});
