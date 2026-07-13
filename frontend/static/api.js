/**
 * API helper layer — all backend communication goes through here.
 * Every function returns a Promise.
 */
const API = (function () {
    const BASE = window.API_BASE_URL || "/api/v1";
    const JSON_HEADERS = { "Content-Type": "application/json" };
    const CRED = "include";

    async function req(method, path, body) {
        const opts = { method, credentials: CRED, headers: { ...JSON_HEADERS }, cache: "no-store" };
        if (body !== undefined) opts.body = JSON.stringify(body);
        const finalPath = method === "GET"
            ? (BASE + path + (path.includes("?") ? "&" : "?") + "_ts=" + Date.now())
            : (BASE + path);
        const r = await fetch(finalPath, opts);
        if (r.status === 401) { window.location.href = "/login"; return; }
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw { status: r.status, ...data };
        return data;
    }

    async function upload(path, formData) {
        const r = await fetch(BASE + path, { method: "POST", credentials: CRED, body: formData, cache: "no-store" });
        if (r.status === 401) { window.location.href = "/login"; return; }
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw { status: r.status, ...data };
        return data;
    }

    return {
        // Auth
        login: (u, p) => req("POST", "/auth/login", { username: u, password: p }),
        signup: (u, e, p, m) => req("POST", "/auth/signup", { username: u, email: e, password: p, masterAdminPassword: m }),
        logout: () => req("POST", "/auth/logout"),
        me: () => req("GET", "/auth/me"),
        listUsers: () => req("GET", "/auth/users"),
        deleteUser: id => req("DELETE", "/auth/users/" + id),

        // CRUD — courses
        listCourses: () => req("GET", "/courses/"),
        createCourse: d => req("POST", "/courses/", d),
        updateCourse: (id, d) => req("PUT", "/courses/" + id, d),
        deleteCourse: id => req("DELETE", "/courses/" + id),

        // CRUD — batches
        listBatches: () => req("GET", "/batches/"),
        createBatch: d => req("POST", "/batches/", d),
        updateBatch: (id, d) => req("PUT", "/batches/" + id, d),
        deleteBatch: id => req("DELETE", "/batches/" + id),

        // CRUD — faculty
        listFaculty: () => req("GET", "/faculties/"),
        createFaculty: d => req("POST", "/faculties/", d),
        updateFaculty: (code, d) => req("PUT", "/faculties/" + encodeURIComponent(code), d),
        deleteFaculty: code => req("DELETE", "/faculties/" + encodeURIComponent(code)),

        // CRUD — classrooms
        listClassrooms: () => req("GET", "/classrooms/"),
        createClassroom: d => req("POST", "/classrooms/", d),
        updateClassroom: (name, d) => req("PUT", "/classrooms/" + encodeURIComponent(name), d),
        deleteClassroom: name => req("DELETE", "/classrooms/" + encodeURIComponent(name)),

        // CRUD — slots
        listSlots: () => req("GET", "/slots/"),
        createSlot: d => req("POST", "/slots/", d),
        updateSlot: (id, d) => req("PUT", "/slots/" + encodeURIComponent(id), d),
        deleteSlot: id => req("DELETE", "/slots/" + encodeURIComponent(id)),

        // CRUD — categories
        listCategories: () => req("GET", "/categories/"),
        createCategory: d => req("POST", "/categories/", d),
        updateCategory: (id, d) => req("PUT", "/categories/" + id, d),
        deleteCategory: id => req("DELETE", "/categories/" + id),

        // Mappings
        listBatchCourses: () => req("GET", "/batch-courses/"),
        createBatchCourse: d => req("POST", "/batch-courses/", d),
        updateBatchCourse: (id, d) => req("PUT", "/batch-courses/" + id, d),
        deleteBatchCourse: id => req("DELETE", "/batch-courses/" + id),
        listFacultyCourses: () => req("GET", "/faculty-courses/"),
        createFacultyCourse: d => req("POST", "/faculty-courses/", d),
        deleteFacultyCourse: id => req("DELETE", "/faculty-courses/" + id),

        // Data
        counts: () => req("GET", "/data/counts"),
        clearTimetable: () => req("DELETE", "/data/timetable"),
        bootstrapAdminDemo: () => req("POST", "/data/bootstrap-admin-demo"),

        // CSV import
        importCSV: (entity, formData) => upload("/import/" + entity, formData),

        // Generate
        generate: () => req("POST", "/generate/"),
        conflicts: () => req("GET", "/generate/conflicts"),
        timetable: () => req("GET", "/timetable/"),
        timetableSummary: () => req("GET", "/timetable/summary"),

        // Export — four separate download endpoints
        downloadUrls: {
            overall: BASE + "/export/download/overall",
            faculty: BASE + "/export/download/faculty",
            batches: BASE + "/export/download/batch",
            rooms: BASE + "/export/download/room",
        },
        downloadUrl: BASE + "/export/download/overall",
        preview: () => req("GET", "/export/preview"),
    };
})();
