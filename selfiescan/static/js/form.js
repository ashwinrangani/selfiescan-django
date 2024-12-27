document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('selfie');
    const cameraInput = document.getElementById('camera_selfie');
    const imagePreview = document.getElementById('image-preview');
    const clearPreviewButton = document.getElementById('clear-preview');
    

    function updatePreview(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                clearPreviewButton.style.display = 'block';
            };
            reader.readAsDataURL(input.files[0]);
        }
    }
    function clearPreview() {
        fileInput.value = '';
        cameraInput.value = '';
        fileInput.disabled = false;
        cameraInput.disabled = false;
        imagePreview.src = '';
        imagePreview.style.display = 'none';
        clearPreviewButton.style.display = 'none';
    }

    fileInput.addEventListener('change', () => {
        cameraInput.disabled = fileInput.files.length > 0;
        updatePreview(fileInput);
    });

    cameraInput.addEventListener('change', () => {
        fileInput.disabled = cameraInput.files.length > 0;
        updatePreview(cameraInput);
    });
    clearPreviewButton.addEventListener('click', clearPreview);
});
