document.addEventListener('DOMContentLoaded', () => {
    const uploadedPhotos = document.getElementById('upload_data');
    const uploadForm = document.getElementById('upload_photos');
    const uploadBtn = document.getElementById('btn');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    const uploadSuccess = document.getElementById('uploadSuccess');

    var notyf = new Notyf({ duration: 5000 });

    // function validate_input(input) {
    //     const allowed_types = ['image/jpeg', 'image/png', 'image/psd', 'image/jpg', 'image/webp'];
    //     const files = input.files;

    //     for (let index = 0; index < files.length; index++) {
    //         if (!allowed_types.includes(files[index].type)) {
    //             notyf.error("Invalid file type! Please upload only images.");
    //             input.value = '';
    //         }
    //     }
    // }

    // if (uploadedPhotos) {
    //     uploadedPhotos.addEventListener('change', (e) => {
    //         validate_input(e.target);
    //     });
    // }

    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const formdata = new FormData(uploadForm);
            let hasFiles = uploadedPhotos.files.length > 0;

            if (!hasFiles) {
                notyf.error("Please select or upload files");
                return;
            }

            // Show Progress Bar
            progressBarContainer.classList.remove("hidden");
            progressBar.style.width = "0%";
            progressBar.textContent = "0%";
            uploadSuccess.classList.add("hidden");

            const xhr = new XMLHttpRequest();

            // Track progress using XHR
            xhr.upload.onprogress = function (event) {
                if (event.lengthComputable) {
                    let percent = Math.round((event.loaded / event.total) * 100);
                    progressBar.style.width = `${percent}%`;
                    progressBar.textContent = `${percent}%`;
                    progressBarContainer.setAttribute("aria-valuenow", percent);
                }
            };

            xhr.onload = function () {
                if (xhr.status === 200) {
                    progressBar.style.width = "100%";
                    progressBar.textContent = "100%";
                    uploadSuccess.classList.remove("hidden");
                } else {
                    notyf.error("Upload failed");
                    progressBarContainer.classList.add("hidden");
                }
            };

            xhr.onerror = function () {
                notyf.error("Upload error");
                progressBarContainer.classList.add("hidden");
            };

            xhr.open("POST", uploadForm.action, true);
            xhr.setRequestHeader("X-CSRFToken", uploadForm.querySelector('[name=csrfmiddlewaretoken]').value);
            xhr.send(formdata);
        });
    }
});
