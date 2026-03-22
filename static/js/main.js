function toggleModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.toggle('hidden');
}
function toggleDrawer() {
  document.getElementById('mobile-drawer')?.classList.toggle('open');
}
function closeDrawer() {
  document.getElementById('mobile-drawer')?.classList.remove('open');
}
function toggleDayPicker(radio) {
  document.getElementById('planned-options')?.classList.toggle('hidden', radio.value !== 'planned');
}
function toggleSugDay(radio) {
  document.getElementById('sug-planned-opts')?.classList.toggle('hidden', radio.value !== 'planned');
}
function selectIcon(icon, el) {
  document.getElementById('selected-icon').value = icon;
  document.querySelectorAll('.icon-opt').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
}
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flashes
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });
  // Close drawer on outside click
  document.addEventListener('click', e => {
    const drawer = document.getElementById('mobile-drawer');
    const hamburger = document.querySelector('.hamburger');
    if (drawer?.classList.contains('open') && !drawer.contains(e.target) && !hamburger?.contains(e.target)) {
      drawer.classList.remove('open');
    }
  });
});
