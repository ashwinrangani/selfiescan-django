// upload_selfie form

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('selfie');
    const cameraInput = document.getElementById('camera_selfie');
    const imagePreview = document.getElementById('image-preview');
    const clearPreviewButton = document.getElementById('clear-preview');
    const uploadForm = document.getElementById('upload_selfie');
    const loadingState = document.querySelector('.loading')
    const is_event_downloadable = document.getElementById('lightgallery').dataset.eventIsdownload.toLowerCase() === "true";
    console.log(is_event_downloadable);
    
    var notyf = new Notyf({
        duration: 5000
    })
    function validate_input(input){
        const allowed_types = ['image/jpeg', 'image/png', 'image/psd', 'image/jpg', 'image/webp']
        const files = input.files

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
        // const matchesContainer = document.querySelector('.matches-section');
        // matchesContainer.innerHTML = ''
    }

    if (fileInput){
        fileInput.addEventListener('change', (event) => {
            validate_input(event.target);
            cameraInput.disabled = fileInput.files.length > 0;
            updatePreview(fileInput);
        });
    }
    
    if(cameraInput){
        cameraInput.addEventListener('change', (event) => {
            validate_input(event.target);
            fileInput.disabled = cameraInput.files.length > 0;
            updatePreview(cameraInput);
        }); 
    }
    if(clearPreviewButton){
        clearPreviewButton.addEventListener('click', clearPreview);
    }
    
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            e.preventDefault()
            
            
    const formdata = new FormData(uploadForm)
            
    // Check if any file input fields contain files
    const fileInputs = [fileInput, cameraInput];
    let hasFiles = false;
    
    fileInputs.forEach(input => {
        if (input && input.files.length > 0) {
            hasFiles = true;
        }
    });

    if (!hasFiles) {
        notyf.error("Please select image or take a photo");
        loadingState.style.display = 'none';
        return; // Stop form submission
    } 
    loadingState.style.display = 'block';
            



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
                    matchesCount = data.matches.length
                    const messages = document.querySelector('.messages')
                    if  (matchesCount > 0 ) {
                        messages.textContent = `${matchesCount}` +  ` ${data.message}`
                    } else {
                        messages.textContent =  ` ${data.message}`
                    }
                    

                    const matchesContainer = document.getElementById("lightgallery");
                    matchesContainer.innerHTML = '';

                    data.matches.forEach((match) => {
                        const container = document.createElement('div')
                        container.className = "overflow-hidden rounded-lg"
                        const anchor = document.createElement('a');
                        anchor.href = match.path;
                        anchor.setAttribute('data-lg-download', match.path);
                        anchor.className = "block mb-4";

                        const img = document.createElement('img');
                        img.src = match.path;
                        img.alt = "Matched photo";
                        img.className = "w-full h-auto rounded-lg object-cover shadow-md shadow-gray-600 hover:scale-105 transition duration-300";
                        if (is_event_downloadable == false){
                            img.setAttribute("oncontextmenu", "return false;");
                            img.setAttribute("draggable", "false");
                        } else {
                            img.setAttribute("oncontextmenu", "return true;");
                            img.setAttribute("draggable", "true");
                        }

                        
                        anchor.appendChild(img);
                        container.appendChild(anchor);
                        matchesContainer.appendChild(container)
                    });


                    // Initialize lightGallery AFTER images are added
                    const lgEl = document.getElementById("lightgallery");
                    if (lgEl.lgInitialized) {
                    lgEl.lgDestroy(true); // destroy existing gallery
                    }
                    
                    lightGallery(lgEl, {
                        plugins: [lgZoom,lgFullscreen],
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
                    
                    lgEl.addEventListener('lgAfterSlide', function(event) {
                    // Find the currently active slide image
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

                }

                
            })
            .catch((error) => {
                loadingState.style.display = 'none';
                console.error('Error:', error);
            });
        })
    }
    
});
