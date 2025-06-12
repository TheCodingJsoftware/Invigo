
window.addEventListener("beforeprint", function () {
    adjustTableOffsets();
});

window.addEventListener("afterprint", function () {
    // Code to reset table offsets after print preview
    resetTableOffsets();
});
function adjustTableOffsets() {
    var headerRows = document.querySelectorAll("thead tr");
    var checkbox = document.getElementById("showTotalCost");
    var checkboxLabel = document.getElementById("showTotalCostLabel");
    var checkboxCoverPageLabel = document.getElementById("showCoverPageLabel");
    var checkboxCoverPage = document.getElementById("showCoverPage");
    var total_cost_div = document.getElementById("total-cost-div");
    var cover_page_div = document.getElementById("cover-page");
    if (checkbox.checked) {
        total_cost_div.style.display = "block";
    } else {
        total_cost_div.style.display = "none";
    }
    if (checkboxCoverPage.checked) {
        cover_page_div.style.display = "block";
    } else {
        cover_page_div.style.display = "none";
    }
    checkbox.style.display = "none";
    checkboxLabel.style.display = "none";
    checkboxCoverPageLabel.style.display = "none";
    for (var i = 0; i < headerRows.length; i++) {
        headerRows[i].style.height = "50px";
    }
    const detailsElement = document.getElementById("sheets-toggle");
    if (detailsElement.open) {
        detailsElement.style.display = "block";
    } else {
        detailsElement.style.display = "none";
    }
}
function resetTableOffsets() {
    const detailsElement = document.getElementById("sheets-toggle");
    detailsElement.style.display = "block";
    var checkboxLabel = document.getElementById("showTotalCostLabel");
    var checkboxCoverPageLabel = document.getElementById("showCoverPageLabel");
    var total_cost_div = document.getElementById("total-cost-div");
    var cover_page_div = document.getElementById("cover-page");
    total_cost_div.style.display = "block";
    cover_page_div.style.display = "block";
    checkboxLabel.style.display = "block";
    checkboxCoverPageLabel.style.display = "block";
}
function clearImageBorders() {
    window.location.href = "";
    const allImages = document.querySelectorAll('.popup-trigger img');
    allImages.forEach(image => {
        image.style.border = '2px solid transparent';
        image.style.borderRadius = '0';
        image.style.filter = 'sepia(0)';
    });
}
function highlightImage(imageName, imageId) {
    const allImages = document.querySelectorAll('.popup-trigger img');
    allImages.forEach(image => {
        image.style.border = '2px solid transparent';
        image.style.borderRadius = '0';
        image.style.filter = 'sepia(0)';
    });
    window.location.href = "#" + imageName;

    const image = document.getElementById(imageId);
    image.style.border = '2px solid lime';
    image.style.borderRadius = '5px';
    image.style.filter = 'sepia(1)';
}
