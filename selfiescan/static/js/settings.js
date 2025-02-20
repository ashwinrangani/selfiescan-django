document.addEventListener('DOMContentLoaded', function(){
    const usernameInput = document.getElementById('username')
    const updateUsernameBtn = document.getElementById('updateUsernameBtn')
    const deleteAccountBtn = document.getElementById('deleteAccountBtn')

    var notyf = new Notyf()
    

    updateUsernameBtn.addEventListener('click', function(){
        let newUsername = usernameInput.value.trim();

        if (!newUsername) {
        notyf.error("Username cannot be empty!");
        return;
        }

        fetch("/settings/update-username/", {
            method: "POST",
            body: JSON.stringify({ username: newUsername }),
            headers: {
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                "Content-Type": "application/json"
            }
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                notyf.success(data.message);
            } else {
                notyf.error(data.message); 
            }
        })
        .catch((error) => {
            console.error("Fetch error:", error);
            notyf.error("Something went wrong!");
        });
    });

    deleteAccountBtn.addEventListener('click', function(){
        if(confirm("Are you sure you want to delete your account?")){
            fetch("/settings/delete-account/", {
                method: "POST",
                headers: {
                   "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.success){
                    notyf.success("Account deleted. Redirecting...")
                    setTimeout(() => { window.location.href="/"}, 2000);
                } else {
                    notyf.error("Error deleting account")
                }
            })
        }
    })
})