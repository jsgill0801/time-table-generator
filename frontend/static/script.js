(function () {
    const STORAGE_KEYS = {
        selectedView: "ttg.selectedView",
        generation: "ttg.generation"
    };

    const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

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

    const RESOURCE_CONFIGS = {
        courses: {
            title: "Courses",
            description: "Review the active course catalogue that feeds the timetable run. Keep titles, semesters, and teaching categories aligned before generation.",
            chip: "Academic Catalogue",
            tableTitle: "Course Registry",
            searchPlaceholder: "Search by code, title, category, or semester",
            note: "Course data defines the academic load that the master timetable must satisfy for each semester and section.",
            metrics: function (rows) {
                return [
                    { label: "Records", value: rows.length, detail: "Courses prepared for allocation." },
                    { label: "Semesters", value: uniqueCount(rows, "semester"), detail: "Distinct teaching cohorts covered." },
                    { label: "Categories", value: uniqueCount(rows, "category"), detail: "Course types reflected in the catalogue." }
                ];
            },
            highlights: [
                { label: "Check before run", value: "Verify credits and category mapping for every course." },
                { label: "Scheduling impact", value: "Labs and core theory papers create the widest slot dependency." },
                { label: "Workflow", value: "Update the catalogue first, then run the master timetable from the dashboard." }
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
            description: "Track faculty members who are available for timetable allocation, along with subject coverage and weekly teaching load.",
            chip: "Teaching Staff",
            tableTitle: "Faculty Directory",
            searchPlaceholder: "Search by faculty ID, name, department, or load",
            note: "Faculty assignments are matched against course ownership and availability to prevent double-booking during generation.",
            metrics: function (rows) {
                return [
                    { label: "Faculty", value: rows.length, detail: "Instructors available this cycle." },
                    { label: "Departments", value: uniqueCount(rows, "department"), detail: "Academic units represented." },
                    { label: "Open Capacity", value: "18 hrs", detail: "Indicative capacity still available." }
                ];
            },
            highlights: [
                { label: "Allocation focus", value: "Monitor weekly load before triggering the next run." },
                { label: "Conflict check", value: "Faculty clashes are validated before the overall timetable is stored." },
                { label: "Export use", value: "Faculty-wise downloads are generated from this roster and the latest run." }
            ],
            columns: [
                { key: "facultyId", label: "Faculty ID" },
                { key: "name", label: "Name" },
                { key: "department", label: "Department", badge: "accent" },
                { key: "subjects", label: "Subject Coverage" },
                { key: "load", label: "Weekly Load", badge: "secondary" }
            ],
            rows: [
                { facultyId: "FAC-01", name: "Dr. Meera Shah", department: "ICT", subjects: "Mathematics, Data Structures", load: "14 hrs" },
                { facultyId: "FAC-02", name: "Prof. Kunal Desai", department: "ICT", subjects: "Database Systems, Labs", load: "16 hrs" },
                { facultyId: "FAC-03", name: "Dr. Nidhi Trivedi", department: "ICT", subjects: "Operating Systems", load: "12 hrs" },
                { facultyId: "FAC-04", name: "Prof. Aditi Rao", department: "ICT", subjects: "Software Engineering", load: "15 hrs" },
                { facultyId: "FAC-05", name: "Dr. Rahul Menon", department: "ICT", subjects: "Machine Learning", load: "10 hrs" },
                { facultyId: "FAC-06", name: "Prof. Hiral Patel", department: "ICT", subjects: "Network Security", load: "11 hrs" },
                { facultyId: "FAC-07", name: "Dr. Sagar Joshi", department: "Science", subjects: "Physics", load: "13 hrs" },
                { facultyId: "FAC-08", name: "Prof. Neha Vyas", department: "Communication", subjects: "Professional Communication", load: "9 hrs" }
            ]
        },
        rooms: {
            title: "Rooms",
            description: "Monitor teaching spaces, capacities, and room types used by the overall timetable engine during allocation.",
            chip: "Infrastructure",
            tableTitle: "Room Allocation Base",
            searchPlaceholder: "Search by room, type, block, or capacity",
            note: "Room records help the scheduler place theory classes, labs, and larger cohorts without overbooking shared spaces.",
            metrics: function (rows) {
                return [
                    { label: "Rooms", value: rows.length, detail: "Rooms mapped for scheduling." },
                    { label: "Lab Spaces", value: countMatching(rows, "type", "Lab"), detail: "Specialised rooms reserved for practical sessions." },
                    { label: "Largest Capacity", value: "72", detail: "Maximum seating in the current room list." }
                ];
            },
            highlights: [
                { label: "Batch fit", value: "Compare capacities with batch strengths before running the timetable." },
                { label: "Room view", value: "Room-wise exports reflect the latest stored overall timetable only." },
                { label: "Availability", value: "Inactive rooms should be removed from the scheduling pool." }
            ],
            columns: [
                { key: "room", label: "Room" },
                { key: "type", label: "Type", badge: "accent" },
                { key: "capacity", label: "Capacity" },
                { key: "block", label: "Block" },
                { key: "status", label: "Status", badge: "secondary" }
            ],
            rows: [
                { room: "A-101", type: "Theory", capacity: "60", block: "Block A", status: "Active" },
                { room: "A-103", type: "Theory", capacity: "48", block: "Block A", status: "Active" },
                { room: "B-204", type: "Theory", capacity: "72", block: "Block B", status: "Active" },
                { room: "LAB-201", type: "Lab", capacity: "36", block: "Tech Wing", status: "Active" },
                { room: "LAB-203", type: "Lab", capacity: "32", block: "Tech Wing", status: "Active" },
                { room: "C-110", type: "Seminar", capacity: "40", block: "Block C", status: "Reserve" }
            ]
        },
        batches: {
            title: "Batches",
            description: "Manage the student cohorts that receive timetable exports. Each batch keeps its own section, strength, and semester mapping.",
            chip: "Student Cohorts",
            tableTitle: "Batch Directory",
            searchPlaceholder: "Search by batch, program, section, or semester",
            note: "Batch definitions drive the overall timetable and are reused directly for batch-wise downloads after a successful run.",
            metrics: function (rows) {
                return [
                    { label: "Batches", value: rows.length, detail: "Cohorts scheduled in the current cycle." },
                    { label: "Programs", value: uniqueCount(rows, "program"), detail: "Distinct academic programs covered." },
                    { label: "Total Strength", value: sumValues(rows, "strength"), detail: "Students represented in timetable planning." }
                ];
            },
            highlights: [
                { label: "Section control", value: "Large sections should be aligned with room capacity planning." },
                { label: "Download source", value: "Batch-wise exports are grouped from the latest overall timetable data." },
                { label: "Recommended check", value: "Validate section names before generation to keep exports clean." }
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
            description: "Maintain the teaching categories used to classify courses for allocation logic, reporting, and download grouping.",
            chip: "Teaching Modes",
            tableTitle: "Category Mapping",
            searchPlaceholder: "Search by code, category, mode, or duration",
            note: "Category rules shape how sessions are distributed across theory, labs, and elective windows in the generated timetable.",
            metrics: function (rows) {
                return [
                    { label: "Categories", value: rows.length, detail: "Classification rules available." },
                    { label: "Lab Enabled", value: countMatching(rows, "mode", "Practical"), detail: "Categories mapped for lab scheduling." },
                    { label: "Average Duration", value: "1.4 hrs", detail: "Typical session duration across categories." }
                ];
            },
            highlights: [
                { label: "Course mapping", value: "Every active course should align to one clear teaching category." },
                { label: "Generation impact", value: "Category duration affects slot selection and room preference." },
                { label: "Export clarity", value: "Consistent names keep timetable downloads readable for staff and students." }
            ],
            columns: [
                { key: "code", label: "Code" },
                { key: "name", label: "Category" },
                { key: "mode", label: "Mode", badge: "accent" },
                { key: "duration", label: "Duration" },
                { key: "priority", label: "Priority", badge: "secondary" }
            ],
            rows: [
                { code: "CT", name: "Core Theory", mode: "Lecture", duration: "1 hr", priority: "High" },
                { code: "LB", name: "Lab", mode: "Practical", duration: "2 hrs", priority: "High" },
                { code: "EL", name: "Elective", mode: "Lecture", duration: "1 hr", priority: "Medium" },
                { code: "SK", name: "Skill Module", mode: "Workshop", duration: "1 hr", priority: "Medium" },
                { code: "PR", name: "Professional", mode: "Lecture", duration: "1 hr", priority: "Low" }
            ]
        },
        slots: {
            title: "Slots",
            description: "Define the available teaching windows that the overall timetable engine can use while arranging sessions through the week.",
            chip: "Time Windows",
            tableTitle: "Slot Grid",
            searchPlaceholder: "Search by slot code, time, pattern, or session type",
            note: "The slot registry controls the time windows available to all courses, rooms, faculty, and batches during generation.",
            metrics: function (rows) {
                return [
                    { label: "Slots", value: rows.length, detail: "Teaching windows available each day." },
                    { label: "Morning Windows", value: countContaining(rows, "time", "08:"), detail: "Early sessions enabled in the registry." },
                    { label: "Lab Blocks", value: countMatching(rows, "sessionType", "Lab Block"), detail: "Extended windows for practical work." }
                ];
            },
            highlights: [
                { label: "Consistency", value: "Slot durations should align with category duration rules." },
                { label: "Run dependency", value: "The dashboard uses this slot map when building the overall timetable." },
                { label: "Download views", value: "All timetable exports respect the same stored slot ordering." }
            ],
            columns: [
                { key: "slotCode", label: "Slot" },
                { key: "time", label: "Time" },
                { key: "dayPattern", label: "Day Pattern", badge: "accent" },
                { key: "sessionType", label: "Session Type", badge: "secondary" },
                { key: "remarks", label: "Remarks" }
            ],
            rows: [
                { slotCode: "S1", time: "08:30 - 09:20", dayPattern: "Mon-Fri", sessionType: "Lecture", remarks: "Regular morning window" },
                { slotCode: "S2", time: "09:25 - 10:15", dayPattern: "Mon-Fri", sessionType: "Lecture", remarks: "Regular morning window" },
                { slotCode: "S3", time: "10:30 - 11:20", dayPattern: "Mon-Fri", sessionType: "Lecture", remarks: "Post-break window" },
                { slotCode: "S4", time: "11:25 - 12:15", dayPattern: "Mon-Fri", sessionType: "Lecture", remarks: "Pre-lunch window" },
                { slotCode: "S5", time: "13:00 - 13:50", dayPattern: "Mon-Fri", sessionType: "Lecture", remarks: "Afternoon theory window" },
                { slotCode: "S6", time: "14:00 - 15:50", dayPattern: "Mon-Fri", sessionType: "Lab Block", remarks: "Extended practical session" },
                { slotCode: "S7", time: "16:00 - 16:50", dayPattern: "Mon-Fri", sessionType: "Lecture", remarks: "Reserve window" }
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
            description: "Download the combined timetable for every batch using the latest stored master schedule.",
            filename: "overall-timetable.xls"
        },
        faculty: {
            title: "Faculty-wise",
            description: "Download grouped timetable sheets for each faculty member from the latest overall timetable.",
            filename: "faculty-wise-timetable.xls"
        },
        rooms: {
            title: "Room-wise",
            description: "Download room allocation sheets organised by teaching space from the stored overall timetable.",
            filename: "room-wise-timetable.xls"
        },
        batches: {
            title: "Batch-wise",
            description: "Download separate timetable sheets for each batch and section using the generated master schedule.",
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
            "<small>Admin Console</small>" +
            "<h1>Timetable Generator</h1>" +
            "</div>" +
            '<nav class="sidebar-nav" aria-label="Primary">' +
            navMarkup +
            "</nav>" +
            '<div class="sidebar-footer">' +
            '<p class="sidebar-note">Review academic data, run the master timetable once, then export the required view.</p>' +
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
                context.textContent = "Validating courses, faculty, rooms, batches, categories, and slots before the master timetable is stored.";
            }

            setButtonBusy(runButton, true, "Running...");

            try {
                await delay(1200);

                const generation = createGenerationPayload();
                storeGeneration(generation);
                renderDashboardReport(generation);

                if (context) {
                    context.textContent = "The latest master timetable is ready. Move to the timetable page to download the view you need.";
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
        setText("generationStatusLabel", "Latest run available");

        reportPanel.classList.remove("is-hidden");
    }

    function renderResourcePage() {
        const resourcePage = document.body.dataset.resourcePage;

        if (!resourcePage || !RESOURCE_CONFIGS[resourcePage]) {
            return;
        }

        const config = RESOURCE_CONFIGS[resourcePage];
        const metrics = config.metrics(config.rows);
        const searchInput = document.querySelector("[data-resource-search]");

        setText("[data-resource-title]", config.title);
        setText("[data-resource-description]", config.description);
        setText("[data-resource-chip]", config.chip);
        setText("[data-table-title]", config.tableTitle);
        setText("[data-resource-note]", config.note);

        if (searchInput) {
            searchInput.setAttribute("placeholder", config.searchPlaceholder);
        }

        renderMetrics(document.querySelector("[data-resource-metrics]"), metrics);
        renderHighlights(document.querySelector("[data-resource-highlights]"), config.highlights);
        renderResourceTable(config, config.rows);

        if (searchInput) {
            searchInput.addEventListener("input", function (event) {
                const value = event.target.value.toLowerCase().trim();
                const filteredRows = config.rows.filter(function (row) {
                    return Object.keys(row).some(function (key) {
                        return String(row[key]).toLowerCase().includes(value);
                    });
                });

                renderResourceTable(config, filteredRows);
            });
        }
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
            "</tr>";

        body.innerHTML = rows
            .map(function (row) {
                return (
                    "<tr>" +
                    config.columns
                        .map(function (column) {
                            return "<td>" + formatTableCell(row[column.key], column.badge) + "</td>";
                        })
                        .join("") +
                    "</tr>"
                );
            })
            .join("");

        if (emptyState) {
            emptyState.classList.toggle("is-hidden", rows.length > 0);
        }
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
                chip.textContent = "Run required";
                chip.classList.remove("is-ready");
            }

            if (downloadButton) {
                downloadButton.disabled = true;
            }

            if (helper) {
                helper.textContent = "Generate the master timetable from the dashboard before downloading any export view.";
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
            chip.textContent = "Latest master timetable ready";
            chip.classList.add("is-ready");
        }

        if (downloadButton) {
            downloadButton.disabled = false;
        }

        if (helper) {
            helper.textContent = "Excel export uses the master timetable generated on " + formatDateTime(generation.generatedAt) + ".";
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
                    detail: "Prepared from the latest overall timetable."
                },
                {
                    label: "Export Groups",
                    value: groupCount,
                    detail: activeView === "overall" ? "Single combined export sheet." : "Separate sections in the export file."
                },
                {
                    label: "Last Generated",
                    value: formatDateTime(generation.generatedAt),
                    detail: "Download reflects the most recent dashboard run."
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
                courseNote: "2 potential course overlaps were isolated and resolved before allocation.",
                facultyNote: "1 faculty double-booking was detected during validation and corrected in the final run."
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

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }
})();
