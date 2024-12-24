document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('selfie');
    const cameraInput = document.getElementById('camera_selfie');
    fileInput.textContent('SELFIE')

    fileInput.addEventListener('change', () => {
        cameraInput.disabled = fileInput.files.length > 0;
    });

    cameraInput.addEventListener('change', () => {
        fileInput.disabled = cameraInput.files.length > 0;
    });
});
