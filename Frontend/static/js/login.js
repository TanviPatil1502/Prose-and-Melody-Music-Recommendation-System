async function validateLogin() {
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let errorMessage = document.getElementById("error-message");
    
    // Check if fields are empty
    if (!email || !password) {
        errorMessage.textContent = "Please enter both email and password.";
        return;
    }

    try {
        console.log("added")
        const response = await fetch("/Enter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Login successful!");
            window.location.href = "/mainpg"; 
        } else {
            errorMessage.textContent = data.message || "Invalid login credentials!";
        }
    } catch (error) {
        errorMessage.textContent = "Server error. Please try again later.";
    }
}
