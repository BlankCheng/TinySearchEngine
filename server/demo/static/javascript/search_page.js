function parse_query_string(query) {
  var vars = query.split("&");
  var query_string = {};
  for (var i = 0; i < vars.length; i++) {
    var pair = vars[i].split("=");
    var key = decodeURIComponent(pair.shift());
    var value = decodeURIComponent(pair.join("="));
    // If first entry with this name
    if (typeof query_string[key] === "undefined") {
      query_string[key] = value;
      // If second entry with this name
    } else if (typeof query_string[key] === "string") {
      var arr = [query_string[key], value];
      query_string[key] = arr;
      // If third or later entry with this name
    } else {
      query_string[key].push(value);
    }
  }
  return query_string;
}

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

function redirect(query, method, page=1){
    window.location.href = "/search?q=" + query + "&m=" + method + "&p=" + page.toString();
}

function get_method(){
    return document.getElementById("method-text").innerText;
}

function set_method(m){
    document.getElementById("method-text").innerText = m;
}

function next_page(){
    params = parse_query_string(window.location.search.substring(1));
    redirect(params.q, params.m, eval(params.p) + 1);
}

function previous_page(){
    params = parse_query_string(window.location.search.substring(1));
    redirect(params.q, params.m, eval(params.p) - 1);
}