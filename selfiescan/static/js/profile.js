document.addEventListener("DOMContentLoaded", function () {
    const profileForm = document.getElementById("profileForm");
    const profileImage = document.getElementById("profileImage");
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('loadingSpinner');
    
    var notyf = new Notyf();


    profileForm.addEventListener("submit", function (event) {
        event.preventDefault(); 

        let formData = new FormData(profileForm);
        btnText.innerText = 'Updating....'
        spinner.classList.value = 'block'

        fetch(profileForm.action, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(data)
                if (data.profile_img_url && profileImage) {
                    profileImage.src = data.profile_img_url;
                    btnText.innerText = 'Update Profile'
                    spinner.classList.value = 'hidden'
                    notyf.success("Profile updated successfully!");
                    
                    
                }
            } else {
                console.error("Error updating profile!", data.errors);
            }
        })
        .catch(error => console.error("Fetch error:", error));
    });
});
