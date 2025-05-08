function previewImage(event) {
    const reader = new FileReader();
    reader.onload = function() {
        document.getElementById('profile-preview').src = reader.result;
        document.querySelector('.profile-image').src = reader.result;  // Update sidebar image in real-time
    }
    reader.readAsDataURL(event.target.files[0]);
}
    function previewImage(event) {
        const reader = new FileReader();
        reader.onload = function() {
            const preview = document.getElementById('profile-preview');
            preview.src = reader.result;
        }
        reader.readAsDataURL(event.target.files[0]);
    }

    const badges = document.querySelectorAll('.badge-option');
    badges.forEach(badge => {
        badge.addEventListener('click', () => {
            badge.classList.toggle('selected');
        });
    });