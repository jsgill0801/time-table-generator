"""
Category model.

Categories group courses by type, such as "Core",
"Science Elective", "Technical Elective", etc.

Used for the soft constraint: same-category courses
should be scheduled in the same slot names.
"""

from sqlalchemy import Column, Integer, String, ForeignKey

from backend.db import Base


class Category(Base):
    __tablename__ = "category"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id", ondelete="CASCADE"), nullable=True)
    category_name = Column(String(30), nullable=False)

    def __repr__(self):
        return f"<Category {self.category_name}>"

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
        }
