$(document).ready(function () {
    $('.dropdown a.toggle-one').on("click", function (e) {
        $(this).next('ul').toggle();
        e.stopPropagation();
        e.preventDefault();
    });
});