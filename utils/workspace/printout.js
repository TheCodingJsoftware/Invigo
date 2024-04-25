
window.addEventListener("beforeprint", function () {
    adjustTableOffsets();
});

window.addEventListener("afterprint", function () {
    // Code to reset table offsets after print preview
    resetTableOffsets();
});
function adjustTableOffsets() {
    var checkboxCoverPageLabel = document.getElementById("showCoverPageLabel");
    var checkboxCoverPage = document.getElementById("showCoverPage");
    var cover_page_div = document.getElementById("cover-page");
    if (checkboxCoverPage.checked) {
        cover_page_div.style.display = "block";
    } else {
        cover_page_div.style.display = "none";
    }
    checkboxCoverPageLabel.style.display = "none";

    const detailsElement = document.getElementById("assemblies-toggle");
    if (detailsElement.open) {
        detailsElement.style.display = "block";
    } else {
        detailsElement.style.display = "none";
    }
}
function resetTableOffsets() {
    const detailsElement = document.getElementById("assemblies-toggle");
    detailsElement.style.display = "block";
    var checkboxCoverPageLabel = document.getElementById("showCoverPageLabel");
    var cover_page_div = document.getElementById("cover-page");
    cover_page_div.style.display = "block";
    checkboxCoverPageLabel.style.display = "block";
}
