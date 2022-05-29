function search(obj){
    var container = $(obj).closest('.search-wrapper');
    if(!container.hasClass('active')){
        container.addClass('active');
        // evt.preventDefault();
    }
    else {
        var input = container.find('.search-input');
        var input_val = input.val();
        if (input_val.length !== 0) {
            redirect(input_val, get_method());
        }
    }
}

function cancel(obj){
    var container = $(obj).closest('.search-wrapper');
    if (container.hasClass('active')){
        var input = container.find('.search-input');
        var input_val = input.val();
        if (input_val.length === 0){
            var menu = document.getElementById("method-menu");
            if (menu.classList.contains("show")) {
                menu.classList.toggle("show");
            }
            container.removeClass('active');
        }
        // clear input
        console.log("Delete the search box:", input_val, input_val.length);
        input.val('');
    }
}

function submit(obj, event){
    var container = $(obj).closest('.search-wrapper');
    var input = container.find('.search-input');
    var input_val = input.val();
    if (event.key === "Enter") {
        redirect(input_val, get_method());
    }
}

function setting(obj, event){
    var menu = document.getElementById("method-menu");
    menu.classList.toggle("show");
}

function choose_method(obj, event){
    var m = $(obj).html();
    set_method(m);
    console.log("choose method:", m);
    var menu = document.getElementById("method-menu");
    menu.classList.toggle("show");
}

function redirect(query, method){
    window.location.href = "/search?q=" + query + "&m=" + method;
}

function get_method(){
    return document.getElementById("method-text").innerText;
}

function set_method(m){
    document.getElementById("method-text").innerText = m;
}