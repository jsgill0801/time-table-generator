(function () {
    const STORAGE_KEYS = {
        selectedView: "ttg.selectedView"
    };

    const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

    const SIDEBAR_ITEMS = [
        { id: "dashboard", label: "Dashboard", href: "/dashboard" },
        { id: "faculty", label: "Faculty", href: "/faculty" },
        { id: "rooms", label: "Rooms", href: "/rooms" },
        { id: "batches", label: "Batches", href: "/batches" },
        { id: "categories", label: "Categories", href: "/categories" },
        { id: "slots", label: "Slots", href: "/slots" },
        { id: "courses", label: "Courses", href: "/courses" },
        { id: "timetable", label: "Timetable", href: "/timetable" }
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
    let currentUser = null;
    let currentUserResolved = false;
    let currentUserPromise = null;
    let adminBootstrapPromise = null;

    const RESOURCE_CONFIGS = {
        courses: {
            title: "Courses",
            description: "",
            chip: "Course Data",
            tableTitle: "Course List",
            searchPlaceholder: "",
            note: "Check names, semesters, and categories before you run.",
            metrics: function (rows) {
                return [];
            },
            highlights: [],
            columns: [
                { key: "code", label: "Course Code" },
                { key: "name", label: "Course Name" },
                { key: "lectureHours", label: "Number of Lecture Hours" },
                { key: "tutorialHours", label: "Tutorial Hours" },
                { key: "labHours", label: "Lab Hours" },
                { key: "credits", label: "Credits" },
                { key: "batchCategories", label: "BATCH-CATEGORY" },
                { key: "studentsEnrolled", label: "Students Enrolled" },
                { key: "faculty", label: "Faculty" }
            ],
            rows: []
        },
        faculty: {
            title: "Faculty",
            description: "",
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
            rows: []
        },
        rooms: {
            title: "Rooms",
            description: "",
            chip: "Room Data",
            tableTitle: "Room List",
            searchPlaceholder: "Search room or capacity",
            note: "List only classrooms and capacities.",
            metrics: function (rows) {
                return [
                    { label: "Rooms", value: rows.length, detail: "Available to schedule." },
                    { label: "Largest Capacity", value: maxValue(rows, "capacity"), detail: "Seats in the largest room." }
                ];
            },
            highlights: [],
            columns: [
                { key: "room", label: "Room" },
                { key: "capacity", label: "Capacity" }
            ],
            rows: []
        },
        batches: {
            title: "Batches",
            description: "Student groups included in the timetable.",
            chip: "Batch Data",
            tableTitle: "Batch List",
            searchPlaceholder: "Search branch, program, section, or semester",
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
                { key: "program", label: "Program" },
                { key: "branch", label: "Branch" },
                { key: "semester", label: "Semester", badge: "secondary" },
                { key: "section", label: "Section", badge: "accent" }
            ],
            rows: []
        },
        categories: {
            title: "Categories",
            description: "",
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
            rows: []
        },
        slots: {
            title: "Slots",
            description: "",
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
            rows: []
        }
    };

    let MASTER_TIMETABLE_TEMPLATE = [];
    let latestGeneration = null;

    const TIMETABLE_VIEWS = {
        overall: {
            title: "Overall",
            description: "Combined file for all batches.",
            filename: "overall-timetable.xlsx"
        },
        faculty: {
            title: "Faculty-wise",
            description: "One file grouped by faculty.",
            filename: "faculty-wise-timetable.xlsx"
        },
        rooms: {
            title: "Room-wise",
            description: "One file grouped by room.",
            filename: "room-wise-timetable.xlsx"
        },
        batches: {
            title: "Batch-wise",
            description: "One file grouped by batch.",
            filename: "batch-wise-timetable.xlsx"
        }
    };

    document.addEventListener("DOMContentLoaded", async function () {
        buildSidebar();
        setupAuthForms();
        await loadResourceDataFromAPI();
        setupDashboardPage();
        renderResourcePage();
        setupTimetablePage();
        setupCSVImportForms();
        await setupUsersPage();
    });

    function isAuthPage() {
        return Boolean(document.getElementById("loginForm") || document.getElementById("signupForm"));
    }

    async function loadCurrentUser() {
        if (currentUserResolved) {
            return currentUser;
        }

        if (currentUserPromise) {
            return currentUserPromise;
        }

        currentUserPromise = API.me()
            .then(function (response) {
                currentUser = response && response.user ? response.user : null;
                currentUserResolved = true;
                return currentUser;
            })
            .catch(function () {
                currentUser = null;
                currentUserResolved = true;
                return null;
            })
            .finally(function () {
                currentUserPromise = null;
            });

        return currentUserPromise;
    }

    function hasAnySeededData(counts) {
        return [
            "courses",
            "batches",
            "faculties",
            "classrooms",
            "slots",
            "categories",
            "batch_courses",
            "faculty_courses"
        ].some(function (key) {
            return Number(counts[key] || 0) > 0;
        });
    }

    async function ensureAdminDemoData() {
        if (isAuthPage()) {
            return null;
        }

        if (adminBootstrapPromise) {
            return adminBootstrapPromise;
        }

        adminBootstrapPromise = (async function () {
            const user = await loadCurrentUser();

            if (!user || user.role !== "admin") {
                return null;
            }

            const countResponse = await API.counts().catch(function () {
                return null;
            });
            const counts = countResponse && countResponse.counts ? countResponse.counts : null;

            if (!counts || hasAnySeededData(counts)) {
                return null;
            }

            return API.bootstrapAdminDemo().catch(function (error) {
                if (!error || error.status !== 409) {
                    console.warn("Unable to load admin demo data.", error);
                }

                return null;
            });
        })();

        return adminBootstrapPromise;
    }

    async function loadResourceDataFromAPI() {
        if (isAuthPage()) return;

        await loadCurrentUser();
        buildSidebar();
        await ensureAdminDemoData();

        try {
            const [courses, batches, faculty, rooms, categories, slots, batchCourses, facultyCourses, timetableResponse, conflictsResponse] = await Promise.all([
                API.listCourses().catch(() => []),
                API.listBatches().catch(() => []),
                API.listFaculty().catch(() => []),
                API.listClassrooms().catch(() => []),
                API.listCategories().catch(() => []),
                API.listSlots().catch(() => []),
                API.listBatchCourses().catch(() => []),
                API.listFacultyCourses().catch(() => []),
                API.timetable().catch(() => ({ timetable: [], generated_at: null })),
                API.conflicts().catch(() => ({ conflicts: [] })),
            ]);
            RESOURCE_CONFIGS.batches.rows = (Array.isArray(batches) ? batches : []).map(function(b) {
                return { id: b.batch_id, batch: b.label || (b.program+" "+b.branch+" Sem "+b.semester+" "+(b.section || "")), program: b.program, branch: b.branch, semester: String(b.semester), section: b.section || "", strength: "0" };
            });
            RESOURCE_CONFIGS.faculty.rows = (Array.isArray(faculty) ? faculty : []).map(function(f) {
                return { facultyId: f.faculty_code, name: f.faculty_name, email: f.faculty_email, load: f.max_load+" hrs", maximumLoad: String(f.max_load) };
            });
            RESOURCE_CONFIGS.rooms.rows = (Array.isArray(rooms) ? rooms : []).map(function(r) {
                return { room: r.classroom_name, capacity: String(r.capacity), status: "Active" };
            });
            RESOURCE_CONFIGS.categories.rows = (Array.isArray(categories) ? categories : []).map(function(c) {
                return { id: c.category_id, name: c.category_name };
            });
            RESOURCE_CONFIGS.slots.rows = (Array.isArray(slots) ? slots : []).map(function(s) {
                var st = String(s.start_time||""); if(st.length>5) st=st.substring(0,5);
                var et = String(s.end_time||""); if(et.length>5) et=et.substring(0,5);
                return { slotId: s.slot_id, slotName: s.slot_name, startTime: st, endTime: et, dayOfWeek: s.day_of_week, time: st+" - "+et };
            });

            const batchCourseRows = Array.isArray(batchCourses) ? batchCourses : [];
            const facultyCourseRows = Array.isArray(facultyCourses) ? facultyCourses : [];
            const facultyByCode = {};

            RESOURCE_CONFIGS.faculty.rows.forEach(function(row) {
                facultyByCode[row.facultyId] = row;
            });

            RESOURCE_CONFIGS.courses.rows = (Array.isArray(courses) ? courses : []).map(function(c) {
                const courseBatchMappings = batchCourseRows
                    .filter(function(bc) { return Number(bc.course_id) === Number(c.course_id); })
                    .map(function(bc) {
                        return {
                            mappingId: bc.auto_id,
                            batch: bc.batch_label,
                            batchId: bc.batch_id,
                            category: bc.category_name || "",
                            categoryId: bc.category_id || "",
                            studentsEnrolled: String(bc.students_enrolled || 1)
                        };
                    });
                const courseFacultyMappings = facultyCourseRows
                    .filter(function(fc) { return Number(fc.course_id) === Number(c.course_id); });
                const primaryFaculty = courseFacultyMappings[0] || null;
                const facultyCode = primaryFaculty ? primaryFaculty.faculty_code : "";
                const facultyRow = facultyCode ? facultyByCode[facultyCode] : null;

                return {
                    id: c.course_id,
                    code: c.course_code,
                    name: c.course_name,
                    lectureHours: String(c.lectures || 0),
                    tutorialHours: String(c.tutorials || 0),
                    labHours: String(c.labs || 0),
                    credits: String(c.credits || 0),
                    studentsEnrolled: String(
                        courseBatchMappings.length ? Number(courseBatchMappings[0].studentsEnrolled || 1) : 1
                    ),
                    batchCategories: courseBatchMappings,
                    facultyCode: facultyCode,
                    faculty: facultyRow ? facultyRow.name : (primaryFaculty ? primaryFaculty.faculty_name || facultyCode : ""),
                    facultyMappings: courseFacultyMappings
                };
            });

            latestGeneration = buildGenerationFromBackend(timetableResponse, conflictsResponse);
            if (latestGeneration) {
                storeGeneration(latestGeneration);
            }
            MASTER_TIMETABLE_TEMPLATE = latestGeneration ? latestGeneration.schedule.slice() : [];
        } catch(e) { console.warn("Data load failed", e); }
    }

    function setupCSVImportForms() {
        document.querySelectorAll(".import-form").forEach(function(form) {
            form.addEventListener("submit", async function(e) {
                e.preventDefault();
                var btn = form.querySelector('button[type="submit"]');
                var origText = btn.textContent;
                btn.disabled = true; btn.textContent = "Uploading...";
                try {
                    var fd = new FormData(form);
                    var action = form.getAttribute("action");
                    var resp = await fetch(action, { method:"POST", credentials:"include", body:fd });
                    var data = await resp.json().catch(function(){return {};});
                    if (!resp.ok) {
                        alert(buildApiErrorMessage(data, "Import failed."));
                        return;
                    }
                    alert(data.message||"Import complete.");
                    await API.clearTimetable().catch(function(){ return null; });
                    await loadResourceDataFromAPI();
                    var page = document.body.dataset.resourcePage;
                    if (page && RESOURCE_CONFIGS[page]) {
                        var si = document.querySelector("[data-resource-search]");
                        refreshResourceDataView(RESOURCE_CONFIGS[page], si);
                    }
                    setDashboardStatCounts();
                } catch(err) { alert(buildApiErrorMessage(err, "Upload failed. Check server.")); }
                finally { btn.disabled=false; btn.textContent=origText; }
            });
        });
    }

    window.logout = handleLogout;

    function buildSidebar() {
        const sidebar = document.querySelector("[data-sidebar]");

        if (!sidebar) {
            return;
        }

        const activePage = document.body.dataset.page || "";
        const items = SIDEBAR_ITEMS.slice();
        if (currentUser && currentUser.username === "admin") {
            items.push({ id: "users", label: "Users", href: "/users" });
        }
        const navMarkup = items.map(function (item) {
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

            window.location.href = "/dashboard";
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
        const masterAdminPassword = document.getElementById("signupMasterAdminPassword").value;

        setError(errorBox, "");

        if (!/^[a-zA-Z0-9]+$/.test(username)) {
            setError(errorBox, "Username must contain alphanumeric characters only (no spaces or special characters).");
            return;
        }

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
                    password: password,
                    masterAdminPassword: masterAdminPassword
                })
            });

            const data = await safeJson(response);

            if (!response.ok) {
                setError(errorBox, data.error || "Unable to create the account with the current details.");
                return;
            }

            window.location.href = "/login";
        } catch (error) {
            setError(errorBox, "Unable to reach the signup service right now. Please verify the server is running.");
        } finally {
            setButtonBusy(submitButton, false, "Create Account");
        }
    }

    function setupDashboardPage() {
        const runButton = document.getElementById("runTimetableButton");

        if (!runButton) {
            return;
        }

        setDashboardStatCounts();

        const savedGeneration = getStoredGeneration();

        if (savedGeneration) {
            renderDashboardReport(savedGeneration);
        }

        runButton.addEventListener("click", async function () {
            // #region agent log
            fetch('http://127.0.0.1:7305/ingest/20e5ec9d-8ac9-4437-998b-fdadc17eb559',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ecec21'},body:JSON.stringify({sessionId:'ecec21',runId:'dashboard-run-click',hypothesisId:'H11',location:'script.js:setupDashboardPage:click',message:'Run button clicked',data:{buttonDisabled:!!runButton.disabled,currentLabel:runButton.textContent||''},timestamp:Date.now()})}).catch(()=>{});
            // #endregion
            setButtonBusy(runButton, true, "Generating...");

            try {
                // #region agent log
                fetch('http://127.0.0.1:7305/ingest/20e5ec9d-8ac9-4437-998b-fdadc17eb559',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ecec21'},body:JSON.stringify({sessionId:'ecec21',runId:'dashboard-run-click',hypothesisId:'H11',location:'script.js:setupDashboardPage:beforeGenerate',message:'Calling API.generate',data:{},timestamp:Date.now()})}).catch(()=>{});
                // #endregion
                const result = await API.generate();
                // #region agent log
                fetch('http://127.0.0.1:7305/ingest/20e5ec9d-8ac9-4437-998b-fdadc17eb559',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ecec21'},body:JSON.stringify({sessionId:'ecec21',runId:'dashboard-run-click',hypothesisId:'H11',location:'script.js:setupDashboardPage:afterGenerate',message:'API.generate resolved',data:{status:(result&&result.status)||'',scheduled_sessions:(result&&result.scheduled_sessions)||null},timestamp:Date.now()})}).catch(()=>{});
                // #endregion
                await refreshLatestGenerationFromAPI(result);
                const generation = getStoredGeneration();
                renderDashboardReport(generation);
            } catch(err) {
                // #region agent log
                fetch('http://127.0.0.1:7305/ingest/20e5ec9d-8ac9-4437-998b-fdadc17eb559',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'ecec21'},body:JSON.stringify({sessionId:'ecec21',runId:'dashboard-run-click',hypothesisId:'H11',location:'script.js:setupDashboardPage:catch',message:'API.generate failed',data:{error:(err&&err.message)||'',status:(err&&err.status)||null},timestamp:Date.now()})}).catch(()=>{});
                // #endregion
                alert(buildApiErrorMessage(err, "Generation failed. Ensure data is imported first."));
            } finally {
                setButtonBusy(runButton, false, "Run");
            }
        });
    }

    async function refreshLatestGenerationFromAPI(generateResult) {
        const [timetableResponse, conflictsResponse] = await Promise.all([
            API.timetable().catch(function () { return { timetable: [], generated_at: null }; }),
            API.conflicts().catch(function () { return { conflicts: [] }; })
        ]);
        storeGeneration(buildGenerationFromBackend(timetableResponse, conflictsResponse, generateResult));
    }

    function buildGenerationFromBackend(timetableResponse, conflictsResponse, generateResult) {
        const rows = timetableResponse && Array.isArray(timetableResponse.timetable)
            ? timetableResponse.timetable
            : [];
        const conflicts = conflictsResponse && Array.isArray(conflictsResponse.conflicts)
            ? conflictsResponse.conflicts
            : [];

        if (!rows.length && !conflicts.length && !generateResult) {
            return null;
        }

        const schedule = rows.map(mapTimetableRowToScheduleEntry).sort(compareScheduleEntries);
        const generatedAt = (
            timetableResponse && timetableResponse.generated_at
        ) || (
            rows.find(function(row) { return row.generated_at; }) || {}
        ).generated_at || (
            generateResult && generateResult.generated_at
        ) || new Date().toISOString();

        return {
            generatedAt: generatedAt,
            report: buildBackendGenerationReport(schedule, conflicts, generateResult),
            schedule: schedule
        };
    }

    function mapTimetableRowToScheduleEntry(row) {
        const start = String(row.start_time || "").substring(0, 5);
        const end = String(row.end_time || "").substring(0, 5);

        return {
            id: row.auto_id,
            day: row.day_of_week || "",
            slot: start && end ? start + " - " + end : row.slot_name || "",
            slotName: row.slot_name || "",
            course: row.course_name || row.course_code || "",
            courseCode: row.course_code || "",
            faculty: row.faculty_code || "",
            room: row.classroom_name || "",
            batch: row.batch_label || "",
            category: row.category_name || ""
        };
    }

    function buildBackendGenerationReport(schedule, conflicts, generateResult) {
        const conflictItems = (Array.isArray(conflicts) ? conflicts : []).map(function(conflict) {
            return {
                title: (conflict.course_code || "Course") + (conflict.course_name ? " - " + conflict.course_name : ""),
                badge: conflict.course_code || "Issue",
                meta: "Batch: " + (conflict.batch_label || "Not mapped") + " | Faculty: " + (conflict.faculty_code || "Unassigned"),
                reason: conflict.reason || "This session could not be placed."
            };
        });
        const scheduledCourses = new Set(schedule.map(function(entry) {
            return entry.courseCode || entry.course;
        }).filter(Boolean));
        const configuredCourses = new Set(RESOURCE_CONFIGS.courses.rows.map(function(row) {
            return row.code;
        }).filter(Boolean));
        conflictItems.forEach(function(conflict) {
            if (conflict.badge && conflict.badge !== "Issue") {
                configuredCourses.add(conflict.badge);
            }
        });

        const totalCourses = generateResult && Number.isFinite(Number(generateResult.total_courses))
            ? Number(generateResult.total_courses)
            : configuredCourses.size;
        const totalSessions = generateResult && Number.isFinite(Number(generateResult.total_sessions))
            ? Number(generateResult.total_sessions)
            : schedule.length + conflictItems.length;
        const scheduledSessions = generateResult && Number.isFinite(Number(generateResult.scheduled_sessions))
            ? Number(generateResult.scheduled_sessions)
            : schedule.length;
        const totalIssues = generateResult && Number.isFinite(Number(generateResult.conflicts_count))
            ? Number(generateResult.conflicts_count)
            : conflictItems.length;

        return {
            totalCourses: totalSessions || totalCourses,
            coursesScheduled: scheduledSessions || scheduledCourses.size,
            courseUsageNote: scheduledSessions + " of " + totalSessions + " required session(s) placed.",
            courseClashes: totalIssues,
            facultyClashes: 0,
            roomConflicts: 0,
            slotConflicts: 0,
            courseNote: totalIssues ? totalIssues + " unresolved session(s)." : "All required sessions were placed.",
            facultyNote: "Faculty conflicts are checked by the backend scheduler.",
            roomNote: "Room conflicts are checked by the backend scheduler.",
            slotNote: "Slot conflicts are checked by the backend scheduler.",
            conflictSummary: totalIssues
                ? totalIssues + " unresolved scheduling issue(s) in the latest run."
                : "No unresolved scheduling conflicts in the latest run.",
            conflicts: conflictItems,
            totalIssues: totalIssues
        };
    }

    function renderDashboardReport(generation) {
        const reportPanel = document.getElementById("dashboardReport");
        const report = generation &&
            generation.report &&
            Array.isArray(generation.report.conflicts) &&
            typeof generation.report.totalIssues === "number" &&
            typeof generation.report.roomConflicts === "number" &&
            typeof generation.report.slotConflicts === "number"
            ? generation.report
            : buildGenerationReport(generation && generation.schedule ? generation.schedule : MASTER_TIMETABLE_TEMPLATE.slice().sort(compareScheduleEntries));

        if (!reportPanel || !generation) {
            return;
        }

        setText("courseUsageCount", report.coursesScheduled + " / " + report.totalCourses);
        setText("courseUsageText", report.courseUsageNote);
        setText("courseClashCount", report.courseClashes);
        setText("facultyClashCount", report.facultyClashes);
        setText("roomConflictCount", report.roomConflicts);
        setText("slotConflictCount", report.slotConflicts);
        setText("courseClashText", report.courseNote);
        setText("facultyClashText", report.facultyNote);
        setText("roomConflictText", report.roomNote);
        setText("slotConflictText", report.slotNote);
        setText("conflictReportSummary", report.conflictSummary);
        setText("lastRunText", "Last generated on " + formatDateTime(generation.generatedAt) + ".");
        renderConflictReportList(document.getElementById("conflictReportList"), report.conflicts);

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

        if (searchInput) {
            searchInput.setAttribute("placeholder", config.searchPlaceholder);
        }

        renderMetrics(document.querySelector("[data-resource-metrics]"), config.metrics(config.rows));
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
                    { key: "studentsEnrolled", label: "Students Enrolled", type: "text", inputMode: "numeric", required: true, numeric: true },
                    { key: "batchCategories", label: "Batches", type: "batch-category-selector", required: true },
                    { key: "faculty", label: "Faculty", type: "select", source: "faculty", optionValue: "facultyId", optionLabel: "name", required: true },
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
                    { key: "program", label: "Program", type: "text", required: true },
                    { key: "branch", label: "Branch", type: "text", required: true },
                    { key: "semester", label: "Semester", type: "text", inputMode: "numeric", required: true, numeric: true },
                    { key: "section", label: "Section", type: "text", required: true }
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
                studentsEnrolled: row.studentsEnrolled || "1",
                batchCategories: normalizeCourseBatchCategories(row),
                faculty: row.facultyCode || findFacultyCodeForCourse(row) || ""
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

    async function handleResourceFormSubmit(event) {
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

        setButtonBusy(modal.submitButton, true, activeResourceModalState.mode === "edit" ? "Saving..." : "Adding...");

        try {
            await persistResourceForm(
                schema.id,
                values,
                activeResourceModalState.mode,
                activeResourceModalState.config.rows[activeResourceModalState.rowIndex]
            );
            await API.clearTimetable().catch(function() { return null; });
            await loadResourceDataFromAPI();
            refreshResourceDataView(activeResourceModalState.config, activeResourceModalState.searchInput);
            setDashboardStatCounts();
            closeResourceModal();
        } catch (error) {
            setError(modal.formError, error.error || error.message || "Unable to save this entry.");
        } finally {
            setButtonBusy(modal.submitButton, false, activeResourceModalState && activeResourceModalState.mode === "edit" ? "Edit" : "Add");
        }
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

        // 1. Required fields validation
        schema.fields.forEach(function (field) {
            const value = values[field.key];
            const isEmpty = Array.isArray(value) ? value.length === 0 : !String(value || "").trim();

            if (field.required && isEmpty) {
                errors[field.key] = field.label + " is required.";
            }
        });

        // Helper regex patterns
        const lettersOnlyRegex = /^[a-zA-Z\s]+$/;
        const alphanumericMinimalRegex = /^[a-zA-Z0-9\s-]+$/;
        const codeRegex = /^[a-zA-Z0-9]+$/;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const integerRegex = /^[0-9]+$/;
        const decimalRegex = /^[0-9]+(\.[0-9]+)?$/;

        // 2. Specific field type/regex validations
        schema.fields.forEach(function (field) {
            const value = String(values[field.key] || "").trim();
            if (!value) return; // Skip validation if empty (handled by required check)

            // A. Letters Only fields (names)
            if (
                field.key === "facultyName" ||
                field.key === "name" ||
                field.key === "categoryName" ||
                field.key === "slotName"
            ) {
                if (!lettersOnlyRegex.test(value)) {
                    errors[field.key] = field.label + " must contain letters only.";
                }
            }

            // B. Email validation
            else if (field.key === "facultyEmail") {
                if (!emailRegex.test(value)) {
                    errors[field.key] = "Please enter a valid email address.";
                }
            }

            // C. Alphanumeric with minimal special characters (Course Code, Faculty Code, Section)
            else if (field.key === "code" || field.key === "facultyCode" || field.key === "section") {
                if (!codeRegex.test(value)) {
                    errors[field.key] = field.label + " must be alphanumeric only (no spaces or special characters).";
                }
            }

            // D. Alphanumeric with spaces and hyphens (Classroom Name, Program, Branch)
            else if (
                field.key === "classroomName" ||
                field.key === "program" ||
                field.key === "branch"
            ) {
                if (!alphanumericMinimalRegex.test(value)) {
                    errors[field.key] = field.label + " must contain letters, numbers, spaces, or hyphens only.";
                }
            }

            // E. Integer checks (Capacity, Semester, Students Enrolled)
            else if (
                field.key === "capacity" ||
                field.key === "semester" ||
                field.key === "studentsEnrolled"
            ) {
                if (!integerRegex.test(value)) {
                    errors[field.key] = field.label + " must be a positive integer.";
                }
            }

            // F. Decimal / General Numeric checks (Lectures, Tutorials, Labs, Credits, Max Load)
            else if (
                field.numeric ||
                (schema.id === "courses" && COURSE_NUMERIC_FIELD_KEYS.includes(field.key)) ||
                field.key === "maximumLoad"
            ) {
                if (!decimalRegex.test(value)) {
                    errors[field.key] = field.label + " must be a valid number.";
                }
            }
        });

        // 3. Custom validations
        if (schema.id === "courses" && Array.isArray(values.batchCategories)) {
            const invalidSelection = values.batchCategories.find(function (item) {
                return !item;
            });
            if (invalidSelection) {
                errors.batchCategories = "Each batch-category entry must be valid.";
            }
        }

        if (
            schema.id === "courses" &&
            errors.studentsEnrolled === undefined &&
            (!Number.isFinite(Number(values.studentsEnrolled)) || Number(values.studentsEnrolled) < 1)
        ) {
            errors.studentsEnrolled = "Students Enrolled must be at least 1.";
        }

        if (schema.id === "slots" && values.startTime && values.endTime) {
            const startMinutes = timeToMinutes(values.startTime);
            const endMinutes = timeToMinutes(values.endTime);

            if (endMinutes <= startMinutes) {
                errors.endTime = "End Time must be later than Start Time.";
            }
        }

        return errors;
    }

    async function persistResourceForm(resourceId, values, mode, existingRow) {
        if (resourceId === "courses") {
            return persistCourse(values, mode, existingRow);
        }

        if (resourceId === "faculty") {
            const payload = {
                faculty_code: values.facultyCode,
                faculty_name: values.facultyName,
                faculty_email: values.facultyEmail,
                max_load: values.maximumLoad
            };
            return mode === "edit"
                ? API.updateFaculty(existingRow.facultyId, payload)
                : API.createFaculty(payload);
        }

        if (resourceId === "rooms") {
            const payload = {
                classroom_name: values.classroomName,
                capacity: values.capacity
            };
            return mode === "edit"
                ? API.updateClassroom(existingRow.room, payload)
                : API.createClassroom(payload);
        }

        if (resourceId === "batches") {
            const payload = {
                program: values.program,
                branch: values.branch,
                semester: parseSemesterValue(values.semester),
                section: values.section
            };
            return mode === "edit"
                ? API.updateBatch(existingRow.id, payload)
                : API.createBatch(payload);
        }

        if (resourceId === "categories") {
            const payload = { category_name: values.categoryName };
            return mode === "edit"
                ? API.updateCategory(existingRow.id, payload)
                : API.createCategory(payload);
        }

        if (resourceId === "slots") {
            const payload = {
                slot_name: values.slotName,
                day_of_week: values.dayOfWeek,
                start_time: values.startTime,
                end_time: values.endTime
            };
            return mode === "edit"
                ? API.updateSlot(existingRow.slotId, payload)
                : API.createSlot(payload);
        }

        return Promise.resolve();
    }

    async function persistCourse(values, mode, existingRow) {
        const payload = {
            course_code: values.code,
            course_name: values.name,
            lectures: values.lectureHours,
            tutorials: values.tutorialHours,
            labs: values.labHours,
            credits: values.credits
        };
        const course = mode === "edit"
            ? await API.updateCourse(existingRow.id, payload)
            : await API.createCourse(payload);
        const courseId = course.course_id || (existingRow && existingRow.id);

        await syncCourseBatchMappings(courseId, values.batchCategories || [], existingRow, values.studentsEnrolled);
        await syncCourseFacultyMapping(courseId, values.faculty, existingRow);

        return course;
    }

    async function syncCourseBatchMappings(courseId, selections, existingRow, totalStudentsEnrolled) {
        const existingMappings = existingRow && Array.isArray(existingRow.batchCategories)
            ? existingRow.batchCategories
            : [];

        for (const mapping of existingMappings) {
            if (mapping.mappingId) {
                await API.deleteBatchCourse(mapping.mappingId).catch(function(error) {
                    if (error.status !== 404) {
                        throw error;
                    }
                });
            }
        }

        for (const selection of selections) {
            const batchId = selection.batchId || getBatchIdByLabel(selection.batch);
            const categoryId = selection.categoryId || getCategoryIdByName(selection.category);

            if (!batchId) {
                throw new Error("Selected batch is no longer available.");
            }

            await API.createBatchCourse({
                course_id: courseId,
                batch_id: batchId,
                category_id: categoryId || null,
                students_enrolled: totalStudentsEnrolled || "1"
            });
        }
    }

    async function syncCourseFacultyMapping(courseId, facultyCode, existingRow) {
        const existingMappings = existingRow && Array.isArray(existingRow.facultyMappings)
            ? existingRow.facultyMappings
            : [];

        for (const mapping of existingMappings) {
            if (mapping.auto_id) {
                await API.deleteFacultyCourse(mapping.auto_id).catch(function(error) {
                    if (error.status !== 404) {
                        throw error;
                    }
                });
            }
        }

        if (facultyCode) {
            await API.createFacultyCourse({
                course_id: courseId,
                faculty_code: facultyCode
            });
        }
    }

    async function deleteResourceRow(resourceId, row) {
        await API.clearTimetable().catch(function() { return null; });

        if (resourceId === "courses") {
            return API.deleteCourse(row.id);
        }
        if (resourceId === "faculty") {
            return API.deleteFaculty(row.facultyId);
        }
        if (resourceId === "rooms") {
            return API.deleteClassroom(row.room);
        }
        if (resourceId === "batches") {
            return API.deleteBatch(row.id);
        }
        if (resourceId === "categories") {
            return API.deleteCategory(row.id);
        }
        if (resourceId === "slots") {
            return API.deleteSlot(row.slotId);
        }
        return Promise.resolve();
    }

    function getBatchIdByLabel(label) {
        const row = RESOURCE_CONFIGS.batches.rows.find(function(batch) {
            return batch.batch === label;
        });

        return row ? row.id : null;
    }

    function getCategoryIdByName(name) {
        const row = RESOURCE_CONFIGS.categories.rows.find(function(category) {
            return category.name === name;
        });

        return row ? row.id : null;
    }

    function parseSemesterValue(value) {
        const match = String(value || "").match(/\d+/);
        return match ? Number(match[0]) : value;
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

    async function confirmResourceDelete() {
        if (!pendingDeleteState) {
            return;
        }

        const state = pendingDeleteState;
        const resourcePage = document.body.dataset.resourcePage;

        setButtonBusy(confirmationModalElements.confirmButton, true, "Deleting...");

        try {
            await deleteResourceRow(resourcePage, state.config.rows[state.rowIndex]);
            await loadResourceDataFromAPI();
            refreshResourceDataView(state.config, state.searchInput);
            setDashboardStatCounts();
            closeDeleteConfirmationModal();
        } catch (error) {
            alert(error.error || error.message || "Unable to delete this entry.");
        } finally {
            if (confirmationModalElements) {
                setButtonBusy(confirmationModalElements.confirmButton, false, "Confirm Delete");
            }
        }
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
            return config.columns.some(function (column) {
                return getResourceColumnText(row, column, config).toLowerCase().includes(value);
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

        const facultyRow = RESOURCE_CONFIGS.faculty.rows.find(function (row) {
            return row.facultyId === values.faculty;
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
            studentsEnrolled: values.studentsEnrolled,
            facultyCode: values.faculty,
            faculty: facultyRow ? facultyRow.name : values.faculty,
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
                    batchId: selection.batchId,
                    category: selection.category,
                    categoryId: selection.categoryId,
                    mappingId: selection.mappingId,
                    studentsEnrolled: selection.studentsEnrolled || "1"
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
        if (row.faculty) {
            return row.faculty;
        }

        const scheduleEntry = MASTER_TIMETABLE_TEMPLATE.find(function (entry) {
            return entry.course === row.name;
        });

        return scheduleEntry ? scheduleEntry.faculty : "";
    }

    function findFacultyCodeForCourse(row) {
        if (row.facultyCode) {
            return row.facultyCode;
        }

        const facultyName = findFacultyForCourse(row);
        const facultyRow = RESOURCE_CONFIGS.faculty.rows.find(function (entry) {
            return entry.name === facultyName || entry.facultyId === facultyName;
        });

        return facultyRow ? facultyRow.facultyId : "";
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
                            return "<td>" + formatTableCell(getResourceColumnValue(row, column, config), column) + "</td>";
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
            const currentGeneration = getStoredGeneration();
            if (!currentGeneration) { return; }
            const currentView = getStoredValue(STORAGE_KEYS.selectedView, "overall");
            const url = (API.downloadUrls && API.downloadUrls[currentView]) || API.downloadUrl;
            window.location.href = url;
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

    function setDashboardStatCounts() {
        setText("courseCount", RESOURCE_CONFIGS.courses.rows.length);
        setText("facultyCount", RESOURCE_CONFIGS.faculty.rows.length);
        setText("roomCount", RESOURCE_CONFIGS.rooms.rows.length);
        setText("batchCount", RESOURCE_CONFIGS.batches.rows.length);
        setText("categoryCount", RESOURCE_CONFIGS.categories.rows.length);
        setText("slotCount", RESOURCE_CONFIGS.slots.rows.length);
    }

    function renderConflictReportList(container, conflicts) {
        if (!container) {
            return;
        }

        if (!Array.isArray(conflicts) || !conflicts.length) {
            container.innerHTML = '<p class="muted-copy conflict-empty">No unresolved course, faculty, room, or slot conflicts in the latest run.</p>';
            return;
        }

        container.innerHTML = conflicts
            .map(function (conflict) {
                const title = conflict.title || conflict.courseName || "Conflict";
                const badge = conflict.badge || conflict.courseCode || "Issue";
                const meta = conflict.meta || buildLegacyConflictMeta(conflict);
                const reason = conflict.reason || "Conflict details are unavailable.";

                return (
                    '<article class="conflict-item">' +
                    '<div class="conflict-item-top">' +
                    "<h4>" +
                    escapeHtml(title) +
                    "</h4>" +
                    '<span class="table-pill">' +
                    escapeHtml(badge) +
                    "</span>" +
                    "</div>" +
                    (meta ? '<p class="conflict-meta">' + escapeHtml(meta) + "</p>" : "") +
                    "<p>" +
                    escapeHtml(reason) +
                    "</p>" +
                    "</article>"
                );
            })
            .join("");
    }

    function buildLegacyConflictMeta(conflict) {
        const facultyLabel = conflict.facultyCode || "Unassigned";
        const batchLabel = conflict.batchLabel || "Not mapped";

        return "Batch: " + batchLabel + " | Faculty: " + facultyLabel;
    }

    function createGenerationPayload() {
        const schedule = MASTER_TIMETABLE_TEMPLATE.slice().sort(compareScheduleEntries);

        return {
            generatedAt: new Date().toISOString(),
            report: buildGenerationReport(schedule),
            schedule: schedule
        };
    }

    function buildGenerationReport(schedule) {
        const courseRows = RESOURCE_CONFIGS.courses.rows;
        const courseConflicts = courseRows.reduce(function (result, row) {
            const scheduledEntries = schedule.filter(function (entry) {
                return entry.course === row.name;
            });
            const facultyLabel = String(row.faculty || findFacultyForCourse(row) || "").trim();
            const batchSelections = normalizeCourseBatchCategories(row);
            const batchLabel = getConflictBatchLabel(row, batchSelections, scheduledEntries);
            const requiredSessions = getRequiredSessionsForCourse(row);

            if (!facultyLabel) {
                result.push({
                    courseCode: row.code || "N/A",
                    courseName: row.name || "Unnamed Course",
                    batchLabel: batchLabel,
                    facultyCode: "",
                    reason: "No faculty mapping is available for this course, so conflict-free placement could not be confirmed."
                });
                return result;
            }

            if (!batchSelections.length) {
                result.push({
                    courseCode: row.code || "N/A",
                    courseName: row.name || "Unnamed Course",
                    batchLabel: batchLabel,
                    facultyCode: facultyLabel,
                    reason: "The course is not mapped to any batch yet, so the scheduler has no valid batch context for placement."
                });
                return result;
            }

            if (scheduledEntries.length < requiredSessions) {
                result.push({
                    courseCode: row.code || "N/A",
                    courseName: row.name || "Unnamed Course",
                    batchLabel: batchLabel,
                    facultyCode: facultyLabel,
                    reason: buildCourseConflictReason(row, scheduledEntries.length, requiredSessions)
                });
            }

            return result;
        }, []);
        const facultyConflicts = buildScheduleOverlapConflicts(schedule, "faculty");
        const roomConflicts = buildScheduleOverlapConflicts(schedule, "room");
        const slotConflicts = buildScheduleOverlapConflicts(schedule, "batch");
        const configuredCourseNames = new Set(courseRows.map(function (row) {
            return row.name;
        }));
        const conflictedCourseNames = new Set(
            courseConflicts
                .map(function (conflict) {
                    return conflict.courseName;
                })
                .filter(Boolean)
        );

        [facultyConflicts, roomConflicts, slotConflicts].forEach(function (conflicts) {
            conflicts.forEach(function (conflict) {
                (conflict.entries || []).forEach(function (entry) {
                    if (configuredCourseNames.has(entry.course)) {
                        conflictedCourseNames.add(entry.course);
                    }
                });
            });
        });

        const totalCourses = courseRows.length;
        const coursesScheduled = Math.max(totalCourses - conflictedCourseNames.size, 0);
        const totalIssues = courseConflicts.length + facultyConflicts.length + roomConflicts.length + slotConflicts.length;
        const courseUsageNote = totalIssues
            ? coursesScheduled + " of " + totalCourses + " configured courses are placed in the timetable without course, faculty, room, or slot conflicts."
            : "All " + totalCourses + " configured courses are placed in the timetable without course, faculty, room, or slot conflicts.";

        return {
            totalCourses: totalCourses,
            coursesScheduled: coursesScheduled,
            courseUsageNote: courseUsageNote,
            courseClashes: courseConflicts.length,
            facultyClashes: facultyConflicts.length,
            roomConflicts: roomConflicts.length,
            slotConflicts: slotConflicts.length,
            courseNote: courseConflicts.length
                ? formatIssueCount(courseConflicts.length, "course placement issue") + (courseConflicts.length === 1 ? " still needs attention." : " still need attention.")
                : "No unresolved course placement issues in the latest run.",
            facultyNote: buildScheduleConflictNote(facultyConflicts.length, "faculty overlap", "No faculty overlaps in the latest run."),
            roomNote: buildScheduleConflictNote(roomConflicts.length, "room conflict", "No room conflicts in the latest run."),
            slotNote: buildScheduleConflictNote(slotConflicts.length, "slot conflict", "No slot conflicts in the latest run."),
            conflictSummary: totalIssues
                ? formatIssueCount(totalIssues, "issue") + " detected across course placement, faculty, room, and slot checks."
                : "No unresolved course, faculty, room, or slot conflicts in the latest run.",
            conflicts: courseConflicts.concat(roomConflicts, slotConflicts, facultyConflicts),
            totalIssues: totalIssues
        };
    }

    function buildScheduleConflictNote(count, label, emptyText) {
        if (!count) {
            return emptyText;
        }

        return formatIssueCount(count, label) + " detected in the latest run.";
    }

    function formatIssueCount(count, label) {
        return count + " " + label + (count === 1 ? "" : "s");
    }

    function buildScheduleOverlapConflicts(schedule, resourceKey) {
        const groups = {};
        const conflicts = [];

        schedule.forEach(function (entry) {
            const resourceValue = String(entry[resourceKey] || "").trim();
            const dayValue = String(entry.day || "").trim();

            if (!resourceValue || !dayValue) {
                return;
            }

            const groupKey = dayValue + "::" + resourceValue;

            if (!groups[groupKey]) {
                groups[groupKey] = [];
            }

            groups[groupKey].push(entry);
        });

        Object.keys(groups).forEach(function (groupKey) {
            const entries = groups[groupKey].slice().sort(compareEntriesByStartTime);

            for (let index = 0; index < entries.length; index += 1) {
                for (let nextIndex = index + 1; nextIndex < entries.length; nextIndex += 1) {
                    const currentEntry = entries[index];
                    const nextEntry = entries[nextIndex];

                    if (!scheduleEntriesOverlap(currentEntry, nextEntry)) {
                        if (getEntryTimeRange(nextEntry).start >= getEntryTimeRange(currentEntry).end) {
                            break;
                        }

                        continue;
                    }

                    conflicts.push(createScheduleConflictRecord(resourceKey, currentEntry, nextEntry));
                }
            }
        });

        return conflicts;
    }

    function compareEntriesByStartTime(a, b) {
        const dayDifference = DAYS.indexOf(a.day) - DAYS.indexOf(b.day);

        if (dayDifference !== 0) {
            return dayDifference;
        }

        return getEntryTimeRange(a).start - getEntryTimeRange(b).start;
    }

    function getEntryTimeRange(entry) {
        const slotParts = String(entry.slot || "").split(/\s*-\s*/);
        const start = timeToMinutes(slotParts[0]);
        const end = timeToMinutes(slotParts[1]);

        if (end > start) {
            return {
                start: start,
                end: end
            };
        }

        const slotRow = RESOURCE_CONFIGS.slots.rows.find(function (row) {
            return row.time === entry.slot;
        });

        if (slotRow) {
            const fallbackParts = String(slotRow.time || "").split(/\s*-\s*/);
            const fallbackStart = timeToMinutes(fallbackParts[0]);
            const fallbackEnd = timeToMinutes(fallbackParts[1]);

            return {
                start: fallbackStart,
                end: fallbackEnd
            };
        }

        return {
            start: start,
            end: start
        };
    }

    function scheduleEntriesOverlap(firstEntry, secondEntry) {
        const firstRange = getEntryTimeRange(firstEntry);
        const secondRange = getEntryTimeRange(secondEntry);

        if (firstRange.end <= firstRange.start || secondRange.end <= secondRange.start) {
            return firstEntry.slot === secondEntry.slot;
        }

        return firstRange.start < secondRange.end && secondRange.start < firstRange.end;
    }

    function createScheduleConflictRecord(resourceKey, firstEntry, secondEntry) {
        const config = getScheduleConflictConfig(resourceKey);
        const resourceValue = firstEntry[resourceKey] || secondEntry[resourceKey] || config.fallbackLabel;

        return {
            type: resourceKey,
            title: config.titlePrefix + " " + resourceValue,
            badge: config.badge,
            meta: buildScheduleConflictMeta(firstEntry, secondEntry, resourceValue, config),
            reason: buildScheduleConflictReason(resourceKey, firstEntry, secondEntry, resourceValue),
            entries: [firstEntry, secondEntry]
        };
    }

    function getScheduleConflictConfig(resourceKey) {
        if (resourceKey === "room") {
            return {
                badge: "Room",
                titlePrefix: "Room conflict in",
                fallbackLabel: "room",
                entityLabel: "Room"
            };
        }

        if (resourceKey === "faculty") {
            return {
                badge: "Faculty",
                titlePrefix: "Faculty clash for",
                fallbackLabel: "faculty",
                entityLabel: "Faculty"
            };
        }

        return {
            badge: "Slot",
            titlePrefix: "Slot conflict for",
            fallbackLabel: "batch",
            entityLabel: "Batch"
        };
    }

    function buildScheduleConflictMeta(firstEntry, secondEntry, resourceValue, config) {
        const windows = Array.from(new Set([firstEntry.slot, secondEntry.slot].filter(Boolean))).join(" and ");

        return firstEntry.day + " | " + config.entityLabel + ": " + resourceValue + " | " + windows;
    }

    function buildScheduleConflictReason(resourceKey, firstEntry, secondEntry, resourceValue) {
        if (resourceKey === "room") {
            return firstEntry.course + " (" + firstEntry.batch + ") and " + secondEntry.course + " (" + secondEntry.batch + ") overlap in room " + resourceValue + ".";
        }

        if (resourceKey === "faculty") {
            return firstEntry.course + " and " + secondEntry.course + " overlap for faculty member " + resourceValue + ".";
        }

        return firstEntry.course + " and " + secondEntry.course + " overlap in the same batch slot for " + resourceValue + ".";
    }

    function getConflictBatchLabel(row, batchSelections, scheduledEntries) {
        const labels = batchSelections.length
            ? batchSelections.map(function (selection) {
                return selection.batch;
            })
            : scheduledEntries.map(function (entry) {
                return entry.batch;
            });
        const uniqueLabels = Array.from(new Set(labels.filter(Boolean)));

        if (uniqueLabels.length) {
            return uniqueLabels.join(", ");
        }

        return row.semester || "Not mapped";
    }

    function getRequiredSessionsForCourse(row) {
        const lectureHours = parseNumericValue(row.lectureHours);
        const explicitSessions = lectureHours;

        if (explicitSessions > 0) {
            return explicitSessions;
        }

        return getCourseCategoryText(row).includes("lab") ? 1 : 3;
    }

    function parseNumericValue(value) {
        const normalized = String(value || "").replace(/[^0-9.]/g, "");
        const parsedValue = Number.parseFloat(normalized);

        return Number.isFinite(parsedValue) ? parsedValue : 0;
    }

    function getCourseCategoryText(row) {
        const selectionLabels = normalizeCourseBatchCategories(row).map(function (selection) {
            return selection.category;
        });

        return [row.category]
            .concat(selectionLabels)
            .filter(Boolean)
            .join(" ")
            .toLowerCase();
    }

    function buildCourseConflictReason(row, scheduledCount, requiredSessions) {
        const isLabCourse = getCourseCategoryText(row).includes("lab");

        if (scheduledCount === 0) {
            return isLabCourse
                ? "No compatible lab block could be placed. The required lab windows still conflict with the current room and slot availability."
                : "No compatible lecture slot could be placed. The required teaching windows still conflict with the current batch, faculty, and slot availability.";
        }

        return isLabCourse
            ? "Only " + scheduledCount + " of " + requiredSessions + " required lab block(s) could be placed. The remaining block(s) still conflict with the current lab-room and long-slot availability."
            : "Only " + scheduledCount + " of " + requiredSessions + " required session(s) could be placed. The remaining session(s) still conflict with the current batch, faculty, and slot availability.";
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
            window.location.href = "/login";
        });
    }

    function getStoredGeneration() {
        return latestGeneration;
    }

    function storeGeneration(payload) {
        latestGeneration = payload || null;
        MASTER_TIMETABLE_TEMPLATE = latestGeneration && Array.isArray(latestGeneration.schedule)
            ? latestGeneration.schedule.slice()
            : [];
        saveStoredValue(STORAGE_KEYS.selectedView, "overall");
    }

    function clearStoredGeneration() {
        latestGeneration = null;
        MASTER_TIMETABLE_TEMPLATE = [];
        try {
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

    function buildApiErrorMessage(payload, fallback) {
        const baseMessage = payload && (payload.error || payload.message)
            ? String(payload.error || payload.message)
            : fallback;
        const details = payload && Array.isArray(payload.errors)
            ? payload.errors.filter(Boolean)
            : [];

        if (!details.length) {
            return baseMessage;
        }

        return baseMessage + "\n\n" + details.map(function (detail, index) {
            return (index + 1) + ". " + detail;
        }).join("\n");
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

        return date.toLocaleString("en-IN", {
            timeZone: "Asia/Kolkata",
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
            hour12: true
        });
    }

    function getResourceColumnValue(row, column, config) {
        if (config === RESOURCE_CONFIGS.courses) {
            if (column.key === "lectureHours") {
                return row.lectureHours || inferCourseHourValue(row, "lecture");
            }

            if (column.key === "tutorialHours") {
                return row.tutorialHours || "0";
            }

            if (column.key === "labHours") {
                return row.labHours || inferCourseHourValue(row, "lab");
            }

            if (column.key === "batchCategories") {
                return normalizeCourseBatchCategories(row);
            }

            if (column.key === "studentsEnrolled") {
                const value = Number(row.studentsEnrolled || 0);
                if (value > 0) {
                    return String(value);
                }
                const mappings = normalizeCourseBatchCategories(row);
                return String(mappings.length ? Number(mappings[0].studentsEnrolled || 1) : 1);
            }

            if (column.key === "faculty") {
                return row.faculty || findFacultyForCourse(row) || "";
            }
        }

        return row[column.key];
    }

    function getResourceColumnText(row, column, config) {
        const value = getResourceColumnValue(row, column, config);

        if (Array.isArray(value)) {
            return value
                .map(function (item) {
                    if (item && typeof item === "object") {
                        if (item.batch && item.category) {
                            return item.batch + " - " + item.category;
                        }

                        return Object.values(item).filter(Boolean).join(" ");
                    }

                    return String(item || "");
                })
                .join(", ");
        }

        if (value && typeof value === "object") {
            return Object.values(value).filter(Boolean).join(" ");
        }

        return String(value || "");
    }

    function formatTableCell(value, column) {
        if (column && column.key === "batchCategories") {
            let items = [];
            if (typeof value === "string") {
                items = value.split(",").map(function(s) { return s.trim(); }).filter(Boolean);
            } else if (Array.isArray(value)) {
                items = value.map(function(item) {
                    if (item && item.batch && item.category) {
                        return item.batch + " - " + item.category;
                    }
                    return getDisplayValueText([item]);
                });
            } else {
                items = getDisplayValueText(value).split(",").map(function(s) { return s.trim(); }).filter(Boolean);
            }

            if (items.length > 0) {
                return '<div class="batch-categories-wrapper">' + items.map(function(item) {
                    let parts = item.split("-");
                    let text = escapeHtml(item);
                    if (parts.length > 1) {
                         const batch = parts[0].trim();
                         const cat = parts.slice(1).join("-").trim();
                         text = '<strong>' + escapeHtml(batch) + '</strong><span class="batch-separator"> - </span><span class="batch-category-light">' + escapeHtml(cat) + '</span>';
                    } else {
                         parts = item.split(":");
                         if (parts.length > 1) {
                              const batch = parts[0].trim();
                              const cat = parts.slice(1).join(":").trim();
                              text = '<strong>' + escapeHtml(batch) + '</strong><span class="batch-separator"> : </span><span class="batch-category-light">' + escapeHtml(cat) + '</span>';
                         } else {
                              text = '<strong>' + escapeHtml(item) + '</strong>';
                         }
                    }
                    return '<span class="batch-category-badge">' + text + '</span>';
                }).join("") + '</div>';
            }
        }

        const badgeType = column && column.badge ? column.badge : (typeof column === "string" ? column : null);
        const safeValue = escapeHtml(getDisplayValueText(value));

        if (!badgeType) {
            return safeValue;
        }

        const className = badgeType === "secondary" ? "table-pill is-secondary" : "table-pill";
        return '<span class="' + className + '">' + safeValue + "</span>";
    }

    function getDisplayValueText(value) {
        if (Array.isArray(value)) {
            return value
                .map(function (item) {
                    if (item && typeof item === "object") {
                        if (item.batch && item.category) {
                            return item.batch + " - " + item.category;
                        }

                        return Object.values(item).filter(Boolean).join(" ");
                    }

                    return String(item || "");
                })
                .join(", ");
        }

        if (value && typeof value === "object") {
            return Object.values(value).filter(Boolean).join(" ");
        }

        return String(value || "");
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

    async function setupUsersPage() {
        if (document.body.dataset.page !== "users") {
            return;
        }

        const user = await loadCurrentUser();
        if (!user || user.username !== "admin") {
            window.location.href = "/dashboard";
            return;
        }

        await loadAndRenderUsersList();
    }

    async function loadAndRenderUsersList() {
        const tableBody = document.querySelector("[data-resource-body]");
        const tableHead = document.querySelector("[data-resource-head]");
        const emptyState = document.getElementById("resourceEmptyState");
        const countValueEl = document.getElementById("usersCountValue");

        if (!tableBody || !tableHead) return;

        tableHead.innerHTML = `
            <tr>
                <th>User ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Created At</th>
                <th>Actions</th>
            </tr>
        `;

        try {
            const users = await API.listUsers();
            
            if (countValueEl) {
                countValueEl.textContent = users.length;
            }

            if (!users || users.length === 0) {
                tableBody.innerHTML = "";
                if (emptyState) emptyState.classList.remove("is-hidden");
                return;
            }

            if (emptyState) emptyState.classList.add("is-hidden");

            tableBody.innerHTML = users.map(function (u) {
                const isMaster = u.username === "admin";
                const deleteBtn = isMaster
                    ? `<span style="font-size: 0.8rem; padding: 0.25rem 0.5rem; background: var(--border); border-radius: 4px; color: var(--text-muted);">System</span>`
                    : `<button class="btn-delete-user btn-danger" data-user-id="${u.user_id}" data-username="${u.username}" type="button" style="padding: 0.35rem 0.75rem; border: none; background: #dc3545; color: white; border-radius: 4px; cursor: pointer; font-size: 0.85rem;">Delete</button>`;
                
                return `
                    <tr>
                        <td>${u.user_id}</td>
                        <td style="font-weight: 600;">${escapeHtml(u.username)}</td>
                        <td>${escapeHtml(u.email)}</td>
                        <td>${escapeHtml(u.created_at.split('.')[0])}</td>
                        <td>${deleteBtn}</td>
                    </tr>
                `;
            }).join("");

            tableBody.querySelectorAll(".btn-delete-user").forEach(function (btn) {
                btn.addEventListener("click", async function (e) {
                    const userId = btn.dataset.userId;
                    const username = btn.dataset.username;
                    if (confirm(`Are you sure you want to delete user "${username}"?`)) {
                        try {
                            btn.disabled = true;
                            btn.textContent = "Deleting...";
                            await API.deleteUser(userId);
                            await loadAndRenderUsersList();
                        } catch (err) {
                            alert(err.error || "Failed to delete user.");
                            btn.disabled = false;
                            btn.textContent = "Delete";
                        }
                    }
                });
            });

        } catch (err) {
            console.error("Failed to load users", err);
            tableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: red;">Failed to load users: ${err.error || 'Server error'}</td></tr>`;
        }
    }
})();
