"""
Pytest configuration and shared fixtures.

Provides reusable CSV test data for all parser test modules.
"""

import pytest


# -----------------------------------------------------------------
#  Valid CSV fixtures
# -----------------------------------------------------------------

@pytest.fixture
def valid_course_csv():
    return (
        "course_code,course_name,lectures,tutorials,labs,credits\n"
        "IT205,Data Structures,3,0,0,3\n"
        "MA206,Probability and Statistics,3,1,0,4\n"
    )


@pytest.fixture
def valid_course_bundle_csv():
    return (
        "course_code,course_name,lectures,tutorials,labs,credits,batches,faculty\n"
        "IT205,Data Structures,3,0,0,3,"
        "\"BTech Sem-IV (ICT) Sec-A|Core|55;BTech Sem-IV (ICT) Sec-B|Core\","
        "PD\n"
    )


@pytest.fixture
def valid_batch_csv():
    return (
        "program,branch,semester,section\n"
        "BTech,ICT,4,A\n"
        "BTech,CS,4,\n"
    )


@pytest.fixture
def valid_faculty_csv():
    return (
        "faculty_code,faculty_name,max_load,faculty_email\n"
        "PD,Prof. Divya,12,divya@test.edu\n"
        "AV,Prof. Amit,10,\n"
    )


@pytest.fixture
def valid_classroom_csv():
    return (
        "classroom_name,capacity\n"
        "LT-1,200\n"
        "CEP108,60\n"
    )


@pytest.fixture
def valid_slot_csv():
    return (
        "slot_id,day_of_week,start_time,end_time,slot_name\n"
        "MON-0800,Monday,8:00,8:50,Slot-1\n"
        "MON-0900,Monday,9:00,9:50,Slot-5\n"
    )


@pytest.fixture
def valid_slot_csv_without_id():
    return (
        "day_of_week,start_time,end_time,slot_name\n"
        "Monday,8:00,8:50,s01\n"
        "Tuesday,9:00,9:50,s02\n"
    )


@pytest.fixture
def valid_batch_course_csv():
    return (
        "course_code,program,branch,semester,section,category,students_enrolled\n"
        "IT205,BTech,ICT,4,A,Core,55\n"
    )


@pytest.fixture
def valid_faculty_course_csv():
    return (
        "faculty_code,course_code\n"
        "PD,IT205\n"
    )
