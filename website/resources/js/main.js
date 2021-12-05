var on_loaded_calls = []

function on_window_loaded(){
    for (i in on_loaded_calls){
        on_loaded_calls[i]()
    }
}

window.addEventListener("load", on_window_loaded, true)