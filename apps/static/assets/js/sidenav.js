document.addEventListener("DOMContentLoaded", function () {
    // Get the current path from the URL
    const currentPath = window.location.pathname;

    // Get the <ul> element by its ID
    const navList = document.getElementById("principalNavList");

    // Loop through each <a> element inside the <ul>
    const navLinks = navList.getElementsByTagName("a");

    for (let i = 0; i < navLinks.length; i++) {
        const link = navLinks[i];

        // Check if the link's href matches the current path
        if (link.getAttribute("href") === currentPath) {
            // Add the 'active' class to the matching link
            link.classList.add("active");
        }
    }
});

document.addEventListener("DOMContentLoaded", function () {
    // Get the current path from the URL
    const currentPath = window.location.pathname;

    // Get the <ul> element by its ID
    const navList = document.getElementById("bottomNavList");

    // Loop through each <a> element inside the <ul>
    const navLinks = navList.getElementsByTagName("a");
    for (let i = 0; i < navLinks.length; i++) {
        const link = navLinks[i];

        // Check if the link's href matches the current path
        if (link.getAttribute("href") === currentPath) {
            // Add the 'active' class to the matching link
            link.classList.add("active");
        }
    }
});
