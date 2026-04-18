function generateTimetable() {

    // Get selected type
    const type = document.getElementById("type").value;

    let selectedValue = "";

    if (type === "faculty") {
        selectedValue = document.getElementById("facultySelect").value;
    } 
    else if (type === "batch") {
        selectedValue = document.getElementById("batchSelect").value;
    } 
    else if (type === "room") {
        selectedValue = document.getElementById("roomSelect").value;
    }

    console.log("Generating:", type, selectedValue);

    // ---------------- MOCK DATA (GRID FORMAT) ----------------
    // Later → replace this with backend API response

    const data = {
        "09:00-10:00": {
            Monday: "Math (F01)\nC101",
            Tuesday: "Physics (F02)\nC102"
        },
        "10:00-11:00": {
            Monday: "Chemistry (F03)\nC103",
            Wednesday: "Biology (F04)\nC104"
        },
        "11:00-12:00": {
            Friday: "English (F05)\nC105"
        }
    };

    // ---------------- RENDER TABLE ----------------
    const tbody = document.getElementById("timetable-body");
    tbody.innerHTML = "";

    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

    Object.keys(data).forEach(time => {

        const row = document.createElement("tr");

        let rowHTML = `<td>${time}</td>`;

        days.forEach(day => {
            rowHTML += `<td>${data[time][day] || ""}</td>`;
        });

        row.innerHTML = rowHTML;
        tbody.appendChild(row);
    });

    // ---------------- CONFLICT HANDLING ----------------
    // (Simulated for now — backend will control this later)

    const hasConflict = true; // change to false to test

    const conflictBox = document.getElementById("conflictBox");
    conflictBox.style.display = hasConflict ? "block" : "none";
}