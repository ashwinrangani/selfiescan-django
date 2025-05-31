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
    const brandingTypeLogo = document.getElementById("brandingTypeLogo");
    const brandingTypeText = document.getElementById("brandingTypeText");
    const startBrandingBtn = document.getElementById("start-branding-btn");
    const downloadToggle = document.getElementById('download-toggle')
    let notyf = new Notyf({ duration: 5000 });

    // Enable or disable branding
brandingSwitch.addEventListener("change", () => {
  if (brandingSwitch.checked) {
    // Ensure logo is selected by default when enabling branding
    brandingTypeLogo.checked = true;
    brandingTypeText.disabled = false;
    brandingTypeLogo.disabled = false;
    toggleBrandingInputs(); // Sync input states based on selected radio button
    
  } else {
    studioNameInput.value = "";
    studioNameInput.disabled = true;
    brandingImageInput.value = "";
    brandingImageInput.disabled = true;
    brandingTypeText.disabled = true;
    brandingTypeLogo.disabled = true;
    preview.src = "";
    preview.classList.add("hidden");
    removeBtn.classList.add("hidden");
    
  }
});

// Selection of branding type, logo or text
function toggleBrandingInputs() {
  if (brandingTypeLogo.checked) {
    studioNameInput.disabled = true;
    studioNameInput.value = "";
    brandingImageInput.disabled = false;
  } else if (brandingTypeText.checked) {
    studioNameInput.disabled = false;
    brandingImageInput.disabled = true;
    brandingImageInput.value = "";
    preview.src = "";
    
  }
}

// Initialize input states based on current event data
function initializeBrandingInputs() {
  if (brandingSwitch.checked) {
    brandingTypeText.disabled = false;
    brandingTypeLogo.disabled = false;
    toggleBrandingInputs(); // Set input states based on selected radio button
  } else {
    studioNameInput.disabled = true;
    brandingImageInput.disabled = true;
    brandingTypeText.disabled = true;
    brandingTypeLogo.disabled = true;
    preview.classList.add("hidden");
    removeBtn.classList.add("hidden");
  }
}

// Run initialization
initializeBrandingInputs();

// Add event listeners for radio buttons
brandingTypeLogo.addEventListener("change", toggleBrandingInputs);
brandingTypeText.addEventListener("change", toggleBrandingInputs);

// Start branding
startBrandingBtn.addEventListener("click", () => {
  startBrandingBtn.disabled = true;

  fetch(`/event/${eventId}/start-branding/`, {
      method: "POST",
      headers: {
          "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
      },
  })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              notyf.success(data.message);
              startBrandingBtn.disabled = false;
          } else {
              notyf.error(data.message || "Failed to start branding.");
              startBrandingBtn.disabled = false;
          }
      })
      .catch(error => {
          console.error("Error starting branding:", error);
          notyf.error("Error starting branding.");
          startBrandingBtn.disabled = false;
      });
});

  brandingForm.addEventListener("submit", function (e) {
  e.preventDefault();  
  const formData = new FormData(brandingForm);
  formData.set("branding_enabled", brandingSwitch.checked);
  formData.set("branding_type", brandingTypeLogo.checked? "logo" : "text");

  if (brandingTypeLogo.checked && brandingImageInput.files.length > 0) {
    formData.append("branding_image", brandingImageInput.files[0]);
  } else if(brandingTypeText.checked){
    formData.set("branding_text", studioNameInput.value)
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
      // Update preview and remove button visibility
      if (data.logo_url && data.logo_url !== "") {            
        preview.src = data.logo_url;
        preview.classList.remove("hidden");
        removeBtn.classList.remove("hidden");
        brandingImageInput.value = "";
        brandingTypeLogo.checked = true;
      } else {
        preview.src = "";
        preview.classList.add("hidden");
        removeBtn.classList.add("hidden");
        brandingTypeText.checked = true;// Hide remove button if no logo
      }
      toggleBrandingInputs();
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
      removeBtn.classList.add("hidden");
      // Update radio based on branding_text
      brandingTypeText.checked = data.branding_text ? true : false;
      brandingTypeLogo.checked = !data.branding_text;
      toggleBrandingInputs(); // Sync input states
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

//Handle download toggle
downloadToggle.addEventListener('change', function(){
  const eventId = this.getAttribute('data-event-id');
  
  const is_downloadable = this.checked;
  console.log(is_downloadable)
  fetch(`/events/${eventId}/toggle-download/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      "X-CSRFToken": document.querySelector("input[name='csrfmiddlewaretoken']").value,
      'X-requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({ is_downloadable: is_downloadable})
  })
  .then(response => response.json())
  .then(data => {
    if (data.success){
      notyf.success(data.message)
    } else {
      notyf.error(data.message);
      this.checked = !isDonloadable
    }
  })
  .catch(error => {
    notyf.error('An error occured while updating the download setting.');
    this.checked = !isDonloadable
  })
})
  
// photo grid of the event photos
  function initLightGallery() {
  const lightGalleryElement = document.getElementById('lightgallery');
  if (lightGalleryElement) {
    lightGallery(lightGalleryElement, {
      plugins: [lgZoom,lgFullscreen],
      selector: 'a',
      speed: 400,
      licenseKey: '0000-0000-000-0000',
      download: true,
      numberOfSlideItemsInDom: 12,

      mobileSettings: {
      controls: true,
      showCloseIcon: true,
      download: true,
      closeOnTap: false,
      },
    });
  }
}
initLightGallery()
  if (!photoGrid || !paginationControls) {
    console.error("Error: photo-grid or pagination-controls not found!");
    return;
  }

  if (showPhotos) {
    showPhotos.addEventListener('click', () => {
      photoGrid.style.display = 'block';
      paginationControls.style.display = 'block';
      
    });
  }

  paginationControls.addEventListener("click", (e) => {
    if (e.target.classList.contains("page-link")) {
      const page = e.target.getAttribute("data-page");
      loadingState.style.display = "block";

      fetch(`/event/${eventId}/photos/?page=${page}`)
        .then((response) => {
          if (!response.ok) throw new Error(`Failed to load page ${page}`);
          return response.json();
        })
        .then((data) => {
          loadingState.style.display = "none";

          if (data.html && data.pagination_html) {
            photoGrid.innerHTML = data.html;
            paginationControls.innerHTML = data.pagination_html;
            initLightGallery()
            window.scrollTo({ top: photoGrid.offsetTop - 100, behavior: "smooth" });
          } else {
            console.error("Error: Incomplete data received", data);
          }
        })
        .catch((error) => console.error("Error loading photos:", error));
    }
  });
});
