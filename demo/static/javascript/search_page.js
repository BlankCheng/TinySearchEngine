function search(obj){
    var container = $(obj).closest('.search-wrapper');
    var input = container.find('.input');
    var input_val = input.val();
    if (input_val.length !== 0) {
        redirect(input_val, get_method());
    }
}

function submit(obj, event){
    var container = $(obj).closest('.search-wrapper');
    var input = container.find('.input');
    var input_val = input.val();
    if (event.key === "Enter") {
        redirect(input_val, get_method());
    }
}

function setting(obj, event){
    var menu = document.getElementById("method-menu");
    if (!menu.classList.contains("active")) {
        $(menu).addClass("active");
    }
    else {
        $(menu).removeClass("active");
    }
}

function choose_method(obj, event){
    var m = $(obj).html();
    set_method(m);
    console.log("choose method:", m);
    var menu = document.getElementById("method-menu");
    $(menu).removeClass("active");
    $(".method-selected").text(m);
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