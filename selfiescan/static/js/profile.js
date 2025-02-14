document.addEventListener('DOMContentLoaded',()=>{
    const profileForm = document.getElementById('profileForm')
    const successMsg = document.getElementById('successMsg')
    const profileImgInput = document.getElementById('profileImgInput')
    const profileImage = document.getElementById('profileImage')
    const btnText = document.getElementById("btnText")
    const spinner = document.getElementById("loadingSpinner")

    document.addEventListener('submit',(e)=>{
        e.preventDefault()
        btnText.textContent = "Updating...";
        spinner.classList.remove("hidden");

        if(profileForm){
            let formData = new FormData(profileForm);

            fetch("{% url 'profile' %}", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    spinner.classList.add("hidden");
                    
                    // If profile picture is updated, change the image source
                    if (data.profile_img_url) {
                        profileImage.src = data.profile_img_url;
                    }
                }
            })
        }

    })
})