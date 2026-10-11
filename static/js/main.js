// main.js — Finance Tracker
// Mobile nav, dynamic form helpers, Chart.js rendering, and UX polish.

document.addEventListener("DOMContentLoaded", function () {

    // ============================================================
    // 1. MOBILE NAV
    // ============================================================
    var toggle = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");

    if (toggle && links) {
        toggle.addEventListener("click", function () {
            var isOpen = links.classList.toggle("open");
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });

        links.querySelectorAll("a").forEach(function (a) {
            a.addEventListener("click", function () {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            });
        });

        window.addEventListener("resize", function () {
            if (window.innerWidth > 768) {
                links.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    }

    // ============================================================
    // 2. STICKY NAV SHADOW ON SCROLL
    // ============================================================
    var header = document.querySelector(".site-header");
    if (header) {
        function updateHeaderShadow() {
            if (window.scrollY > 8) {
                header.classList.add("scrolled");
            } else {
                header.classList.remove("scrolled");
            }
        }
        window.addEventListener("scroll", updateHeaderShadow, { passive: true });
        updateHeaderShadow();
    }

    // ============================================================
    // 3. FLASH MESSAGES — auto-dismiss + click-to-close
    // ============================================================
    document.querySelectorAll(".flash").forEach(function (flash) {
        // Click to close
        flash.style.cursor = "pointer";
        flash.addEventListener("click", function () {
            dismissFlash(flash);
        });

        // Auto-dismiss after 4s for success/info (keep errors/warnings visible)
        var isError = flash.classList.contains("flash-error") ||
                      flash.classList.contains("flash-danger") ||
                      flash.classList.contains("flash-warning");
        if (!isError) {
            setTimeout(function () {
                dismissFlash(flash);
            }, 4000);
        }
    });

    function dismissFlash(el) {
        el.style.transition = "opacity 240ms ease, transform 240ms ease";
        el.style.opacity = "0";
        el.style.transform = "translateY(-6px)";
        setTimeout(function () {
            if (el.parentNode) { el.parentNode.removeChild(el); }
        }, 260);
    }

    // ============================================================
    // 4. AUTO-FOCUS FIRST INPUT ON AUTH PAGES
    // ============================================================
    var authCard = document.querySelector(".auth-card");
    if (authCard) {
        var firstInput = authCard.querySelector("input:not([type=hidden]):not([type=submit])");
        if (firstInput) {
            // Slight delay so the page fade-in doesn't fight focus animation
            setTimeout(function () { firstInput.focus(); }, 120);
        }
    }

    // ============================================================
    // 5. LOADING STATE ON FORM SUBMIT
    // ============================================================
    // Applies to all forms except delete forms (which use confirm dialogs).
    document.querySelectorAll("form").forEach(function (form) {
        if (form.classList.contains("delete-form")) { return; }
        if (form.classList.contains("savings-add-form")) { return; }

        form.addEventListener("submit", function () {
            // Let delete-confirm intercept first if it wants to.
            // We just add a loading state.
            var submitBtn = form.querySelector("button[type=submit]");
            if (!submitBtn) { return; }

            // Avoid double-submit
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = "Saving…";
            submitBtn.style.opacity = "0.7";
            submitBtn.style.cursor = "wait";
        });
    });

    // ============================================================
    // 6. WARN BEFORE LEAVING A FORM WITH UNSAVED DATA
    // ============================================================
    // Only for add/edit forms (they have novalidate + method=POST)
    var dirtyForms = [];
    document.querySelectorAll("form[method=POST]:not(.delete-form):not(.savings-add-form)").forEach(function (form) {
        var initialState = snapshotForm(form);
        var dirty = false;

        function check() {
            var current = snapshotForm(form);
            dirty = current !== initialState;
        }

        form.addEventListener("input", check);
        form.addEventListener("change", check);

        // Clear the flag when submitted
        form.addEventListener("submit", function () {
            dirty = false;
        });

        dirtyForms.push(function () { return dirty; });
    });

    window.addEventListener("beforeunload", function (e) {
        var anyDirty = dirtyForms.some(function (fn) { return fn(); });
        if (anyDirty) {
            e.preventDefault();
            e.returnValue = "";
            return "";
        }
    });

    function snapshotForm(form) {
        var parts = [];
        form.querySelectorAll("input, select, textarea").forEach(function (el) {
            if (el.type === "hidden" || el.name === "csrf_token") { return; }
            if (el.type === "checkbox" || el.type === "radio") {
                if (el.checked) {
                    parts.push(el.name + "=" + el.value);
                }
            } else {
                parts.push(el.name + "=" + el.value);
            }
        });
        return parts.join("|");
    }

    // ============================================================
    // 7. CONFIRM DELETE FORMS
    // ============================================================
    document.querySelectorAll("form.delete-form").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            var msg = form.dataset.confirm || "Are you sure?";
            if (!window.confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // ============================================================
    // 8. DYNAMIC CATEGORY LOADING ON TRANSACTION FORMS
    // ============================================================
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

    // ============================================================
    // 9. CHART.JS: DASHBOARD
    // ============================================================
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

    // ============================================================
    // 10. CHART.JS: REPORTS
    // ============================================================
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

// ============================================================
// 33. MICRO-INTERACTIONS
// ============================================================

// ---- Staggered fade-in for cards, metrics, table rows ----
document.addEventListener("DOMContentLoaded", function () {
    var staggerTargets = document.querySelectorAll(
        ".metric, .card, .chart-card, .savings-card, .flash, tbody tr"
    );

    staggerTargets.forEach(function (el, i) {
        // Skip elements that are already visible in the first viewport (avoid jank)
        el.style.opacity = "0";
        el.style.transform = "translateY(6px)";
        el.style.transition = "opacity 300ms ease, transform 300ms ease";

        // Stagger in intervals of 40ms, capped so it never feels slow
        var delay = Math.min(i * 40, 600);

        setTimeout(function () {
            el.style.opacity = "1";
            el.style.transform = "translateY(0)";
        }, delay);
    });
});

// ---- Smooth scroll-to-top on route change ----
// When a new page loads, if the previous URL was different, scroll to top.
(function () {
    var lastPath = sessionStorage.getItem("lastPath") || "";
    var currentPath = window.location.pathname + window.location.search;

    if (lastPath && lastPath !== currentPath) {
        // New page loaded — scroll to top smoothly (or instantly on first load)
        window.scrollTo({ top: 0, behavior: "instant" });
    }

    sessionStorage.setItem("lastPath", currentPath);
})();

// ---- Smooth anchor scroll (for any in-page links) ----
document.addEventListener("click", function (e) {
    var link = e.target.closest('a[href^="#"]');
    if (!link) { return; }
    var href = link.getAttribute("href");
    if (href.length <= 1) { return; }
    var target = document.querySelector(href);
    if (!target) { return; }
    e.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
});

// ---- Chart placeholder shimmer removal ----
// The Chart.js charts render into <canvas>. We add a class to the parent
// that shows a shimmer, then remove it when Chart is ready.
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".chart-container").forEach(function (el) {
        el.classList.add("chart-loading");
        // Chart.js is loaded with `defer`, so it'll be ready shortly.
        // Give it up to 800ms to initialize.
        var attempts = 0;
        var check = setInterval(function () {
            attempts++;
            if (window.Chart || attempts > 40) {
                clearInterval(check);
                el.classList.remove("chart-loading");
            }
        }, 20);
    });
});