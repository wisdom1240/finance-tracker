// main.js — Finance Tracker
// Minimal JS for mobile nav toggle and dynamic form helpers.

document.addEventListener("DOMContentLoaded", function () {
    // ---- Mobile nav toggle ----
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");
    if (toggle && links) {
        toggle.addEventListener("click", function () {
            links.classList.toggle("open");
        });
    }

    // ---- Dynamic category loading on the transaction form ----
    var typeInputs = document.querySelectorAll('input[name="type"]');
    var categorySelect = document.getElementById("category_id");

    if (typeInputs.length && categorySelect) {
        var allCategories = Array.from(categorySelect.querySelectorAll("option"))
            .filter(function (o) { return o.value !== ""; });

        function filterCategories() {
            var selectedType = document.querySelector('input[name="type"]:checked');
            if (!selectedType) { return; }
            var t = selectedType.value;

            var current = categorySelect.value;
            categorySelect.innerHTML = '<option value="">Select a category…</option>';

            allCategories.forEach(function (opt) {
                if (opt.dataset.type === t) {
                    var clone = opt.cloneNode(true);
                    if (clone.value === current) { clone.selected = true; }
                    categorySelect.appendChild(clone);
                }
            });
        }

        typeInputs.forEach(function (input) {
            input.addEventListener("change", filterCategories);
        });
        filterCategories();
    }
});

// ---- Confirm delete forms ----
document.querySelectorAll("form.delete-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
        var msg = form.dataset.confirm || "Are you sure?";
        if (!window.confirm(msg)) {
            e.preventDefault();
        }
    });
});