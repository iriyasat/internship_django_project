// Initialize theme before parsing body to prevent FOUC (flash of unstyled content)
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark-theme");
}
