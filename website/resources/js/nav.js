{
    function setup_navbar() {
        var navbar = document.getElementsByTagName("nav")[0]
        var m_navbar = document.querySelector(".navbar_menu")

        var last_width = window.innerWidth
        var nav_links = document.getElementsByClassName("navbar_link")
        var navbar_logo = document.querySelector(".navbar_logo")
        var hamburger = document.querySelector("button.hamburger")
        var root = document.documentElement
        var wrapper = document.querySelector(".wrapper")

        window.onresize = function () {
            if (window.innerWidth < 869) {
                if (!last_width || last_width >= 869) {
                    for (let i = 0; i < nav_links.length; i++) {
                        nav_links[i].classList.toggle("inactive", true)
                    }
                    navbar_logo.style["min-width"] = "200px";
                    navbar_logo.style["width"] = "200px";

                    navbar.style.height = "64px"

                    m_navbar.classList.toggle("inactive", false)
                    
                    hamburger.classList.toggle("inactive", false)
                }
            } else {
                if (!last_width || last_width < 869) {
                    for (let i = 0; i < nav_links.length; i++) {
                        nav_links[i].classList.toggle("inactive", false)
                    }
                    navbar_logo.style = ""
                    navbar.style.height = "80px"

                    m_navbar.classList.toggle("inactive", true)

                    hamburger.classList.toggle("inactive", true)
                    hamburger.classList.toggle("is-active", false)
                    root.style.setProperty('--navbar-menu-x', '-100%')
                }

            }
            last_width = window.innerWidth
        }

        last_width = false
        window.onresize()


        hamburger.addEventListener("click", () => {
            hamburger.classList.toggle("is-active")
            root.style.setProperty('--navbar-menu-x', hamburger.classList.contains('is-active') ? '0' : '-100%')
        })
    }

    on_loaded_calls.push(setup_navbar)
}