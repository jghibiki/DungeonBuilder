"use strict";

var stage;
var queue;
var cursed = {
    constants: {
        font_size: 14 ,
        font_width_offset: -5
    },
    state: {
        handling: false,
        username: "",
        password: ""
    }
};

function load(){
    queue = new createjs.LoadQueue(false);
    queue.addEventListener("complete", init);
    queue.loadManifest([
        {id: "jquery", src:"./third_party/jquery-3.1.1.min.js"},
        {id: "features", src: "./features.js"},
        {id: "colors", src: "./colors.js"},
        {id: "grid", src: "./grid.js"},
        {id: "command_window", src: "./command_window.js"},
        {id: "text_box", src: "./text_box.js"},
        {id: "colon_line", src: "./colon_line.js"},
        {id: "status_line", src: "./status_line.js"},
        {id: "client", src: "./client.js"},
        {id: "viewer", src: "./viewer.js"}
    ])
}


function init(){


    while(cursed.state.username == ""){
        cursed.state.username = window.prompt("Please enter a username.", "");
    }
    while(cursed.state.password == ""){
        cursed.state.password = window.prompt("Please enter a username.", "");
    }
    

    set_canvas_size();
    stage = new createjs.Stage("canvas");
    build_namespace();
    init_modules();

    cursed.viewer.draw();
    cursed.command_window.draw();
    cursed.text_box.draw();
    cursed.colon_line.draw();
    cursed.status_line.draw();

    document.onkeydown = handleKeypress;

}

function set_canvas_size(){
    var canvas = document.getElementById("canvas");
    var w = window.innerWidth;
    var h = window.innerHeight;

    canvas.width = w;
    canvas.height = h;

    cursed.constants.grid_width = Math.floor(window.innerWidth/(cursed.constants.font_size + cursed.constants.font_width_offset));

    cursed.constants.grid_height = Math.floor(window.innerHeight/cursed.constants.font_size);

    cursed.constants.width = window.innerWidth;
    cursed.constants.height = window.innerHeight;

    canvas.style.visibility = "visible";
}

function test(){
    var circle = new createjs.Shape();
    circle.graphics.beginFill("Yellow").drawCircle(0, 0, 50);
    circle.x = 200;
    circle.y = 200;

    stage.addChild(circle);
    stage.update();
}

function build_namespace() {
    cursed.stage = stage;
    cursed.features = features;
    cursed.colors = colors;
    cursed.grid = grid;
    cursed.viewer = viewer;
    cursed.command_window = command_window;
    cursed.text_box = text_box; 
    cursed.colon_line = colon_line;
    cursed.status_line = status_line;
    cursed.client = client;
}

function init_modules(){
    cursed.features.init(); //must be first
    cursed.grid.init(); //must be second

    cursed.viewer.init(); 
    cursed.command_window.init();
    cursed.text_box.init();
    cursed.colon_line.init();
    cursed.status_line.init();

    cursed.client.init();

}

function handleKeypress(e){
    if(!cursed.state.handling){
        cursed.state.handling = true;
        setTimeout(()=>{cursed.state.handling = false;}, 100);
        console.log(e);
        cursed.viewer.handle(e);
    }
}




