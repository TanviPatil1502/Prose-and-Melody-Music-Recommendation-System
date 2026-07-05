document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        let authButtons = document.querySelector(".auth-buttons");
        authButtons.style.opacity = "1";
        authButtons.style.transform = "translateX(0)"; 
        authButtons.style.transition = "transform 1.5s ease-out, opacity 1.5s ease-out";
    }, 2500);
});