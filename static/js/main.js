// main.js — Finance Tracker
// Mobile nav, dynamic form helpers, Chart.js rendering, and mobile polish.

document.addEventListener("DOMContentLoaded", function () {

    // ---- Mobile nav toggle ----
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");

    if (toggle && links) {
        toggle.addEventListener("click", function () {
            var isOpen = links.classList.toggle("open");
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });

        // Auto-close the menu when a link is tapped
        links.querySelectorAll("a").forEach(function (a) {
            a.addEventListener("click", function () {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            });
        });

        // Close the menu if the viewport grows past mobile (avoid stuck-open state)
        window.addEventListener("resize", function () {
            if (window.innerWidth > 768) {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // ---- Dynamic category loading on transaction forms ----
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

    // ---- Confirm delete forms ----
    document.querySelectorAll("form.delete-form").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            var msg = form.dataset.confirm || "Are you sure?";
            if (!window.confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // ---- Chart.js: Dashboard ----
    var dashEl = document.getElementById("dashboard-chart-data");
    if (dashEl && window.Chart) {
        var data = JSON.parse(dashEl.textContent);

        var palette = [
            "#4F46E5", "#10B981", "#EF4444", "#F59E0B",
            "#6366F1", "#8B5CF6", "#06B6D4", "#EC4899",
            "#84CC16", "#F97316"
        ];

        var catCanvas = document.getElementById("categoryChart");
        if (catCanvas && data.category_labels && data.category_labels.length) {
            new Chart(catCanvas, {
                type: "doughnut",
                data: {
                    labels: data.category_labels,
                    datasets: [{
                        data: data.category_values,
                        backgroundColor: palette.slice(0, data.category_labels.length),
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                font: { family: "Inter", size: 12 },
                                padding: 12,
                                usePointStyle: true,
                            },
                        },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    var v = ctx.parsed || 0;
                                    var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                                    var pct = total > 0 ? ((v / total) * 100).toFixed(1) : "0.0";
                                    return ctx.label + ": ₦" + v.toLocaleString() + " (" + pct + "%)";
                                },
                            },
                        },
                    },
                },
            });
        }

        var monthlyCanvas = document.getElementById("monthlyChart");
        if (monthlyCanvas) {
            new Chart(monthlyCanvas, {
                type: "bar",
                data: {
                    labels: data.monthly_labels,
                    datasets: [
                        {
                            label: "Income",
                            data: data.monthly_income,
                            backgroundColor: "#10B981",
                            borderRadius: 6,
                        },
                        {
                            label: "Expenses",
                            data: data.monthly_expense,
                            backgroundColor: "#EF4444",
                            borderRadius: 6,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                font: { family: "Inter", size: 12 },
                                usePointStyle: true,
                            },
                        },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    return ctx.dataset.label + ": ₦" + (ctx.parsed.y || 0).toLocaleString();
                                },
                            },
                        },
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { family: "Inter" } } },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: { family: "Inter" },
                                callback: function (v) { return "₦" + v.toLocaleString(); },
                            },
                        },
                    },
                },
            });
        }
    }

    // ---- Chart.js: Reports ----
    var reportEl = document.getElementById("report-chart-data");
    if (reportEl && window.Chart) {
        var rdata = JSON.parse(reportEl.textContent);

        var palette = [
            "#4F46E5", "#10B981", "#EF4444", "#F59E0B",
            "#6366F1", "#8B5CF6", "#06B6D4", "#EC4899",
            "#84CC16", "#F97316"
        ];

        var reportCatCanvas = document.getElementById("reportCategoryChart");
        if (reportCatCanvas && rdata.category_labels && rdata.category_labels.length) {
            new Chart(reportCatCanvas, {
                type: "doughnut",
                data: {
                    labels: rdata.category_labels,
                    datasets: [{
                        data: rdata.category_values,
                        backgroundColor: palette.slice(0, rdata.category_labels.length),
                        borderWidth: 0,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: {
                                font: { family: "Inter", size: 12 },
                                padding: 12,
                                usePointStyle: true,
                            },
                        },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    var v = ctx.parsed || 0;
                                    var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                                    var pct = total > 0 ? ((v / total) * 100).toFixed(1) : "0.0";
                                    return ctx.label + ": ₦" + v.toLocaleString() + " (" + pct + "%)";
                                },
                            },
                        },
                    },
                },
            });
        }

        var trendCanvas = document.getElementById("trendChart");
        if (trendCanvas && rdata.trend_labels && rdata.trend_labels.length) {
            new Chart(trendCanvas, {
                type: "line",
                data: {
                    labels: rdata.trend_labels,
                    datasets: [{
                        label: "Daily Expenses",
                        data: rdata.trend_values,
                        borderColor: "#4F46E5",
                        backgroundColor: "rgba(79, 70, 229, 0.12)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointBackgroundColor: "#4F46E5",
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    return "₦" + (ctx.parsed.y || 0).toLocaleString();
                                },
                            },
                        },
                    },
                    scales: {
                        x: { grid: { display: false }, ticks: { font: { family: "Inter" } } },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: { family: "Inter" },
                                callback: function (v) { return "₦" + v.toLocaleString(); },
                            },
                        },
                    },
                },
            });
        }
    }
});