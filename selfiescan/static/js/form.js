document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('selfie');
    const cameraInput = document.getElementById('camera_selfie');
    const imagePreview = document.getElementById('image-preview');
    const clearPreviewButton = document.getElementById('clear-preview');
    const uploadForm = document.getElementById('upload_selfie');
    const loadingState = document.querySelector('.loading')

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
        // const matchesContainer = document.querySelector('.matches-section');
        // matchesContainer.innerHTML = ''
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

    uploadForm.addEventListener('submit', (e) => {
        e.preventDefault()
        loadingState.style.display = 'block'
        
        const formdata = new FormData(uploadForm)

        fetch(uploadForm.action, {
            method: 'POST',
            headers : {
                'X-CSRFToken': uploadForm.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: formdata,
        })
        .then((response) => response.json())
        .then((data) => {
            loadingState.style.display = 'none';
            
            if (data.matches) {
                const matchesContainer = document.querySelector('.matches-section');
                matchesContainer.innerHTML = '';
                data.matches.forEach((match) => {
                    matchesContainer.innerHTML += `
                    <div class="card group hover:shadow sm:max-w-sm">
                            <img src="${match.path}" alt="Match" class="transition-transform duration-500 md:w-60 md:h-60 rounded-md group-hover:scale-110"'/>
                            <p>Distance: ${match.distance}</p>
                        </div>
                    `;
                });
            }
        })
        .catch((error) => {
            loadingSpinner.style.display = 'none'; // Hide the spinner
            console.error('Error:', error);
        });
    })
});
