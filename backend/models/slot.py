"""
Slot model.

A slot represents a specific (day, time-period) cell in the
weekly grid. Each slot also carries a slot_name (e.g. "Slot-1")
which is the named rotation used by the university.

The same slot_name can appear at multiple (day, time) positions.
For example, "Slot-1" might be Monday 8:00 and also Friday 9:00.
"""

from sqlalchemy import Column, String, Time, CheckConstraint

from backend.db import Base


class Slot(Base):
    __tablename__ = "slot"

    # Unique identifier for this (day, time) cell, e.g. "MON-0800"
    slot_id = Column(String(10), primary_key=True)

    day_of_week = Column(String(10), nullable=False)   # "Monday", "Tuesday", etc.
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Named slot in the rotation, e.g. "Slot-1", "Free-Slot"
    slot_name = Column(String(15), nullable=True)

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_slot_time_order"),
    )

    def __repr__(self):
        return f"<Slot {self.slot_id}: {self.day_of_week} {self.start_time}-{self.end_time}>"

    def to_dict(self):
        return {
            "slot_id": self.slot_id,
            "day_of_week": self.day_of_week,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "slot_name": self.slot_name,
        }
