document.addEventListener("DOMContentLoaded", () => {
    
    const photoGrid = document.getElementById("photo-grid");
    const paginationControls = document.getElementById("pagination-controls");
    const loadingState = document.querySelector('.loading');
    const showPhotos = document.getElementById("show-photo")
    const studioNameInput = document.getElementById("studioNameInput")
    const brandingForm = document.getElementById("branding-form")
    const brandingSwitch = document.getElementById("brandingSwitch");
    const brandingImageInput = document.getElementById("brandingImage");
    const eventSection = document.getElementById("event-section");
    const eventId = eventSection.dataset.eventId; //data-event-id converts to eventId camelcase in js 
    const preview = document.getElementById("branding-logo-preview");
    const removeBtn = document.getElementById("remove-branding-logo-btn");

    let notyf = new Notyf({ duration: 5000 });

    // enable or disable branding 
    brandingSwitch.addEventListener("change", () => {
      if (brandingSwitch.checked) {
        studioNameInput.disabled = false;
        brandingImageInput.disabled = false
      } else {
        studioNameInput.value = "";
        studioNameInput.disabled = true;
        brandingImageInput.value = "";
        brandingImageInput.disabled = true
      }
    });

    brandingForm.addEventListener("submit", function (e) {
      e.preventDefault();  
      const formData = new FormData(brandingForm);
      formData.set("branding_enabled", brandingSwitch.checked);


      if (brandingImageInput.files.length > 0) {
        formData.append("branding_image", brandingImageInput.files[0]);
      }

      fetch(`/event/${eventId}/branding/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
        },
        body: formData,
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
            // Optional: update preview
            if (data.logo_url) {
            
            preview.src = data.logo_url;
            preview.classList.remove("hidden");
            brandingImageInput.value = "";
                    
          } 
          if (removeBtn) {
            removeBtn.classList.remove("hidden");
           }
          notyf.success("Branding updated successfully!");
        } else {
          notyf.error("Something went wrong while updating branding.");
        }
      })
      .catch(error => {
        console.error("AJAX Branding Error:", error);
        notyf.error("An error occurred.");
      });
    });

  // remove logo
  const removeLogoBtn = document.getElementById("remove-branding-logo-btn");

if (removeLogoBtn) {
  removeLogoBtn.addEventListener("click", function () {
    fetch(`/event/${eventId}/branding/remove-logo/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
      },
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        notyf.success("Branding logo removed!");
        
      
        preview.src = "";
        preview.classList.add("hidden");
    

    
        removeLogoBtn.classList.add("hidden");
    

      } else {
        notyf.error("Failed to remove branding logo.");
      }
    })
    .catch(err => {
      console.error("Error removing logo:", err);
      notyf.error("Something went wrong.");
    });
  });
}

    
// photo grid of the event photos
    if (!photoGrid || !paginationControls) {
      console.error("Error: photo-grid or pagination-controls not found!");
      return;
    }
    if (showPhotos) {
      showPhotos.addEventListener('click', () => {
        photoGrid.style.display = 'block'
        paginationControls.style.display = 'block'
      })

    }


    paginationControls.addEventListener("click", (e) => {
      if (e.target.classList.contains("page-link")) {
        const page = e.target.getAttribute("data-page");
        loadingState.style.display = "block"

        fetch(`/event/${eventId}/photos/?page=${page}`)
          .then((response) => {
            if (!response.ok) throw new Error(`Failed to load page ${page}`);
            return response.json();
          })
          .then((data) => {
            loadingState.style.display = 'none';

            if (data.html && data.pagination_html) {
              photoGrid.innerHTML = data.html;
              paginationControls.innerHTML = data.pagination_html;
              window.scrollTo({ top: photoGrid.offsetTop - 100, behavior: "smooth" });
            } else {
              console.error("Error: Incomplete data received", data);
            }
          })
          .catch((error) => console.error("Error loading photos:", error));
      }
    });
  });

