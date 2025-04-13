// upload_selfie form

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('selfie');
    const cameraInput = document.getElementById('camera_selfie');
    const imagePreview = document.getElementById('image-preview');
    const clearPreviewButton = document.getElementById('clear-preview');
    const uploadForm = document.getElementById('upload_selfie');
    const loadingState = document.querySelector('.loading')
    
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
        notyf.error("Please select or upload files");
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
                    console.log(data.matches)
                    matchesCount = data.matches.length
                    const messages = document.querySelector('.messages')
                    if  (matchesCount > 0 ) {
                        messages.textContent = `${matchesCount}` +  ` ${data.message}`
                    } else {
                        messages.textContent =  ` ${data.message}`
                    }
                    

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
                loadingState.style.display = 'none';
                console.error('Error:', error);
            });
        })
    }
    
});
