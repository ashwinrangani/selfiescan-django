document.addEventListener("DOMContentLoaded", function () {
    const profileForm = document.getElementById("profileForm");
    const profileImage = document.getElementById("profileImage");

    profileForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Prevent normal form submission

        let formData = new FormData(profileForm);
        

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
                console.log("Profile updated successfully!");
                console.log(data)
                // ✅ Check if `profile_img_url` exists before updating
                if (data.profile_img_url && profileImage) {
                    profileImage.src = data.profile_img_url;
                }
            } else {
                console.error("Error updating profile!", data.errors);
            }
        })
        .catch(error => console.error("Fetch error:", error));
    });
});
