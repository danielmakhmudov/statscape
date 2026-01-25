document.addEventListener('DOMContentLoaded', function() {
    const deleteProfileBtn = document.getElementById('deleteProfileBtn');
    if (!deleteProfileBtn) return;
    const deleteProfileDialog = document.getElementById('deleteProfileDialog');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const deleteProfileForm = document.getElementById('deleteProfileForm');

    deleteProfileBtn.addEventListener('click', function(e) {
        e.preventDefault(); 
        deleteProfileDialog.showModal();
    });

    cancelDeleteBtn.addEventListener('click', function() {
        deleteProfileDialog.close();
    });

    confirmDeleteBtn.addEventListener('click', function() {
        deleteProfileForm.submit(); 
    });

    deleteProfileDialog.addEventListener('click', function(e) {
        const rect = deleteProfileDialog.getBoundingClientRect();
        if (
            e.clientX < rect.left ||
            e.clientX > rect.right ||
            e.clientY < rect.top ||
            e.clientY > rect.bottom
        ) {
            deleteProfileDialog.close();
        }
    });
});