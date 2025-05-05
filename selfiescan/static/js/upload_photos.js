document.addEventListener('DOMContentLoaded', () => {
    const uploadedPhotos = document.getElementById('upload_data');
    const uploadForm = document.getElementById('upload_photos');
    const selectedPhotos = document.getElementById('selected-photos');
    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    const uploadSuccess = document.getElementById('uploadSuccess');

    let total_upload_count = parseInt(uploadForm.dataset.uploadCount) || 0
    const isUnlimited = uploadForm.dataset.unlimitedUpload === 'true';
    const billingURL = uploadForm.dataset.billingUrl;

    document.getElementById("upgrade-plan-btn").onclick = function () {
        if (billingURL) {
            window.location.href = billingURL;
        }
    };
    

    var notyf = new Notyf({ duration: 20000 ,dismissible: true });

    function validate_input(input) {
        const allowed_types = ['image/jpeg', 'image/png', 'image/psd', 'image/jpg', 'image/webp'];
        const files = input.files;
        selectedPhotos.textContent = "Photos Selected: " + files.length;

        for (let index = 0; index < files.length; index++) {
            if (!allowed_types.includes(files[index].type)) {
                notyf.error("Invalid file type! Please upload only images.");
                input.value = '';
                
            }
        }
    }

    if (uploadedPhotos) {
        uploadedPhotos.addEventListener('change', (e) => {
            validate_input(e.target);
            
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const formdata = new FormData(uploadForm);
            let hasFiles = uploadedPhotos.files.length > 0;

            if (!hasFiles) {
                notyf.error("Please select or upload files");
                return;
            }

            const totalCount = total_upload_count + uploadedPhotos.files.length;
            
            
            if (!isUnlimited && totalCount > 100) {
                document.getElementById("open-subscription-modal").click();
                return; // stop before uploading
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
                try {
                    const response = JSON.parse(xhr.responseText);
            
                    if (xhr.status === 200) {
                        progressBar.style.width = "100%";
                        progressBar.textContent = "100%";
                        uploadSuccess.classList.remove("hidden");
            
                        if (response.upload_success) {
                            total_upload_count += response.uploaded_images;
                            uploadForm.dataset.uploadCount = total_upload_count; // update the data attribute too
                            notyf.success(`Successfully uploaded ${response.uploaded_images} photo(s). Processing started.`);
                        } else if (response.message) {
                            notyf.success(response.message);
                        }
                    } else {
                        handleUploadError(response, xhr.status);
                    }
                } catch (error) {
                    notyf.error("An unexpected error occurred.");
                    progressBarContainer.classList.add("hidden");
                }
            };
            
            function handleUploadError(response, statusCode) {
                const message = response.message || "Upload failed";
                            
                if (statusCode === 403 && response.redirect) {
                    // Open the modal via trigger
                    document.getElementById("open-subscription-modal").click();
            
                    // Upgrade button click => redirect
                    document.getElementById("upgrade-plan-btn").onclick = function () {
                        window.location.href = response.redirect;
                    };
                } else {
                    notyf.error(message);
                }
            
                progressBarContainer.classList.add("hidden");
            }
            
            
            
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
