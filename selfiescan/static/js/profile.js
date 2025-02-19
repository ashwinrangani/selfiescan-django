document.addEventListener("DOMContentLoaded", function () {
  const profileForm = document.getElementById("profileForm");
  const profileImage = document.getElementById("profileImage");
  const btnText = document.getElementById("btnText");
  const spinner = document.getElementById("loadingSpinner");
  const updateBtn = document.getElementById("updateProfileBtn");
  const formInputs = profileForm.querySelectorAll("input, select, textarea"); // ✅ Track all fields

  var notyf = new Notyf();

  let isChanged = false; 

  
  const initialFormData = new FormData(profileForm);

  function checkForChanges() {
    isChanged = false;

    for (let input of formInputs) {
      let name = input.name;
      let initialValue = initialFormData.get(name);
      let currentValue = input.type === "file" ? input.files.length : input.value;

      if (initialValue !== currentValue) {
        isChanged = true;
        break;
      }
    }

    updateBtn.disabled = !isChanged; 
  }

  // Listen for changes in all fields
  formInputs.forEach(input => {
    input.addEventListener("input", checkForChanges);
    input.addEventListener("change", checkForChanges);
  });

  profileForm.addEventListener("submit", function (event) {
    event.preventDefault();

    if (!isChanged) {
      return; 
    }

    let formData = new FormData(profileForm);

    btnText.innerText = "Updating....";
    spinner.classList.value = "block";
    updateBtn.disabled = true; 

    fetch(profileForm.action, {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          if (data.profile_img_url && profileImage) {
            profileImage.src = data.profile_img_url;
          }
          notyf.success("Profile updated successfully!");
        } else {
          console.error("Error updating profile!", data.errors);
          notyf.error("Error updating profile!");
        }
      })
      .catch((error) => {
        console.error("Fetch error:", error);
        notyf.error("Something went wrong!");
      })
      .finally(() => {
        btnText.innerText = "Update Profile";
        spinner.classList.value = "hidden";
        updateBtn.disabled = true; 
        isChanged = false;
      });
  });
});
