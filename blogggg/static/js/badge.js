function showSuccess(message) {
    const flash = document.getElementById('successFlash');
    flash.textContent = message;
    flash.style.display = 'block';
    setTimeout(() => {
        flash.style.display = 'none';
    }, 3000);
}

document.querySelectorAll('.pill').forEach(pill => {
    pill.addEventListener('click', () => {
        document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
    });
});