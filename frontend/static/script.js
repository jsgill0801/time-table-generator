(function () {
    const STORAGE_KEYS = {
        selectedView: "ttg.selectedView",
        generation: "ttg.generation"
    };

    const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    const SIDEBAR_ITEMS = [
        { id: "dashboard", label: "Dashboard", href: "dashboard.html" },
        { id: "courses", label: "Courses", href: "courses.html" },
        { id: "faculty", label: "Faculty", href: "faculty.html" },
        { id: "rooms", label: "Rooms", href: "rooms.html" },
        { id: "batches", label: "Batches", href: "batches.html" },
        { id: "categories", label: "Categories", href: "categories.html" },
        { id: "slots", label: "Slots", href: "slots.html" },
        { id: "timetable", label: "Timetable", href: "timetable.html" }
    ];

    const RESOURCE_SINGULAR_LABELS = {
        courses: "Course",
        faculty: "Faculty",
        rooms: "Classroom",
        batches: "Batch",
        categories: "Category",
        slots: "Slot"
    };

    const COURSE_NUMERIC_FIELD_KEYS = ["lectureHours", "tutorialHours", "labHours", "credits"];

    let resourceModalElements = null;
    let activeResourceModalState = null;
    let confirmationModalElements = null;
    let pendingDeleteState = null;

    const RESOURCE_CONFIGS = {
        courses: {
            title: "Courses",
            description: "Courses used in the timetable.",
            chip: "Course Data",
            tableTitle: "Course List",
            searchPlaceholder: "Search code, course, category, or semester",
            note: "Check names, semesters, and categories before you run.",
            metrics: function (rows) {
                return [
                    { label: "Records", value: rows.length, detail: "Used in the next run." },
                    { label: "Semesters", value: uniqueCount(rows, "semester"), detail: "Covered in this setup." },
                    { label: "Categories", value: uniqueCount(rows, "category"), detail: "Mapped course types." }
                ];
            },
            highlights: [
                { label: "Before run", value: "Check category and semester." },
                { label: "High impact", value: "Labs need tighter slot planning." },
                { label: "Next", value: "Go to Dashboard and run." }
            ],
            columns: [
                { key: "code", label: "Code" },
                { key: "name", label: "Course" },
                { key: "category", label: "Category", badge: "accent" },
                { key: "credits", label: "Credits" },
                { key: "semester", label: "Semester", badge: "secondary" }
            ],
            rows: [
                { code: "ICT201", name: "Data Structures", category: "Core Theory", credits: "4", semester: "Sem 2" },
                { code: "ICT203", name: "Database Systems", category: "Core Theory", credits: "4", semester: "Sem 4" },
                { code: "ICT205", name: "Operating Systems", category: "Core Theory", credits: "4", semester: "Sem 4" },
                { code: "ICT207", name: "Digital Logic Lab", category: "Lab", credits: "2", semester: "Sem 2" },
                { code: "ICT209", name: "Software Engineering", category: "Core Theory", credits: "3", semester: "Sem 6" },
                { code: "ICT211", name: "Machine Learning", category: "Elective", credits: "3", semester: "Sem 6" },
                { code: "ICT213", name: "Network Security", category: "Elective", credits: "3", semester: "Sem 6" },
                { code: "ICT215", name: "Python Programming Lab", category: "Lab", credits: "2", semester: "Sem 4" }
            ]
        },
        faculty: {
            title: "Faculty",
            description: "Faculty available for scheduling.",
            chip: "Faculty Data",
            tableTitle: "Faculty List",
            searchPlaceholder: "Search faculty or load",
            note: "Use faculty email and weekly load only.",
            metrics: function (rows) {
                return [
                    { label: "Faculty", value: rows.length, detail: "In the current roster." }
                ];
            },
            highlights: [],
            columns: [
                { key: "facultyId", label: "Faculty ID" },
                { key: "name", label: "Name" },
                { key: "email", label: "Email" },
                { key: "load", label: "Weekly Load", badge: "secondary" }
            ],
            rows: [
                { facultyId: "FAC-01", name: "Dr. Meera Shah", email: "meera.shah@college.edu", load: "18 hrs" },
                { facultyId: "FAC-02", name: "Prof. Kunal Desai", email: "kunal.desai@college.edu", load: "16 hrs" },
                { facultyId: "FAC-03", name: "Dr. Nidhi Trivedi", email: "nidhi.trivedi@college.edu", load: "12 hrs" },
                { facultyId: "FAC-04", name: "Prof. Aditi Rao", email: "aditi.rao@college.edu", load: "15 hrs" },
                { facultyId: "FAC-05", name: "Dr. Rahul Menon", email: "rahul.menon@college.edu", load: "10 hrs" },
                { facultyId: "FAC-06", name: "Prof. Hiral Patel", email: "hiral.patel@college.edu", load: "11 hrs" },
                { facultyId: "FAC-07", name: "Dr. Sagar Joshi", email: "sagar.joshi@college.edu", load: "13 hrs" },
                { facultyId: "FAC-08", name: "Prof. Neha Vyas", email: "neha.vyas@college.edu", load: "9 hrs" }
            ]
        },
        rooms: {
            title: "Rooms",
            description: "Rooms and capacities used in scheduling.",
            chip: "Room Data",
            tableTitle: "Room List",
            searchPlaceholder: "Search room or capacity",
            note: "List only classrooms and capacities.",
            metrics: function (rows) {
                return [
                    { label: "Rooms", value: rows.length, detail: "Available to schedule." },
                    { label: "Largest Capacity", value: "72", detail: "Seats in the largest room." }
                ];
            },
            highlights: [],
            columns: [
                { key: "room", label: "Room" },
                { key: "capacity", label: "Capacity" }
            ],
            rows: [
                { room: "A-101", capacity: "60" },
                { room: "A-103", capacity: "48" },
                { room: "B-204", capacity: "72" },
                { room: "LAB-201", capacity: "36" },
                { room: "LAB-203", capacity: "32" },
                { room: "C-110", capacity: "40" }
            ]
        },
        batches: {
            title: "Batches",
            description: "Student groups included in the timetable.",
            chip: "Batch Data",
            tableTitle: "Batch List",
            searchPlaceholder: "Search batch, program, section, or semester",
            note: "Batch names, sections, and strength shape the exports.",
            metrics: function (rows) {
                return [
                    { label: "Batches", value: rows.length, detail: "Included this cycle." },
                    { label: "Programs", value: uniqueCount(rows, "program"), detail: "Programs covered." },
                    { label: "Total Strength", value: sumValues(rows, "strength"), detail: "Students in plan." }
                ];
            },
            highlights: [
                { label: "Sections", value: "Keep names consistent." },
                { label: "Capacity", value: "Match strength with rooms." },
                { label: "Exports", value: "Each batch gets its own file." }
            ],
            columns: [
                { key: "batch", label: "Batch" },
                { key: "program", label: "Program" },
                { key: "semester", label: "Semester", badge: "secondary" },
                { key: "section", label: "Section", badge: "accent" },
                { key: "strength", label: "Strength" }
            ],
            rows: [
                { batch: "ICT Sem 2 A", program: "B.Tech ICT", semester: "Sem 2", section: "A", strength: "62" },
                { batch: "ICT Sem 2 B", program: "B.Tech ICT", semester: "Sem 2", section: "B", strength: "58" },
                { batch: "ICT Sem 4 A", program: "B.Tech ICT", semester: "Sem 4", section: "A", strength: "54" },
                { batch: "ICT Sem 4 B", program: "B.Tech ICT", semester: "Sem 4", section: "B", strength: "51" },
                { batch: "ICT Sem 6 A", program: "B.Tech ICT", semester: "Sem 6", section: "A", strength: "47" },
                { batch: "ICT Sem 6 B", program: "B.Tech ICT", semester: "Sem 6", section: "B", strength: "45" }
            ]
        },
        categories: {
            title: "Categories",
            description: "Teaching categories used in scheduling.",
            chip: "Category Rules",
            tableTitle: "Category List",
            searchPlaceholder: "Search category",
            note: "Enter only the category name.",
            metrics: function (rows) {
                return [
                    { label: "Categories", value: rows.length, detail: "Rules in use." }
                ];
            },
            highlights: [],
            columns: [
                { key: "name", label: "Category" }
            ],
            rows: [
                { name: "Core Theory" },
                { name: "Lab" },
                { name: "Elective" },
                { name: "Skill Module" },
                { name: "Professional" }
            ]
        },
        slots: {
            title: "Slots",
            description: "Time windows used by the timetable.",
            chip: "Slot Data",
            tableTitle: "Slot List",
            searchPlaceholder: "Search slot name or time",
            note: "Define time slots with names and day of week.",
            metrics: function (rows) {
                return [
                    { label: "Slots", value: rows.length, detail: "Daily teaching windows." }
                ];
            },
            highlights: [],
            columns: [
                { key: "slotName", label: "Slot Name" },
                { key: "startTime", label: "Start Time" },
                { key: "endTime", label: "End Time" },
                { key: "dayOfWeek", label: "Day of the Week" }
            ],
            rows: [
                { slotName: "Slot-1", startTime: "08:30", endTime: "09:20", dayOfWeek: "Monday" },
                { slotName: "Slot-2", startTime: "09:25", endTime: "10:15", dayOfWeek: "Monday" },
                { slotName: "Slot-3", startTime: "10:30", endTime: "11:20", dayOfWeek: "Monday" },
                { slotName: "Slot-4", startTime: "11:25", endTime: "12:15", dayOfWeek: "Monday" },
                { slotName: "Slot-5", startTime: "13:00", endTime: "13:50", dayOfWeek: "Monday" },
                { slotName: "Slot-6", startTime: "14:00", endTime: "15:50", dayOfWeek: "Monday" },
                { slotName: "Slot-7", startTime: "16:00", endTime: "16:50", dayOfWeek: "Monday" }
            ]
        }
    };

    const MASTER_TIMETABLE_TEMPLATE = [
        { day: "Monday", slot: "08:30 - 09:20", course: "Data Structures", faculty: "Dr. Meera Shah", room: "B-204", batch: "ICT Sem 2 A", category: "Core Theory" },
        { day: "Monday", slot: "09:25 - 10:15", course: "Database Systems", faculty: "Prof. Kunal Desai", room: "A-101", batch: "ICT Sem 4 A", category: "Core Theory" },
        { day: "Monday", slot: "10:30 - 11:20", course: "Software Engineering", faculty: "Prof. Aditi Rao", room: "A-103", batch: "ICT Sem 6 A", category: "Core Theory" },
        { day: "Monday", slot: "14:00 - 15:50", course: "Digital Logic Lab", faculty: "Prof. Kunal Desai", room: "LAB-201", batch: "ICT Sem 2 B", category: "Lab" },
        { day: "Tuesday", slot: "08:30 - 09:20", course: "Operating Systems", faculty: "Dr. Nidhi Trivedi", room: "B-204", batch: "ICT Sem 4 B", category: "Core Theory" },
        { day: "Tuesday", slot: "09:25 - 10:15", course: "Professional Communication", faculty: "Prof. Neha Vyas", room: "C-110", batch: "ICT Sem 2 A", category: "Professional" },
        { day: "Tuesday", slot: "10:30 - 11:20", course: "Machine Learning", faculty: "Dr. Rahul Menon", room: "A-103", batch: "ICT Sem 6 B", category: "Elective" },
        { day: "Tuesday", slot: "14:00 - 15:50", course: "Python Programming Lab", faculty: "Prof. Kunal Desai", room: "LAB-203", batch: "ICT Sem 4 A", category: "Lab" },
        { day: "Wednesday", slot: "08:30 - 09:20", course: "Data Structures", faculty: "Dr. Meera Shah", room: "A-101", batch: "ICT Sem 2 B", category: "Core Theory" },
        { day: "Wednesday", slot: "09:25 - 10:15", course: "Network Security", faculty: "Prof. Hiral Patel", room: "A-103", batch: "ICT Sem 6 A", category: "Elective" },
        { day: "Wednesday", slot: "10:30 - 11:20", course: "Database Systems", faculty: "Prof. Kunal Desai", room: "B-204", batch: "ICT Sem 4 B", category: "Core Theory" },
        { day: "Wednesday", slot: "13:00 - 13:50", course: "Software Engineering", faculty: "Prof. Aditi Rao", room: "A-101", batch: "ICT Sem 6 B", category: "Core Theory" },
        { day: "Thursday", slot: "08:30 - 09:20", course: "Operating Systems", faculty: "Dr. Nidhi Trivedi", room: "A-103", batch: "ICT Sem 4 A", category: "Core Theory" },
        { day: "Thursday", slot: "09:25 - 10:15", course: "Data Structures", faculty: "Dr. Meera Shah", room: "B-204", batch: "ICT Sem 2 A", category: "Core Theory" },
        { day: "Thursday", slot: "14:00 - 15:50", course: "Python Programming Lab", faculty: "Prof. Kunal Desai", room: "LAB-203", batch: "ICT Sem 4 B", category: "Lab" },
        { day: "Friday", slot: "08:30 - 09:20", course: "Machine Learning", faculty: "Dr. Rahul Menon", room: "A-101", batch: "ICT Sem 6 A", category: "Elective" },
        { day: "Friday", slot: "09:25 - 10:15", course: "Professional Communication", faculty: "Prof. Neha Vyas", room: "C-110", batch: "ICT Sem 2 B", category: "Professional" },
        { day: "Friday", slot: "10:30 - 11:20", course: "Network Security", faculty: "Prof. Hiral Patel", room: "A-103", batch: "ICT Sem 6 B", category: "Elective" },
        { day: "Friday", slot: "13:00 - 13:50", course: "Software Engineering", faculty: "Prof. Aditi Rao", room: "B-204", batch: "ICT Sem 6 A", category: "Core Theory" }
    ];

    const TIMETABLE_VIEWS = {
        overall: {
            title: "Overall",
            description: "Combined file for all batches.",
            filename: "overall-timetable.xls"
        },
        faculty: {
            title: "Faculty-wise",
            description: "One file grouped by faculty.",
            filename: "faculty-wise-timetable.xls"
        },
        rooms: {
            title: "Room-wise",
            description: "One file grouped by room.",
            filename: "room-wise-timetable.xls"
        },
        batches: {
            title: "Batch-wise",
            description: "One file grouped by batch.",
            filename: "batch-wise-timetable.xls"
        }
    };

    document.addEventListener("DOMContentLoaded", function () {
        buildSidebar();
        setupAuthForms();
        setupDashboardPage();
        renderResourcePage();
        setupTimetablePage();
    });

    window.logout = handleLogout;

    function buildSidebar() {
        const sidebar = document.querySelector("[data-sidebar]");

        if (!sidebar) {
            return;
        }

        const activePage = document.body.dataset.page || "";
        const navMarkup = SIDEBAR_ITEMS.map(function (item) {
            const isActive = item.id === activePage;
            return (
                '<a class="sidebar-link' +
                (isActive ? " is-active" : "") +
                '" href="' +
                item.href +
                '"' +
                (isActive ? ' aria-current="page"' : "") +
                ">" +
                '<span>' +
                escapeHtml(item.label) +
                "</span>" +
                "<span aria-hidden=\"true\">&rsaquo;</span>" +
                "</a>"
            );
        }).join("");

        sidebar.innerHTML =
            '<div class="sidebar-brand">' +
            "<small>Admin</small>" +
            "<h1>Timetable Generator</h1>" +
            "</div>" +
            '<nav class="sidebar-nav" aria-label="Primary">' +
            navMarkup +
            "</nav>" +
            '<div class="sidebar-footer">' +
            '<p class="sidebar-note">Setup, run, download.</p>' +
            '<button class="logout-button" type="button" data-logout-button>Logout</button>' +
            "</div>";

        const logoutButton = sidebar.querySelector("[data-logout-button]");

        if (logoutButton) {
            logoutButton.addEventListener("click", handleLogout);
        }
    }

    function setupAuthForms() {
        const loginForm = document.getElementById("loginForm");
        const signupForm = document.getElementById("signupForm");

        if (loginForm) {
            loginForm.addEventListener("submit", handleLoginSubmit);
        }

        if (signupForm) {
            signupForm.addEventListener("submit", handleSignupSubmit);
        }
    }

    async function handleLoginSubmit(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const submitButton = form.querySelector('button[type="submit"]');
        const errorBox = document.getElementById("loginError");
        const username = document.getElementById("loginUsername").value.trim();
        const password = document.getElementById("loginPassword").value;

        setError(errorBox, "");
        setButtonBusy(submitButton, true, "Signing in...");

        try {
            const response = await fetch("/api/v1/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await safeJson(response);

            if (!response.ok) {
                setError(errorBox, data.error || "Unable to sign in with the provided credentials.");
                return;
            }

            window.location.href = "dashboard.html";
        } catch (error) {
            setError(errorBox, "Unable to reach the login service right now. Please verify the server is running.");
        } finally {
            setButtonBusy(submitButton, false, "Sign In");
        }
    }

    async function handleSignupSubmit(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const submitButton = form.querySelector('button[type="submit"]');
        const errorBox = document.getElementById("signupError");
        const username = document.getElementById("signupUsername").value.trim();
        const email = document.getElementById("signupEmail").value.trim();
        const password = document.getElementById("signupPassword").value;

        setError(errorBox, "");
        setButtonBusy(submitButton, true, "Creating account...");

        try {
            const response = await fetch("/api/v1/auth/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            const data = await safeJson(response);

            if (!response.ok) {
                setError(errorBox, data.error || "Unable to create the account with the current details.");
                return;
            }

            window.location.href = "login.html";
        } catch (error) {
            setError(errorBox, "Unable to reach the signup service right now. Please verify the server is running.");
        } finally {
            setButtonBusy(submitButton, false, "Create Account");
        }
    }

    function setupDashboardPage() {
        const courseCount = document.getElementById("courseCount");
        const facultyCount = document.getElementById("facultyCount");
        const runButton = document.getElementById("runTimetableButton");

        if (!courseCount || !facultyCount || !runButton) {
            return;
        }

        courseCount.textContent = RESOURCE_CONFIGS.courses.rows.length;
        facultyCount.textContent = RESOURCE_CONFIGS.faculty.rows.length;

        const savedGeneration = getStoredGeneration();

        if (savedGeneration) {
            renderDashboardReport(savedGeneration);
        }

        runButton.addEventListener("click", async function () {
            const status = document.getElementById("runStatus");
            const context = document.getElementById("runContext");

            if (status) {
                status.classList.add("is-visible");
            }

            if (context) {
                context.textContent = "Checking setup data...";
            }

            setButtonBusy(runButton, true, "Running...");

            try {
                await delay(1200);

                const generation = createGenerationPayload();
                storeGeneration(generation);
                renderDashboardReport(generation);

                if (context) {
                    context.textContent = "Run complete. Open Timetable to download.";
                }
            } finally {
                if (status) {
                    status.classList.remove("is-visible");
                }

                setButtonBusy(runButton, false, "Run");
            }
        });
    }

    function renderDashboardReport(generation) {
        const reportPanel = document.getElementById("dashboardReport");

        if (!reportPanel || !generation || !generation.report) {
            return;
        }

        setText("courseClashCount", generation.report.courseClashes);
        setText("facultyClashCount", generation.report.facultyClashes);
        setText("courseClashText", generation.report.courseNote);
        setText("facultyClashText", generation.report.facultyNote);
        setText("lastRunText", "Last generated on " + formatDateTime(generation.generatedAt) + ".");
        setText("generationStatusLabel", "Ready");

        reportPanel.classList.remove("is-hidden");
    }

    function renderResourcePage() {
        const resourcePage = document.body.dataset.resourcePage;

        if (!resourcePage || !RESOURCE_CONFIGS[resourcePage]) {
            return;
        }

        const config = RESOURCE_CONFIGS[resourcePage];
        const searchInput = document.querySelector("[data-resource-search]");

        setText("[data-resource-title]", config.title);
        setText("[data-resource-description]", config.description);
        setText("[data-resource-chip]", config.chip);
        setText("[data-table-title]", config.tableTitle);
        setText("[data-resource-note]", config.note);

        if (searchInput) {
            searchInput.setAttribute("placeholder", config.searchPlaceholder);
        }

        renderMetrics(document.querySelector("[data-resource-metrics]"), config.metrics(config.rows));
        renderHighlights(document.querySelector("[data-resource-highlights]"), config.highlights);
        renderResourceTable(config, getFilteredResourceRows(config, ""));
        setupResourceAddControls(resourcePage, config, searchInput);
        setupResourceTableActions(resourcePage, config, searchInput);

        if (searchInput) {
            searchInput.addEventListener("input", function (event) {
                renderResourceTable(config, getFilteredResourceRows(config, event.target.value));
            });
        }
    }

    function setupResourceAddControls(resourcePage, config, searchInput) {
        const tablePanelHeading = document.querySelector(".content-panel .panel-heading");

        if (!tablePanelHeading || tablePanelHeading.querySelector("[data-resource-add-button]")) {
            return;
        }

        const singularLabel = RESOURCE_SINGULAR_LABELS[resourcePage] || config.title;
        const searchField = searchInput ? searchInput.closest(".search-field") : null;
        const actions = document.createElement("div");
        const addButton = document.createElement("button");

        actions.className = "resource-table-actions";
        actions.dataset.resourceActions = "";

        addButton.type = "button";
        addButton.className = "resource-add-button";
        addButton.dataset.resourceAddButton = resourcePage;
        addButton.textContent = "Add";
        addButton.setAttribute("aria-label", "Add " + singularLabel);
        addButton.addEventListener("click", function () {
            openResourceModal(resourcePage, config, searchInput, addButton, { mode: "add" });
        });

        if (searchField) {
            actions.appendChild(searchField);
        }

        actions.appendChild(addButton);
        tablePanelHeading.appendChild(actions);
    }

    function setupResourceTableActions(resourcePage, config, searchInput) {
        const body = document.querySelector("[data-resource-body]");

        if (!body || body.dataset.rowActionsBound === "true") {
            return;
        }

        body.dataset.rowActionsBound = "true";
        body.addEventListener("click", function (event) {
            const button = event.target.closest("[data-row-action]");

            if (!button) {
                return;
            }

            const rowIndex = Number(button.dataset.rowIndex);

            if (!Number.isInteger(rowIndex) || !config.rows[rowIndex]) {
                return;
            }

            if (button.dataset.rowAction === "edit") {
                openResourceModal(resourcePage, config, searchInput, button, {
                    mode: "edit",
                    rowIndex: rowIndex
                });
            }

            if (button.dataset.rowAction === "delete") {
                openDeleteConfirmationModal(resourcePage, config, searchInput, button, rowIndex);
            }
        });
    }

    function openResourceModal(resourcePage, config, searchInput, triggerButton, options) {
        const schema = getResourceFormSchema(resourcePage, config);
        const modal = ensureResourceModal();
        const modalOptions = options || {};
        const mode = modalOptions.mode === "edit" ? "edit" : "add";
        const rowIndex = Number.isInteger(modalOptions.rowIndex) ? modalOptions.rowIndex : -1;
        const row = mode === "edit" ? config.rows[rowIndex] : null;

        activeResourceModalState = {
            config: config,
            schema: schema,
            searchInput: searchInput,
            triggerButton: triggerButton,
            mode: mode,
            rowIndex: rowIndex
        };

        if (modal.closeTimer) {
            window.clearTimeout(modal.closeTimer);
            modal.closeTimer = null;
        }

        modal.title.textContent = getResourceModalTitle(schema, mode);
        modal.fields.innerHTML = buildResourceFormMarkup(schema);
        modal.submitButton.textContent = mode === "edit" ? "Edit" : "Add";
        modal.form.reset();
        clearResourceFormErrors(modal.form);
        setError(modal.formError, "");
        setupResourceFormInteractions(schema, modal.form);

        if (row) {
            populateResourceForm(schema, modal.form, row);
        }

        bindResourceFormLiveValidation(schema, modal.form, modal.submitButton);
        syncResourceSubmitState(schema, modal.form, modal.submitButton);

        modal.overlay.hidden = false;
        document.body.classList.add("modal-open");

        window.requestAnimationFrame(function () {
            modal.overlay.classList.add("is-open");
        });

        const firstInput = modal.form.querySelector("input:not([type='hidden']), select:not([disabled]), textarea");

        if (firstInput) {
            firstInput.focus();
        } else {
            modal.dialog.focus();
        }
    }

    function ensureResourceModal() {
        if (resourceModalElements) {
            return resourceModalElements;
        }

        const overlay = document.createElement("div");

        overlay.className = "resource-modal-overlay";
        overlay.dataset.resourceModal = "";
        overlay.hidden = true;
        overlay.innerHTML =
            '<div class="resource-modal" role="dialog" aria-modal="true" aria-labelledby="resourceModalTitle" tabindex="-1">' +
            '<div class="resource-modal-header">' +
            '<h2 id="resourceModalTitle"></h2>' +
            '<button class="resource-modal-close" type="button" aria-label="Close modal" data-modal-close>&times;</button>' +
            "</div>" +
            '<form class="resource-form" data-resource-form novalidate>' +
            '<div class="resource-form-grid" data-resource-form-fields></div>' +
            '<div class="form-error is-hidden" data-modal-form-error></div>' +
            '<div class="resource-modal-actions">' +
            '<button class="modal-submit-button" type="submit">Add</button>' +
            '<button class="modal-cancel-button" type="button" data-modal-cancel>Cancel</button>' +
            "</div>" +
            "</form>" +
            "</div>";

        document.body.appendChild(overlay);

        resourceModalElements = {
            overlay: overlay,
            dialog: overlay.querySelector(".resource-modal"),
            title: overlay.querySelector("#resourceModalTitle"),
            form: overlay.querySelector("[data-resource-form]"),
            fields: overlay.querySelector("[data-resource-form-fields]"),
            formError: overlay.querySelector("[data-modal-form-error]"),
            submitButton: overlay.querySelector(".modal-submit-button"),
            closeButton: overlay.querySelector("[data-modal-close]"),
            cancelButton: overlay.querySelector("[data-modal-cancel]"),
            closeTimer: null
        };

        resourceModalElements.form.addEventListener("submit", handleResourceFormSubmit);
        resourceModalElements.closeButton.addEventListener("click", closeResourceModal);
        resourceModalElements.cancelButton.addEventListener("click", closeResourceModal);
        overlay.addEventListener("mousedown", function (event) {
            if (event.target === overlay) {
                closeResourceModal();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && activeResourceModalState) {
                closeResourceModal();
            }
        });

        return resourceModalElements;
    }

    function getResourceModalTitle(schema, mode) {
        if (mode !== "edit") {
            return schema.title;
        }

        return schema.title.replace(/^Add\s+/, "Edit ");
    }

    function getResourceFormSchema(resourcePage, config) {
        if (resourcePage === "courses") {
            return {
                id: "courses",
                title: "Add Course",
                fields: [
                    { key: "code", label: "Course Code", type: "text", required: true },
                    { key: "name", label: "Course Name", type: "text", required: true },
                    { key: "lectureHours", label: "Number of Lecture Hours", type: "text", inputMode: "decimal", required: true, numeric: true },
                    { key: "tutorialHours", label: "Tutorial Hours", type: "text", inputMode: "decimal", required: true, numeric: true },
                    { key: "labHours", label: "Lab Hours", type: "text", inputMode: "decimal", required: true, numeric: true },
                    { key: "credits", label: "Credits", type: "text", inputMode: "decimal", required: true, numeric: true },
                    { key: "batchCategories", label: "Batches", type: "batch-category-selector", required: true },
                    { key: "faculty", label: "Faculty", type: "select", source: "faculty", optionValue: "name", optionLabel: "name", required: true },
                ],
                toRow: createCourseResourceRow
            };
        }

        if (resourcePage === "faculty") {
            return {
                id: "faculty",
                title: "Add Faculty",
                fields: [
                    { key: "facultyCode", label: "Faculty Code", type: "text", required: true },
                    { key: "facultyName", label: "Faculty Name", type: "text", required: true },
                    { key: "facultyEmail", label: "Faculty Email", type: "text", required: true },
                    { key: "maximumLoad", label: "Maximum Load", type: "text", inputMode: "decimal", required: true, numeric: true }
                ],
                toRow: createFacultyResourceRow
            };
        }

        if (resourcePage === "rooms") {
            return {
                id: "rooms",
                title: "Add Classroom",
                fields: [
                    { key: "classroomName", label: "Classroom Name", type: "text", required: true },
                    { key: "capacity", label: "Capacity", type: "text", inputMode: "numeric", required: true, numeric: true }
                ],
                toRow: createClassroomResourceRow
            };
        }

        if (resourcePage === "batches") {
            return {
                id: "batches",
                title: "Add Batch",
                fields: [
                    { key: "program", label: "Program", type: "select", options: getUniqueResourceValues("batches", "program"), required: true },
                    { key: "branch", label: "Branch", type: "select", options: getBatchBranchOptions(), required: true },
                    { key: "semester", label: "Semester", type: "select", options: getUniqueResourceValues("batches", "semester"), required: true },
                    { key: "section", label: "Section", type: "select", options: getUniqueResourceValues("batches", "section"), required: true }
                ],
                toRow: createBatchResourceRow
            };
        }

        if (resourcePage === "categories") {
            return {
                id: "categories",
                title: "Add Category",
                fields: [
                    { key: "categoryName", label: "Category Name", type: "text", required: true }
                ],
                toRow: createCategoryResourceRow
            };
        }

        if (resourcePage === "slots") {
            return {
                id: "slots",
                title: "Add Slot",
                fields: [
                    { key: "slotName", label: "Slot Name", type: "text", required: true },
                    { key: "dayOfWeek", label: "Day of the Week", type: "select", options: WEEK_DAYS, required: true },
                    { key: "startTime", label: "Start Time", type: "time", required: true },
                    { key: "endTime", label: "End Time", type: "time", required: true }
                ],
                toRow: createSlotResourceRow
            };
        }

        return {
            id: resourcePage,
            title: "Add " + (RESOURCE_SINGULAR_LABELS[resourcePage] || config.title),
            fields: config.columns.map(function (column) {
                return {
                    key: column.key,
                    label: column.label,
                    type: "text",
                    required: true
                };
            }),
            toRow: function (values) {
                return createGenericResourceRow(config, values);
            }
        };
    }

    function buildResourceFormMarkup(schema) {
        return schema.fields.map(function (field) {
            return renderResourceFormField(schema, field);
        }).join("");
    }

    function renderResourceFormField(schema, field) {
        const fieldId = "resource-" + schema.id + "-" + field.key;
        const requiredAttribute = field.required ? " required" : "";
        const inputModeAttribute = field.inputMode ? ' inputmode="' + escapeHtml(field.inputMode) + '"' : "";
        let controlMarkup = "";

        if (field.type === "batch-category-selector") {
            controlMarkup = renderBatchCategorySelector(field, fieldId);
        } else if (field.type === "day-slot-selector") {
            controlMarkup = renderDaySlotSelector(field, fieldId);
        } else if (field.type === "select" || field.type === "multi-select") {
            const isMultiple = field.type === "multi-select";
            const disabledAttribute = field.waitsFor ? " disabled" : "";

            controlMarkup =
                '<select id="' +
                escapeHtml(fieldId) +
                '" data-field-input="' +
                escapeHtml(field.key) +
                '"' +
                (isMultiple ? " multiple" : "") +
                requiredAttribute +
                disabledAttribute +
                ">" +
                renderSelectOptions(field) +
                "</select>";
        } else {
            const inputType = field.type === "time" ? "time" : "text";

            controlMarkup =
                '<input id="' +
                escapeHtml(fieldId) +
                '" type="' +
                escapeHtml(inputType) +
                '" data-field-input="' +
                escapeHtml(field.key) +
                '"' +
                inputModeAttribute +
                requiredAttribute +
                ' autocomplete="off">';
        }

        return (
            '<div class="resource-form-field" data-field-wrapper="' +
            escapeHtml(field.key) +
            '">' +
            '<label for="' +
            escapeHtml(fieldId) +
            '">' +
            escapeHtml(field.label) +
            "</label>" +
            controlMarkup +
            '<p class="field-error" data-field-error></p>' +
            "</div>"
        );
    }

    function renderBatchCategorySelector(field, fieldId) {
        return (
            '<div class="chip-selector" data-batch-category-selector>' +
            '<input id="' +
            escapeHtml(fieldId) +
            '" type="hidden" data-field-input="' +
            escapeHtml(field.key) +
            '" value="[]">' +
            '<div class="dependent-selector-row">' +
            '<label class="visually-hidden" for="courseBatchPicker">Batch</label>' +
            '<select id="courseBatchPicker" data-batch-picker>' +
            '<option value="">Select Batch</option>' +
            getResourceFieldOptions({ source: "batches", optionValue: "batch", optionLabel: "batch" })
                .map(function (option) {
                    return '<option value="' + escapeHtml(option.value) + '">' + escapeHtml(option.label) + "</option>";
                })
                .join("") +
            "</select>" +
            '<label class="visually-hidden" for="courseCategoryPicker">Category</label>' +
            '<select id="courseCategoryPicker" class="is-hidden" data-category-picker disabled>' +
            '<option value="">Select Category</option>' +
            getResourceFieldOptions({ source: "categories", optionValue: "name", optionLabel: "name" })
                .map(function (option) {
                    return '<option value="' + escapeHtml(option.value) + '">' + escapeHtml(option.label) + "</option>";
                })
                .join("") +
            "</select>" +
            "</div>" +
            '<div class="chip-list is-empty" data-chip-list>' +
            '<span class="chip-empty-text">No batch categories selected yet.</span>' +
            "</div>" +
            "</div>"
        );
    }

    function renderDaySlotSelector(field, fieldId) {
        return (
            '<div class="chip-selector" data-day-slot-selector>' +
            '<input id="' +
            escapeHtml(fieldId) +
            '" type="hidden" data-field-input="' +
            escapeHtml(field.key) +
            '" value="[]">' +
            '<div class="dependent-selector-row">' +
            '<label class="visually-hidden" for="facultyDayPicker">Day</label>' +
            '<select id="facultyDayPicker" data-day-picker>' +
            '<option value="">Select Day</option>' +
            WEEK_DAYS.map(function (day) {
                return '<option value="' + escapeHtml(day) + '">' + escapeHtml(day) + "</option>";
            }).join("") +
            "</select>" +
            '<label class="visually-hidden" for="facultySlotPicker">Time Slot</label>' +
            '<select id="facultySlotPicker" data-time-slot-picker disabled>' +
            '<option value="">Select Time Slot</option>' +
            getUniqueSlotTimes()
                .map(function (time) {
                    return '<option value="' + escapeHtml(time) + '">' + escapeHtml(time) + "</option>";
                })
                .join("") +
            "</select>" +
            "</div>" +
            '<div class="chip-list is-empty" data-chip-list>' +
            '<span class="chip-empty-text">No unavailable slots selected yet.</span>' +
            "</div>" +
            "</div>"
        );
    }

    function renderSelectOptions(field) {
        if (field.waitsFor) {
            return '<option value="">Select batches first</option>';
        }

        const options = getResourceFieldOptions(field);
        const placeholder = field.type === "multi-select" ? "" : '<option value="">Select ' + escapeHtml(field.label) + "</option>";

        return (
            placeholder +
            options
                .map(function (option) {
                    return '<option value="' + escapeHtml(option.value) + '">' + escapeHtml(option.label) + "</option>";
                })
                .join("")
        );
    }

    function getResourceFieldOptions(field) {
        if (field.options) {
            return field.options.map(function (option) {
                if (typeof option === "string") {
                    return {
                        value: option,
                        label: option
                    };
                }

                return {
                    value: String(option.value || ""),
                    label: String(option.label || option.value || "")
                };
            });
        }

        const source = RESOURCE_CONFIGS[field.source];

        if (!source || !source.rows) {
            return [];
        }

        return source.rows.map(function (row) {
            const value = row[field.optionValue];
            const label = typeof field.optionLabel === "function" ? field.optionLabel(row) : row[field.optionLabel];

            return {
                value: String(value || ""),
                label: String(label || value || "")
            };
        });
    }

    function setupResourceFormInteractions(schema, form) {
        if (schema.id === "courses") {
            setupBatchCategorySelector(form);
        }

        if (schema.id === "faculty") {
            setupDaySlotSelector(form);
        }
    }

    function setupBatchCategorySelector(form) {
        const selector = form.querySelector("[data-batch-category-selector]");
        const batchSelect = selector ? selector.querySelector("[data-batch-picker]") : null;
        const categorySelect = selector ? selector.querySelector("[data-category-picker]") : null;
        const hiddenInput = selector ? selector.querySelector('[data-field-input="batchCategories"]') : null;

        if (!selector || !batchSelect || !categorySelect || !hiddenInput) {
            return;
        }

        batchSelect.addEventListener("change", function () {
            const hasBatch = Boolean(batchSelect.value);

            categorySelect.classList.toggle("is-hidden", !hasBatch);
            categorySelect.disabled = !hasBatch;
            categorySelect.value = "";
            clearFieldError(form, "batchCategories");
        });

        categorySelect.addEventListener("change", function () {
            const batch = batchSelect.value;
            const category = categorySelect.value;

            if (!batch || !category) {
                return;
            }

            if (!addStructuredSelection(hiddenInput, { batch: batch, category: category }, "batch", "category")) {
                showFieldMessage(form, "batchCategories", "This batch-category combination is already selected.");
                return;
            }

            renderBatchCategoryChips(selector, hiddenInput, form);
            batchSelect.value = "";
            categorySelect.value = "";
            categorySelect.disabled = true;
            categorySelect.classList.add("is-hidden");
            clearFieldError(form, "batchCategories");
            emitResourceFieldChange(hiddenInput);
        });

        selector.addEventListener("click", function (event) {
            const removeButton = event.target.closest("[data-remove-selection]");

            if (!removeButton) {
                return;
            }

            removeStructuredSelection(hiddenInput, Number(removeButton.dataset.removeSelection));
            renderBatchCategoryChips(selector, hiddenInput, form);
            emitResourceFieldChange(hiddenInput);
        });
    }

    function setupDaySlotSelector(form) {
        const selector = form.querySelector("[data-day-slot-selector]");
        const daySelect = selector ? selector.querySelector("[data-day-picker]") : null;
        const timeSelect = selector ? selector.querySelector("[data-time-slot-picker]") : null;
        const hiddenInput = selector ? selector.querySelector('[data-field-input="unavailableSlotSelections"]') : null;

        if (!selector || !daySelect || !timeSelect || !hiddenInput) {
            return;
        }

        daySelect.addEventListener("change", function () {
            const hasDay = Boolean(daySelect.value);

            timeSelect.disabled = !hasDay;
            timeSelect.value = "";
            clearFieldError(form, "unavailableSlotSelections");
        });

        timeSelect.addEventListener("change", function () {
            const day = daySelect.value;
            const time = timeSelect.value;

            if (!day || !time) {
                return;
            }

            if (!addStructuredSelection(hiddenInput, { day: day, time: time }, "day", "time")) {
                showFieldMessage(form, "unavailableSlotSelections", "This day and time slot is already selected.");
                return;
            }

            renderDaySlotChips(selector, hiddenInput, form);
            timeSelect.value = "";
            clearFieldError(form, "unavailableSlotSelections");
            emitResourceFieldChange(hiddenInput);
        });

        selector.addEventListener("click", function (event) {
            const removeButton = event.target.closest("[data-remove-selection]");

            if (!removeButton) {
                return;
            }

            removeStructuredSelection(hiddenInput, Number(removeButton.dataset.removeSelection));
            renderDaySlotChips(selector, hiddenInput, form);
            emitResourceFieldChange(hiddenInput);
        });
    }

    function addStructuredSelection(input, selection, primaryKey, secondaryKey) {
        const selections = getStructuredFieldValues(input);
        const exists = selections.some(function (item) {
            return item[primaryKey] === selection[primaryKey] && item[secondaryKey] === selection[secondaryKey];
        });

        if (exists) {
            return false;
        }

        selections.push(selection);
        input.value = JSON.stringify(selections);
        return true;
    }

    function removeStructuredSelection(input, index) {
        const selections = getStructuredFieldValues(input);

        selections.splice(index, 1);
        input.value = JSON.stringify(selections);
    }

    function renderBatchCategoryChips(selector, input, form) {
        const list = selector.querySelector("[data-chip-list]");
        const selections = getStructuredFieldValues(input);

        if (!list) {
            return;
        }

        list.classList.toggle("is-empty", selections.length === 0);
        list.innerHTML = selections.length
            ? selections.map(function (selection, index) {
                return renderSelectionChip(selection.batch + " " + selection.category, index);
            }).join("")
            : '<span class="chip-empty-text">No batch categories selected yet.</span>';

        clearFieldError(form, "batchCategories");
    }

    function renderDaySlotChips(selector, input, form) {
        const list = selector.querySelector("[data-chip-list]");
        const selections = getStructuredFieldValues(input);

        if (!list) {
            return;
        }

        list.classList.toggle("is-empty", selections.length === 0);
        list.innerHTML = selections.length
            ? selections.map(function (selection, index) {
                return renderSelectionChip(selection.day + " " + normalizeSlotSeparator(selection.time), index);
            }).join("")
            : '<span class="chip-empty-text">No unavailable slots selected yet.</span>';

        clearFieldError(form, "unavailableSlotSelections");
    }

    function renderSelectionChip(label, index) {
        return (
            '<span class="selection-chip">' +
            '<span>' +
            escapeHtml(label) +
            "</span>" +
            '<button type="button" aria-label="Remove ' +
            escapeHtml(label) +
            '" data-remove-selection="' +
            index +
            '">&times;</button>' +
            "</span>"
        );
    }

    function getStructuredFieldValues(input) {
        if (!input || !input.value) {
            return [];
        }

        try {
            const values = JSON.parse(input.value);

            return Array.isArray(values) ? values : [];
        } catch (error) {
            return [];
        }
    }

    function showFieldMessage(form, key, message) {
        const wrapper = form.querySelector('[data-field-wrapper="' + key + '"]');
        const input = form.querySelector('[data-field-input="' + key + '"]');
        const errorText = wrapper ? wrapper.querySelector("[data-field-error]") : null;

        if (wrapper) {
            wrapper.classList.add("has-error");
        }

        if (input) {
            input.setAttribute("aria-invalid", "true");
        }

        if (errorText) {
            errorText.textContent = message;
        }
    }

    function emitResourceFieldChange(input) {
        input.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function populateResourceForm(schema, form, row) {
        const values = getResourceRowFormValues(schema.id, row);

        schema.fields.forEach(function (field) {
            const input = form.querySelector('[data-field-input="' + field.key + '"]');

            if (!input) {
                return;
            }

            if (field.type === "batch-category-selector") {
                input.value = JSON.stringify(values[field.key] || []);
                renderBatchCategoryChips(form.querySelector("[data-batch-category-selector]"), input, form);
                return;
            }

            if (field.type === "day-slot-selector") {
                input.value = JSON.stringify(values[field.key] || []);
                renderDaySlotChips(form.querySelector("[data-day-slot-selector]"), input, form);
                return;
            }

            if (field.type === "multi-select") {
                setMultiSelectValues(input, values[field.key] || []);
                return;
            }

            input.value = values[field.key] || "";
        });
    }

    function getResourceRowFormValues(resourceId, row) {
        if (resourceId === "courses") {
            return {
                code: row.code || "",
                name: row.name || "",
                lectureHours: row.lectureHours || inferCourseHourValue(row, "lecture"),
                tutorialHours: row.tutorialHours || "0",
                labHours: row.labHours || inferCourseHourValue(row, "lab"),
                credits: row.credits || "",
                batchCategories: normalizeCourseBatchCategories(row),
                faculty: row.faculty || findFacultyForCourse(row) || ""
            };
        }

        if (resourceId === "faculty") {
            return {
                facultyCode: row.facultyId || "",
                facultyName: row.name || "",
                facultyEmail: row.email || "",
                maximumLoad: row.maximumLoad || stripHourSuffix(row.load)
            };
        }

        if (resourceId === "rooms") {
            return {
                classroomName: row.room || "",
                capacity: row.capacity || ""
            };
        }

        if (resourceId === "batches") {
            return {
                program: row.program || "",
                branch: row.branch || deriveBranchFromProgram(row.program),
                semester: row.semester || "",
                section: row.section || ""
            };
        }

        if (resourceId === "categories") {
            return {
                categoryName: row.name || ""
            };
        }

        if (resourceId === "slots") {
            return {
                slotName: row.slotName || "",
                dayOfWeek: row.dayOfWeek || normalizeDayPattern(row.dayPattern),
                startTime: row.startTime || (typeof row.time === "string" ? row.time.split(" - ")[0] : ""),
                endTime: row.endTime || (typeof row.time === "string" ? row.time.split(" - ")[1] : "")
            };
        }

        return Object.assign({}, row);
    }

    function setMultiSelectValues(select, values) {
        const selectedValues = Array.isArray(values) ? values : [];

        Array.from(select.options).forEach(function (option) {
            option.selected = selectedValues.includes(option.value);
        });
    }

    function bindResourceFormLiveValidation(schema, form, submitButton) {
        form.oninput = function (event) {
            handleResourceFormLiveChange(event, schema, form, submitButton);
        };

        form.onchange = function (event) {
            handleResourceFormLiveChange(event, schema, form, submitButton);
        };
    }

    function handleResourceFormLiveChange(event, schema, form, submitButton) {
        const target = event.target;

        if (target && target.dataset && target.dataset.fieldInput) {
            clearFieldError(form, target.dataset.fieldInput);
        }

        if (resourceModalElements) {
            setError(resourceModalElements.formError, "");
        }

        syncResourceSubmitState(schema, form, submitButton);
    }

    function syncResourceSubmitState(schema, form, submitButton) {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = !hasRequiredResourceValues(schema, form);
    }

    function hasRequiredResourceValues(schema, form) {
        return schema.fields.every(function (field) {
            const input = form.querySelector('[data-field-input="' + field.key + '"]');

            if (!field.required) {
                return true;
            }

            if (!input) {
                return false;
            }

            if (input.disabled && field.waitsFor) {
                return true;
            }

            if (field.type === "multi-select") {
                return getSelectedValues(input).length > 0;
            }

            if (field.type === "batch-category-selector" || field.type === "day-slot-selector") {
                return getStructuredFieldValues(input).length > 0;
            }

            return Boolean(input.value.trim());
        });
    }

    function handleResourceFormSubmit(event) {
        event.preventDefault();

        if (!activeResourceModalState) {
            return;
        }

        const modal = ensureResourceModal();
        const schema = activeResourceModalState.schema;
        const values = collectResourceFormValues(modal.form, schema);
        const errors = validateResourceForm(schema, values);

        clearResourceFormErrors(modal.form);
        setError(modal.formError, "");

        if (Object.keys(errors).length) {
            showResourceFormErrors(modal.form, modal.formError, errors);
            return;
        }

        if (activeResourceModalState.mode === "edit") {
            activeResourceModalState.config.rows[activeResourceModalState.rowIndex] = schema.toRow(
                values,
                activeResourceModalState.config.rows[activeResourceModalState.rowIndex]
            );
        } else {
            activeResourceModalState.config.rows.push(schema.toRow(values));
        }

        refreshResourceDataView(activeResourceModalState.config, activeResourceModalState.searchInput);
        closeResourceModal();
    }

    function collectResourceFormValues(form, schema) {
        const values = {};

        schema.fields.forEach(function (field) {
            const input = form.querySelector('[data-field-input="' + field.key + '"]');

            if (!input) {
                values[field.key] = field.type === "multi-select" ? [] : "";
                return;
            }

            if (field.type === "multi-select") {
                values[field.key] = getSelectedValues(input);
            } else if (field.type === "batch-category-selector" || field.type === "day-slot-selector") {
                values[field.key] = getStructuredFieldValues(input);
            } else {
                values[field.key] = input.value.trim();
            }
        });

        return values;
    }

    function validateResourceForm(schema, values) {
        const errors = {};

        schema.fields.forEach(function (field) {
            const value = values[field.key];
            const isEmpty = Array.isArray(value) ? value.length === 0 : !String(value || "").trim();

            if (field.required && isEmpty) {
                errors[field.key] = field.label + " is required.";
            }
        });

        schema.fields
            .filter(function (field) {
                return field.numeric || (schema.id === "courses" && COURSE_NUMERIC_FIELD_KEYS.includes(field.key));
            })
            .forEach(function (field) {
                const value = values[field.key];

                if (value && (!Number.isFinite(Number(value)) || Number(value) < 0)) {
                    errors[field.key] = field.label + " must be a number.";
                }
            });

        if (schema.id === "slots" && values.startTime && values.endTime) {
            const startMinutes = timeToMinutes(values.startTime);
            const endMinutes = timeToMinutes(values.endTime);

            if (endMinutes <= startMinutes) {
                errors.endTime = "End Time must be later than Start Time.";
            }
        }

        return errors;
    }

    function showResourceFormErrors(form, formError, errors) {
        setError(formError, "Please complete the highlighted fields.");

        Object.keys(errors).forEach(function (key) {
            const wrapper = form.querySelector('[data-field-wrapper="' + key + '"]');
            const input = form.querySelector('[data-field-input="' + key + '"]');
            const errorText = wrapper ? wrapper.querySelector("[data-field-error]") : null;

            if (wrapper) {
                wrapper.classList.add("has-error");
            }

            if (input) {
                input.setAttribute("aria-invalid", "true");
            }

            if (errorText) {
                errorText.textContent = errors[key];
            }
        });

        const firstInvalid = form.querySelector("[aria-invalid='true']");

        if (firstInvalid) {
            if (firstInvalid.type === "hidden") {
                const wrapper = firstInvalid.closest(".resource-form-field");
                const visibleControl = wrapper ? wrapper.querySelector("select:not([disabled]), input:not([type='hidden']), button") : null;

                if (visibleControl) {
                    visibleControl.focus();
                }
            } else {
                firstInvalid.focus();
            }
        }
    }

    function clearResourceFormErrors(form) {
        form.querySelectorAll(".resource-form-field.has-error").forEach(function (wrapper) {
            wrapper.classList.remove("has-error");
        });

        form.querySelectorAll("[aria-invalid='true']").forEach(function (input) {
            input.removeAttribute("aria-invalid");
        });

        form.querySelectorAll("[data-field-error]").forEach(function (errorText) {
            errorText.textContent = "";
        });
    }

    function clearFieldError(form, key) {
        const wrapper = form.querySelector('[data-field-wrapper="' + key + '"]');
        const input = form.querySelector('[data-field-input="' + key + '"]');
        const errorText = wrapper ? wrapper.querySelector("[data-field-error]") : null;

        if (wrapper) {
            wrapper.classList.remove("has-error");
        }

        if (input) {
            input.removeAttribute("aria-invalid");
        }

        if (errorText) {
            errorText.textContent = "";
        }
    }

    function closeResourceModal() {
        const modal = ensureResourceModal();
        const triggerButton = activeResourceModalState ? activeResourceModalState.triggerButton : null;

        activeResourceModalState = null;
        modal.overlay.classList.remove("is-open");
        document.body.classList.remove("modal-open");

        modal.closeTimer = window.setTimeout(function () {
            if (!modal.overlay.classList.contains("is-open")) {
                modal.overlay.hidden = true;
            }
        }, 180);

        if (triggerButton) {
            triggerButton.focus();
        }
    }

    function openDeleteConfirmationModal(resourcePage, config, searchInput, triggerButton, rowIndex) {
        const modal = ensureDeleteConfirmationModal();
        const row = config.rows[rowIndex];

        pendingDeleteState = {
            config: config,
            searchInput: searchInput,
            triggerButton: triggerButton,
            rowIndex: rowIndex
        };

        if (modal.closeTimer) {
            window.clearTimeout(modal.closeTimer);
            modal.closeTimer = null;
        }

        modal.message.textContent = 'Are you sure you want to delete "' + getDeleteEntryLabel(resourcePage, row) + '"?';
        modal.overlay.hidden = false;
        document.body.classList.add("modal-open");

        window.requestAnimationFrame(function () {
            modal.overlay.classList.add("is-open");
        });

        modal.cancelButton.focus();
    }

    function ensureDeleteConfirmationModal() {
        if (confirmationModalElements) {
            return confirmationModalElements;
        }

        const overlay = document.createElement("div");

        overlay.className = "resource-modal-overlay";
        overlay.dataset.confirmationModal = "";
        overlay.hidden = true;
        overlay.innerHTML =
            '<div class="resource-modal confirmation-modal" role="dialog" aria-modal="true" aria-labelledby="deleteModalTitle" tabindex="-1">' +
            '<div class="resource-modal-header">' +
            '<h2 id="deleteModalTitle">Delete Entry</h2>' +
            '<button class="resource-modal-close" type="button" aria-label="Close modal" data-delete-close>&times;</button>' +
            "</div>" +
            '<p class="confirmation-message" data-delete-message>Are you sure you want to delete this entry?</p>' +
            '<div class="resource-modal-actions">' +
            '<button class="delete-confirm-button" type="button" data-delete-confirm>Confirm Delete</button>' +
            '<button class="modal-cancel-button" type="button" data-delete-cancel>Cancel</button>' +
            "</div>" +
            "</div>";

        document.body.appendChild(overlay);

        confirmationModalElements = {
            overlay: overlay,
            message: overlay.querySelector("[data-delete-message]"),
            confirmButton: overlay.querySelector("[data-delete-confirm]"),
            cancelButton: overlay.querySelector("[data-delete-cancel]"),
            closeButton: overlay.querySelector("[data-delete-close]"),
            closeTimer: null
        };

        confirmationModalElements.confirmButton.addEventListener("click", confirmResourceDelete);
        confirmationModalElements.cancelButton.addEventListener("click", closeDeleteConfirmationModal);
        confirmationModalElements.closeButton.addEventListener("click", closeDeleteConfirmationModal);
        overlay.addEventListener("mousedown", function (event) {
            if (event.target === overlay) {
                closeDeleteConfirmationModal();
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && pendingDeleteState) {
                closeDeleteConfirmationModal();
            }
        });

        return confirmationModalElements;
    }

    function confirmResourceDelete() {
        if (!pendingDeleteState) {
            return;
        }

        pendingDeleteState.config.rows.splice(pendingDeleteState.rowIndex, 1);
        refreshResourceDataView(pendingDeleteState.config, pendingDeleteState.searchInput);
        closeDeleteConfirmationModal();
    }

    function closeDeleteConfirmationModal() {
        const modal = ensureDeleteConfirmationModal();
        const triggerButton = pendingDeleteState ? pendingDeleteState.triggerButton : null;

        pendingDeleteState = null;
        modal.overlay.classList.remove("is-open");
        document.body.classList.remove("modal-open");

        modal.closeTimer = window.setTimeout(function () {
            if (!modal.overlay.classList.contains("is-open")) {
                modal.overlay.hidden = true;
            }
        }, 180);

        if (triggerButton) {
            triggerButton.focus();
        }
    }

    function getDeleteEntryLabel(resourcePage, row) {
        if (!row) {
            return "this entry";
        }

        if (resourcePage === "courses") {
            return row.code || row.name || "this course";
        }

        if (resourcePage === "faculty") {
            return row.facultyId || row.name || "this faculty member";
        }

        if (resourcePage === "rooms") {
            return row.room || "this classroom";
        }

        if (resourcePage === "batches") {
            return row.batch || "this batch";
        }

        if (resourcePage === "categories") {
            return row.name || row.code || "this category";
        }

        if (resourcePage === "slots") {
            return row.slotName || "this slot";
        }

        return "this entry";
    }

    function refreshResourceDataView(config, searchInput) {
        renderMetrics(document.querySelector("[data-resource-metrics]"), config.metrics(config.rows));
        renderResourceTable(config, getFilteredResourceRows(config, searchInput ? searchInput.value : ""));
    }

    function getFilteredResourceRows(config, searchValue) {
        const value = String(searchValue || "").toLowerCase().trim();

        if (!value) {
            return config.rows;
        }

        return config.rows.filter(function (row) {
            return Object.keys(row).some(function (key) {
                return String(row[key]).toLowerCase().includes(value);
            });
        });
    }

    function createGenericResourceRow(config, values) {
        const row = {};

        config.columns.forEach(function (column) {
            row[column.key] = values[column.key];
        });

        return row;
    }

    function createCourseResourceRow(values, existingRow) {
        const batchCategories = values.batchCategories || [];
        const semesterLabels = batchCategories.map(function (selection) {
            const batch = RESOURCE_CONFIGS.batches.rows.find(function (row) {
                return row.batch === selection.batch;
            });

            return batch ? batch.semester : selection.batch;
        });
        const categoryLabels = batchCategories.map(function (selection) {
            return selection.batch + " " + selection.category;
        });

        return {
            code: values.code,
            name: values.name,
            category: categoryLabels.join(", "),
            credits: values.credits,
            semester: Array.from(new Set(semesterLabels)).join(", "),
            lectureHours: values.lectureHours,
            tutorialHours: values.tutorialHours,
            labHours: values.labHours,
            faculty: values.faculty,
            batchCategories: batchCategories.slice()
        };
    }

    function createFacultyResourceRow(values, existingRow) {
        return {
            facultyId: values.facultyCode,
            name: values.facultyName,
            email: values.facultyEmail || "",
            load: formatHourLoad(values.maximumLoad),
            maximumLoad: values.maximumLoad
        };
    }

    function createClassroomResourceRow(values, existingRow) {
        return {
            room: values.classroomName,
            type: existingRow && existingRow.type ? existingRow.type : "Theory",
            capacity: values.capacity,
            block: existingRow && existingRow.block ? existingRow.block : "Unassigned",
            status: existingRow && existingRow.status ? existingRow.status : "Active"
        };
    }

    function createBatchResourceRow(values, existingRow) {
        return {
            batch: values.branch + " " + values.semester + " " + values.section,
            program: values.program,
            branch: values.branch,
            semester: values.semester,
            section: values.section,
            strength: existingRow && existingRow.strength ? existingRow.strength : "0"
        };
    }

    function createCategoryResourceRow(values, existingRow) {
        return {
            name: values.categoryName
        };
    }

    function createSlotResourceRow(values, existingRow) {
        return {
            slotName: values.slotName,
            dayOfWeek: values.dayOfWeek,
            startTime: values.startTime,
            endTime: values.endTime
        };
    }

    function normalizeCourseBatchCategories(row) {
        if (Array.isArray(row.batchCategories)) {
            return row.batchCategories.map(function (selection) {
                return {
                    batch: selection.batch,
                    category: selection.category
                };
            });
        }

        const scheduleSelections = MASTER_TIMETABLE_TEMPLATE
            .filter(function (entry) {
                return entry.course === row.name;
            })
            .map(function (entry) {
                return {
                    batch: entry.batch,
                    category: entry.category
                };
            });

        if (scheduleSelections.length) {
            return uniqueStructuredSelections(scheduleSelections, "batch", "category");
        }

        const fallbackBatch = RESOURCE_CONFIGS.batches.rows.find(function (batch) {
            return batch.semester === row.semester;
        });

        if (fallbackBatch && row.category) {
            return [
                {
                    batch: fallbackBatch.batch,
                    category: row.category
                }
            ];
        }

        return [];
    }

    function normalizeFacultyUnavailableSlots(row) {
        if (!Array.isArray(row.unavailableSlots)) {
            return [];
        }

        return row.unavailableSlots
            .map(function (slot) {
                if (slot && typeof slot === "object" && slot.day && slot.time) {
                    return {
                        day: slot.day,
                        time: slot.time
                    };
                }

                const slotRow = RESOURCE_CONFIGS.slots.rows.find(function (entry) {
                    return entry.slotName === slot;
                });

                if (!slotRow) {
                    return null;
                }

                return {
                    day: slotRow.dayOfWeek,
                    time: slotRow.startTime + " - " + slotRow.endTime
                };
            })
            .filter(Boolean);
    }

    function uniqueStructuredSelections(selections, primaryKey, secondaryKey) {
        const seen = new Set();

        return selections.filter(function (selection) {
            const key = selection[primaryKey] + "::" + selection[secondaryKey];

            if (seen.has(key)) {
                return false;
            }

            seen.add(key);
            return true;
        });
    }

    function findFacultyForCourse(row) {
        const scheduleEntry = MASTER_TIMETABLE_TEMPLATE.find(function (entry) {
            return entry.course === row.name;
        });

        return scheduleEntry ? scheduleEntry.faculty : "";
    }

    function inferCourseHourValue(row, kind) {
        const category = String(row.category || "").toLowerCase();

        if (kind === "lab") {
            return category.includes("lab") ? "2" : "0";
        }

        return category.includes("lab") ? "0" : "3";
    }

    function stripHourSuffix(value) {
        return String(value || "").replace(/\s*hrs?\.?\s*$/i, "");
    }

    function splitSlotTime(row) {
        const value = String(row.time || "");
        const parts = value.split(/\s*-\s*/);

        return {
            startTime: toTimeInputValue(parts[0]),
            endTime: toTimeInputValue(parts[1])
        };
    }

    function toTimeInputValue(value) {
        const parts = String(value || "").split(":");

        if (parts.length < 2) {
            return "";
        }

        return parts[0].padStart(2, "0") + ":" + parts[1].padStart(2, "0");
    }

    function normalizeDayPattern(value) {
        const normalized = String(value || "").trim();

        if (WEEK_DAYS.includes(normalized)) {
            return normalized;
        }

        if (normalized.toLowerCase().startsWith("mon")) {
            return "Monday";
        }

        return WEEK_DAYS[0];
    }

    function getUniqueResourceValues(resourceKey, rowKey) {
        const resource = RESOURCE_CONFIGS[resourceKey];

        if (!resource || !resource.rows) {
            return [];
        }

        return Array.from(new Set(
            resource.rows
                .map(function (row) {
                    return row[rowKey];
                })
                .filter(Boolean)
        ));
    }

    function getBatchBranchOptions() {
        const branches = RESOURCE_CONFIGS.batches.rows
            .map(function (row) {
                return deriveBranchFromProgram(row.program);
            })
            .filter(Boolean);

        return Array.from(new Set(branches));
    }

    function deriveBranchFromProgram(programName) {
        const parts = String(programName || "").trim().split(/\s+/);

        return parts.length ? parts[parts.length - 1] : "";
    }

    function getSlotOptionLabel(slot) {
        return slot.slotName + " | " + slot.startTime + " - " + slot.endTime + " | " + slot.dayOfWeek;
    }

    function getUniqueSlotTimes() {
        return Array.from(new Set(
            RESOURCE_CONFIGS.slots.rows
                .map(function (slot) {
                    return slot.time;
                })
                .filter(Boolean)
        ));
    }

    function normalizeSlotSeparator(time) {
        return String(time || "").replace(/\s*-\s*/g, " - ");
    }

    function getNextSlotCode() {
        const nextNumber = RESOURCE_CONFIGS.slots.rows.length + 1;

        return "S" + nextNumber;
    }

    function formatHourLoad(value) {
        const normalized = String(value || "").trim();

        if (!normalized) {
            return "";
        }

        return normalized.toLowerCase().includes("hr") ? normalized : normalized + " hrs";
    }

    function createCategoryCode(name) {
        const words = String(name || "")
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        if (!words.length) {
            return "CAT";
        }

        return words
            .map(function (word) {
                return word.charAt(0).toUpperCase();
            })
            .join("")
            .slice(0, 4);
    }

    function formatSlotTime(startTime, endTime) {
        return formatTimeForDisplay(startTime) + " - " + formatTimeForDisplay(endTime);
    }

    function formatTimeForDisplay(value) {
        const parts = String(value || "").split(":");

        if (parts.length < 2) {
            return value;
        }

        return parts[0].padStart(2, "0") + ":" + parts[1].padStart(2, "0");
    }

    function timeToMinutes(value) {
        const parts = String(value || "").split(":");
        const hours = Number(parts[0]);
        const minutes = Number(parts[1]);

        if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
            return 0;
        }

        return hours * 60 + minutes;
    }

    function getSelectedValues(select) {
        return Array.from(select.selectedOptions)
            .map(function (option) {
                return option.value;
            })
            .filter(Boolean);
    }

    function renderMetrics(container, metrics) {
        if (!container) {
            return;
        }

        container.innerHTML = metrics
            .map(function (metric) {
                return (
                    '<article class="stat-card stat-card-muted">' +
                    '<span class="stat-label">' +
                    escapeHtml(metric.label) +
                    "</span>" +
                    '<strong class="stat-value">' +
                    escapeHtml(String(metric.value)) +
                    "</strong>" +
                    "<p>" +
                    escapeHtml(metric.detail) +
                    "</p>" +
                    "</article>"
                );
            })
            .join("");
    }

    function renderHighlights(container, highlights) {
        if (!container) {
            return;
        }

        container.innerHTML = highlights
            .map(function (item) {
                return (
                    '<div class="detail-row">' +
                    "<span>" +
                    escapeHtml(item.label) +
                    "</span>" +
                    "<strong>" +
                    escapeHtml(item.value) +
                    "</strong>" +
                    "</div>"
                );
            })
            .join("");
    }

    function renderResourceTable(config, rows) {
        const head = document.querySelector("[data-resource-head]");
        const body = document.querySelector("[data-resource-body]");
        const emptyState = document.getElementById("resourceEmptyState");

        if (!head || !body) {
            return;
        }

        head.innerHTML =
            "<tr>" +
            config.columns
                .map(function (column) {
                    return "<th>" + escapeHtml(column.label) + "</th>";
                })
                .join("") +
            (config.showActions === false ? "" : '<th class="actions-header">Actions</th>') +
            "</tr>";

        body.innerHTML = rows
            .map(function (row) {
                const rowIndex = config.rows.indexOf(row);

                return (
                    "<tr>" +
                    config.columns
                        .map(function (column) {
                            return "<td>" + formatTableCell(row[column.key], column.badge) + "</td>";
                        })
                        .join("") +
                    (config.showActions === false ? "" : '<td class="actions-cell">' + renderResourceActionButtons(rowIndex) + "</td>") +
                    "</tr>"
                );
            })
            .join("");

        if (emptyState) {
            emptyState.classList.toggle("is-hidden", rows.length > 0);
        }
    }

    function renderResourceActionButtons(rowIndex) {
        if (rowIndex < 0) {
            return "";
        }

        return (
            '<div class="row-action-buttons" aria-label="Row actions">' +
            '<button class="row-action-button" type="button" data-row-action="edit" data-row-index="' +
            rowIndex +
            '" aria-label="Edit entry">' +
            '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
            '<path d="M4 20h4.7L18.9 9.8l-4.7-4.7L4 15.3V20zm11.3-16 1.4-1.4a1.5 1.5 0 0 1 2.1 0l2.6 2.6a1.5 1.5 0 0 1 0 2.1L20 8.7 15.3 4z"></path>' +
            "</svg>" +
            "</button>" +
            '<button class="row-action-button is-danger" type="button" data-row-action="delete" data-row-index="' +
            rowIndex +
            '" aria-label="Delete entry">' +
            '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
            '<path d="M7 21a2 2 0 0 1-2-2V8h14v11a2 2 0 0 1-2 2H7zM9 4h6l1 2h4v2H4V6h4l1-2zm1 6v8h2v-8h-2zm4 0v8h2v-8h-2z"></path>' +
            "</svg>" +
            "</button>" +
            "</div>"
        );
    }

    function setupTimetablePage() {
        const tabButtons = document.querySelectorAll("[data-view-tab]");
        const downloadButton = document.getElementById("downloadTimetableButton");

        if (!tabButtons.length || !downloadButton) {
            return;
        }

        const generation = getStoredGeneration();
        const selectedView = getStoredValue(STORAGE_KEYS.selectedView, "overall");

        tabButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                const view = button.dataset.viewTab;
                saveStoredValue(STORAGE_KEYS.selectedView, view);
                renderTimetableView(view, getStoredGeneration());
            });
        });

        downloadButton.addEventListener("click", function () {
            const currentView = getStoredValue(STORAGE_KEYS.selectedView, "overall");
            const currentGeneration = getStoredGeneration();

            if (!currentGeneration) {
                return;
            }

            downloadTimetableWorkbook(currentView, currentGeneration.schedule, currentGeneration.generatedAt);
        });

        renderTimetableView(selectedView, generation);
    }

    function renderTimetableView(view, generation) {
        const activeView = TIMETABLE_VIEWS[view] ? view : "overall";
        const config = TIMETABLE_VIEWS[activeView];
        const chip = document.getElementById("timetableStatusChip");
        const downloadButton = document.getElementById("downloadTimetableButton");
        const helper = document.getElementById("downloadHelperText");
        const emptyState = document.getElementById("timetableEmptyState");
        const statusCards = document.getElementById("timetableStatusCards");

        document.querySelectorAll("[data-view-tab]").forEach(function (button) {
            button.classList.toggle("is-active", button.dataset.viewTab === activeView);
        });

        setText("selectedTimetableTitle", config.title);
        setText("selectedTimetableDescription", config.description);

        if (!generation) {
            if (chip) {
                chip.textContent = "No run";
                chip.classList.remove("is-ready");
            }

            if (downloadButton) {
                downloadButton.disabled = true;
            }

            if (helper) {
                helper.textContent = "Run Dashboard first to enable downloads.";
            }

            if (emptyState) {
                emptyState.classList.remove("is-hidden");
            }

            if (statusCards) {
                statusCards.innerHTML = "";
            }

            return;
        }

        if (chip) {
            chip.textContent = "Ready";
            chip.classList.add("is-ready");
        }

        if (downloadButton) {
            downloadButton.disabled = false;
        }

        if (helper) {
            helper.textContent = "From run: " + formatDateTime(generation.generatedAt);
        }

        if (emptyState) {
            emptyState.classList.add("is-hidden");
        }

        if (statusCards) {
            const groups = getTimetableGroups(activeView, generation.schedule);
            const groupCount = Object.keys(groups).length;
            const cards = [
                {
                    label: "Selected View",
                    value: config.title,
                    detail: "From latest run."
                },
                {
                    label: "Export Groups",
                    value: groupCount,
                    detail: activeView === "overall" ? "1 combined sheet." : "Grouped export sheets."
                },
                {
                    label: "Last Generated",
                    value: formatDateTime(generation.generatedAt),
                    detail: "Used for downloads."
                }
            ];

            statusCards.innerHTML = cards
                .map(function (card) {
                    return (
                        '<article class="stat-card stat-card-muted">' +
                        '<span class="stat-label">' +
                        escapeHtml(card.label) +
                        "</span>" +
                        '<strong class="stat-value">' +
                        escapeHtml(String(card.value)) +
                        "</strong>" +
                        "<p>" +
                        escapeHtml(card.detail) +
                        "</p>" +
                        "</article>"
                    );
                })
                .join("");
        }
    }

    function downloadTimetableWorkbook(view, schedule, generatedAt) {
        const sections = buildWorkbookSections(view, schedule);
        const html = buildWorkbookHtml(view, sections, generatedAt);
        const blob = new Blob([html], {
            type: "application/vnd.ms-excel;charset=utf-8;"
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");

        link.href = url;
        link.download = TIMETABLE_VIEWS[view].filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    function buildWorkbookSections(view, schedule) {
        if (view === "overall") {
            return [
                {
                    title: "Overall Timetable",
                    headers: ["Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    rows: buildOverallGrid(schedule)
                }
            ];
        }

        const groups = getTimetableGroups(view, schedule);

        return Object.keys(groups)
            .sort()
            .map(function (groupName) {
                return {
                    title: groupName,
                    headers: ["Day", "Time", "Course", "Faculty", "Room", "Batch", "Category"],
                    rows: groups[groupName].map(function (entry) {
                        return [
                            entry.day,
                            entry.slot,
                            entry.course,
                            entry.faculty,
                            entry.room,
                            entry.batch,
                            entry.category
                        ];
                    })
                };
            });
    }

    function buildWorkbookHtml(view, sections, generatedAt) {
        const title = TIMETABLE_VIEWS[view].title + " Timetable";
        const tables = sections
            .map(function (section) {
                return (
                    "<h2>" +
                    escapeHtml(section.title) +
                    "</h2>" +
                    "<table>" +
                    "<thead><tr>" +
                    section.headers
                        .map(function (header) {
                            return "<th>" + escapeHtml(header) + "</th>";
                        })
                        .join("") +
                    "</tr></thead>" +
                    "<tbody>" +
                    section.rows
                        .map(function (row) {
                            return (
                                "<tr>" +
                                row
                                    .map(function (cell) {
                                        return "<td>" + escapeHtml(String(cell || "")) + "</td>";
                                    })
                                    .join("") +
                                "</tr>"
                            );
                        })
                        .join("") +
                    "</tbody></table>"
                );
            })
            .join("");

        return (
            '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">' +
            "<head>" +
            '<meta charset="utf-8">' +
            "<title>" +
            escapeHtml(title) +
            "</title>" +
            "<style>" +
            "body{font-family:Trebuchet MS,sans-serif;color:#5C4F4A;padding:24px;background:#EDE9E6;}" +
            "h1,h2{font-family:Georgia,serif;color:#5C4F4A;}" +
            "h1{margin-bottom:8px;}" +
            "h2{margin:28px 0 10px;}" +
            "p{margin:0 0 12px;}" +
            "table{width:100%;border-collapse:collapse;margin-bottom:22px;}" +
            "th,td{border:1px solid #5C4F4A;padding:8px 10px;text-align:left;}" +
            "th{background:#C9996B;color:#5C4F4A;}" +
            "</style>" +
            "</head>" +
            "<body>" +
            "<h1>" +
            escapeHtml(title) +
            "</h1>" +
            "<p>Generated on " +
            escapeHtml(formatDateTime(generatedAt)) +
            "</p>" +
            tables +
            "</body></html>"
        );
    }

    function buildOverallGrid(schedule) {
        const slotOrder = RESOURCE_CONFIGS.slots.rows.map(function (row) {
            return row.time;
        });

        return slotOrder.map(function (slot) {
            const row = [slot];

            DAYS.forEach(function (day) {
                const session = schedule.find(function (entry) {
                    return entry.day === day && entry.slot === slot;
                });

                row.push(session ? session.course + " | " + session.batch + " | " + session.room : "");
            });

            return row;
        });
    }

    function getTimetableGroups(view, schedule) {
        if (view === "overall") {
            return { "Overall Timetable": schedule.slice() };
        }

        const groupKey = view === "faculty" ? "faculty" : view === "rooms" ? "room" : "batch";
        const groups = {};

        schedule
            .slice()
            .sort(compareScheduleEntries)
            .forEach(function (entry) {
                const key = entry[groupKey];

                if (!groups[key]) {
                    groups[key] = [];
                }

                groups[key].push(entry);
            });

        return groups;
    }

    function createGenerationPayload() {
        return {
            generatedAt: new Date().toISOString(),
            report: {
                courseClashes: 2,
                facultyClashes: 1,
                courseNote: "2 course overlaps auto-resolved.",
                facultyNote: "1 faculty clash auto-resolved."
            },
            schedule: MASTER_TIMETABLE_TEMPLATE.slice().sort(compareScheduleEntries)
        };
    }

    function compareScheduleEntries(a, b) {
        const dayDifference = DAYS.indexOf(a.day) - DAYS.indexOf(b.day);

        if (dayDifference !== 0) {
            return dayDifference;
        }

        const slotOrder = RESOURCE_CONFIGS.slots.rows.map(function (row) {
            return row.time;
        });

        return slotOrder.indexOf(a.slot) - slotOrder.indexOf(b.slot);
    }

    function handleLogout() {
        clearStoredGeneration();

        fetch("/api/v1/auth/logout", {
            method: "POST",
            credentials: "include"
        }).catch(function () {
            return null;
        }).finally(function () {
            window.location.href = "login.html";
        });
    }

    function getStoredGeneration() {
        const raw = getStoredValue(STORAGE_KEYS.generation, "");

        if (!raw) {
            return null;
        }

        try {
            return JSON.parse(raw);
        } catch (error) {
            return null;
        }
    }

    function storeGeneration(payload) {
        saveStoredValue(STORAGE_KEYS.generation, JSON.stringify(payload));
        saveStoredValue(STORAGE_KEYS.selectedView, "overall");
    }

    function clearStoredGeneration() {
        try {
            localStorage.removeItem(STORAGE_KEYS.generation);
            localStorage.removeItem(STORAGE_KEYS.selectedView);
        } catch (error) {
            return;
        }
    }

    function setButtonBusy(button, isBusy, label) {
        if (!button) {
            return;
        }

        button.disabled = isBusy;
        button.textContent = label;
    }

    function setError(element, message) {
        if (!element) {
            return;
        }

        element.textContent = message;
        element.classList.toggle("is-hidden", !message);
    }

    function setText(target, value) {
        const element = typeof target === "string" ? document.querySelector(target) || document.getElementById(target) : target;

        if (element) {
            element.textContent = value;
        }
    }

    function safeJson(response) {
        return response.json().catch(function () {
            return {};
        });
    }

    function saveStoredValue(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (error) {
            return;
        }
    }

    function getStoredValue(key, fallback) {
        try {
            const value = localStorage.getItem(key);
            return value === null ? fallback : value;
        } catch (error) {
            return fallback;
        }
    }

    function delay(ms) {
        return new Promise(function (resolve) {
            window.setTimeout(resolve, ms);
        });
    }

    function formatDateTime(isoString) {
        const date = new Date(isoString);

        if (Number.isNaN(date.getTime())) {
            return "Unavailable";
        }

        return date.toLocaleString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit"
        });
    }

    function formatTableCell(value, badgeType) {
        const safeValue = escapeHtml(String(value || ""));

        if (!badgeType) {
            return safeValue;
        }

        const className = badgeType === "secondary" ? "table-pill is-secondary" : "table-pill";
        return '<span class="' + className + '">' + safeValue + "</span>";
    }

    function uniqueCount(rows, key) {
        return new Set(
            rows.map(function (row) {
                return row[key];
            })
        ).size;
    }

    function countMatching(rows, key, expectedValue) {
        return rows.filter(function (row) {
            return row[key] === expectedValue;
        }).length;
    }

    function countContaining(rows, key, fragment) {
        return rows.filter(function (row) {
            return String(row[key]).includes(fragment);
        }).length;
    }

    function sumValues(rows, key) {
        return rows.reduce(function (total, row) {
            return total + Number.parseInt(row[key], 10);
        }, 0);
    }

    function maxValue(rows, key) {
        return rows.reduce(function (highest, row) {
            const value = Number.parseInt(row[key], 10);

            if (Number.isNaN(value)) {
                return highest;
            }

            return Math.max(highest, value);
        }, 0);
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }
})();
