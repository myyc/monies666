function startoverlay() {
    $("body").prepend("<div id='loadoverlay'><h1><blink>LOADING</blink></h1></div>").promise().done(function () {
        var ov = $("#loadoverlay");
        ov.css({position: "absolute", height: "100%", width: "100%", "background-color": "#1a1a1a"});
        ov.find("h1").css({
            "text-align": "center",
            "font-size": "200pt",
            "margin-top": (0.5 * $(window).height() - 200) + "px",
            color: "#cc8225"
        });
    });
}

function stopoverlay() {
    $("#loadoverlay").css({display: "none"});
}
