function validateLogin() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const errorMsg = document.getElementById("error-msg");

  if (username === "" || password === "") {
      errorMsg.textContent = "Please fill in all fields.";
      return false;
  }

  // Example dummy check (replace with real login logic)
  if (username === "admin" && password === "1234") {
      // ✅ Redirect to another page (e.g., dashboard.html)
      window.location.href = "/dashboard/";  // Change this to your desired page
      return false; // prevent actual form submission since we're redirecting
  } else {
      errorMsg.textContent = "Invalid username or password.";
      return false;
  }
}
