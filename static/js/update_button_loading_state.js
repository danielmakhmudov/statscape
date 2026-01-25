document.addEventListener('DOMContentLoaded', function() {
const updateForm = document.querySelector('.update-form');
const updateButton = document.querySelector('.btn-update');

if (updateForm && updateButton) {
    updateForm.addEventListener('submit', function(e) {
        updateButton.disabled = true;
        updateButton.style.opacity = '0.6';
        updateButton.style.cursor = 'wait';
        updateButton.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>';
        updateButton.querySelector('svg').style.animation = 'spin 1s linear infinite';
    });
}});