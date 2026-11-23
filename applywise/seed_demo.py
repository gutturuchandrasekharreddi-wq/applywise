"""Load a small, clearly fictional dataset to preview the dashboard."""

from datetime import date, timedelta

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import Application


def main() -> None:
    """Insert demo applications once, preserving any existing user data."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(Application.id).limit(1)) is not None:
            print("ApplyWise already has applications; demo data was not added.")
            return

        today = date.today()
        examples = [
            Application(company="Northstar Labs", role="Backend Engineer", status="applied", location="Remote", source="Referral", applied_on=today - timedelta(days=5), follow_up_on=today, notes="Interested in their developer platform."),
            Application(company="Studio Field", role="Product Engineer", status="interview", location="Bengaluru", source="Company site", applied_on=today - timedelta(days=12), follow_up_on=today + timedelta(days=3), notes="Hiring manager conversation went well."),
            Application(company="Pinecone Works", role="Python Developer", status="saved", location="Remote", source="LinkedIn", notes="Tailor project examples before applying."),
            Application(company="Atlas Metrics", role="Data Engineer", status="applied", location="Hybrid", source="Referral", applied_on=today - timedelta(days=8), follow_up_on=today - timedelta(days=1)),
            Application(company="Goodwell Health", role="Software Engineer", status="offer", location="Remote", source="Company site", applied_on=today - timedelta(days=28), notes="Review role scope and benefits."),
            Application(company="Daybreak Systems", role="Platform Engineer", status="rejected", location="Remote", source="Careers page", applied_on=today - timedelta(days=19)),
        ]
        db.add_all(examples)
        db.commit()
        print(f"Added {len(examples)} fictional demo applications.")


if __name__ == "__main__":
    main()
