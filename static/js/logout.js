document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;
    const logoutDialog = document.getElementById('logoutDialog');
    const cancelBtn = document.getElementById('cancelBtn');
    const confirmLogoutBtn = document.getElementById('confirmLogoutBtn');
    const logoutForm = document.getElementById('logoutForm');

    logoutBtn.addEventListener('click', function(e) {
        e.preventDefault(); 
        logoutDialog.showModal();
    });

    cancelBtn.addEventListener('click', function() {
        logoutDialog.close();
    });

    confirmLogoutBtn.addEventListener('click', function() {
        logoutForm.submit(); 
    });

    logoutDialog.addEventListener('click', function(e) {
        const rect = logoutDialog.getBoundingClientRect();
        if (
            e.clientX < rect.left ||
            e.clientX > rect.right ||
            e.clientY < rect.top ||
            e.clientY > rect.bottom
        ) {
            logoutDialog.close();
        }
    });
});