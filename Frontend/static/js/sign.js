async function validateSignup() {
    let fullname = document.getElementById("fullname").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let confirmPassword = document.getElementById("confirm-password").value;
    let errorMessage = document.getElementById("error-message");

    // Check if passwords match
    if (password !== confirmPassword) {
        errorMessage.style.display = "block";
        return;
    } else {
        errorMessage.style.display = "none";
    }

    // Create user data object
    let userData = {
        name: fullname,
        email: email,
        password: password
    };

    try {
        let response = await fetch("/newUser", { // Flask API URL
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(userData)
        });

        let result = await response.json();

        if (response.ok) {
            alert(result.message);
            window.location.href = "/login"; 
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Something went wrong. Please try again later.");
    }
}