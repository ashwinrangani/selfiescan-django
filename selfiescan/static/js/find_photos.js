// ================= GLOBAL — Back Button LightGallery Handling =================
let lgInstanceFind = null;
let lgOpenFind = false;

window.addEventListener("popstate", function (event) {
    if (lgOpenFind && lgInstanceFind) {
        // Close LightGallery instead of navigating back
        try {
            lgInstanceFind.closeGallery();
        } catch (e) {}

        // Restore fake state to prevent actual backward navigation again
        history.pushState({ lgFind: true }, "");
    }
});
// ==============================================================================


// upload_selfie form
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('selfie');
    const cameraInput = document.getElementById('camera_selfie');
    const imagePreview = document.getElementById('image-preview');
    const clearPreviewButton = document.getElementById('clear-preview');
    const uploadForm = document.getElementById('upload_selfie');
    const loadingState = document.querySelector('.loading');
    const is_event_downloadable = document.getElementById('lightgallery').dataset.eventIsdownload.toLowerCase() === "true";

    var notyf = new Notyf({ duration: 5000 });

    function validate_input(input) {
        const allowed_types = ['image/jpeg', 'image/png', 'image/psd', 'image/jpg', 'image/webp'];
        const files = input.files;

        for (let index = 0; index < files.length; index++) {
            if (!allowed_types.includes(files[index].type)) {
                notyf.error("Invalid file type! Please upload only images.");
                input.value = '';
            }
        }
    }

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

    if (fileInput) {
        fileInput.addEventListener('change', (event) => {
            validate_input(event.target);
            cameraInput.disabled = fileInput.files.length > 0;
            updatePreview(fileInput);
        });
    }

    if (cameraInput) {
        cameraInput.addEventListener('change', (event) => {
            validate_input(event.target);
            fileInput.disabled = cameraInput.files.length > 0;
            updatePreview(cameraInput);
        });
    }

    if (clearPreviewButton) {
        clearPreviewButton.addEventListener('click', clearPreview);
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const formdata = new FormData(uploadForm);

            const fileInputs = [fileInput, cameraInput];
            let hasFiles = fileInputs.some(input => input && input.files.length > 0);

            if (!hasFiles) {
                notyf.error("Please select image or take a photo");
                loadingState.style.display = 'none';
                return;
            }

            loadingState.style.display = 'block';

            fetch(uploadForm.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': uploadForm.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: formdata,
            })
                .then((response) => response.json())
                .then((data) => {
                    loadingState.style.display = 'none';

                    if (data.matches) {
                        const messages = document.querySelector('.messages');
                        const count = data.matches.length;

                        if (count > 0) {
                            messages.textContent = `${count} ${data.message}`;
                        } else {
                            messages.textContent = data.message;
                        }

                        const matchesContainer = document.getElementById("lightgallery");
                        matchesContainer.innerHTML = '';

                        data.matches.forEach(match => {
                            const container = document.createElement('div');
                            container.className = "overflow-hidden rounded-lg";

                            const anchor = document.createElement('a');
                            anchor.href = match.medium;               // lightbox image
                            anchor.dataset.src = match.medium;
                            anchor.dataset.downloadUrl = match.large; // download target
                            anchor.className = "block mb-4";

                            const img = document.createElement('img');
                            img.src = match.thumb;                    // thumbnail
                            img.alt = "Matched photo";
                            img.loading = "lazy";
                            img.className =
                                "w-full h-auto rounded-lg object-cover shadow-md shadow-gray-600 hover:scale-105 transition duration-300";

                            if (!is_event_downloadable) {
                                img.oncontextmenu = () => false;
                                img.draggable = false;
                            }

                            anchor.appendChild(img);
                            container.appendChild(anchor);
                            matchesContainer.appendChild(container);
                        });


                        // ================= LightGallery Safe Init =================
                        const lgEl = document.getElementById("lightgallery");

                        // Destroy previous instance if exists
                        if (lgInstanceFind) {
                            try {
                                lgInstanceFind.destroy(true);
                            } catch (e) {}
                        }

                        lgInstanceFind = lightGallery(lgEl, {
                            plugins: [lgZoom, lgFullscreen],
                            selector: 'a',
                            speed: 400,
                            licenseKey: '0000-0000-000-0000',
                            download: is_event_downloadable,

                            mobileSettings: {
                                controls: true,
                                showCloseIcon: true,
                                download: is_event_downloadable,
                                closeOnTap: false,
                            },
                        });

                        // Open + Close tracking (for back button fix)
                        lgEl.addEventListener("lgAfterOpen", () => {
                            lgOpenFind = true;
                            history.pushState({ lgFind: true }, "");
                        });

                        lgEl.addEventListener("lgAfterClose", () => {
                            lgOpenFind = false;
                        });

                        // Disable drag/save on each slide load
                        lgEl.addEventListener('lgAfterSlide', function () {
                            const galleryImg = document.querySelector('.lg-current .lg-img-wrap img');
                            if (galleryImg) {
                                if (!is_event_downloadable) {
                                    galleryImg.setAttribute('oncontextmenu', 'return false;');
                                    galleryImg.setAttribute('draggable', 'false');
                                } else {
                                    galleryImg.setAttribute('oncontextmenu', 'return true;');
                                    galleryImg.setAttribute('draggable', 'true');
                                }
                            }
                        });
                        // ============================================================
                    }
                })
                .catch((error) => {
                    loadingState.style.display = 'none';
                    console.error('Error:', error);
                });
        });
    }
});

