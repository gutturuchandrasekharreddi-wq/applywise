"""Load a small, clearly fictional dataset to preview the dashboard."""

from datetime import date, timedelta

from .database import connect
from .models import create


def main() -> None:
    """Insert demo applications once, preserving any existing user data."""
    with connect() as db:
        if db.execute("SELECT id FROM applications LIMIT 1").fetchone() is not None:
            print("ApplyWise already has applications; demo data was not added.")
            return

        today = date.today()
        examples = [
            {"company": "Northstar Labs", "role": "Backend Engineer", "status": "applied", "location": "Remote", "source": "Referral", "applied_on": today - timedelta(days=5), "follow_up_on": today, "notes": "Interested in their developer platform."},
            {"company": "Studio Field", "role": "Product Engineer", "status": "interview", "location": "Bengaluru", "source": "Company site", "applied_on": today - timedelta(days=12), "follow_up_on": today + timedelta(days=3), "notes": "Hiring manager conversation went well."},
            {"company": "Pinecone Works", "role": "Python Developer", "status": "saved", "location": "Remote", "source": "LinkedIn", "notes": "Tailor project examples before applying."},
            {"company": "Atlas Metrics", "role": "Data Engineer", "status": "applied", "location": "Hybrid", "source": "Referral", "applied_on": today - timedelta(days=8), "follow_up_on": today - timedelta(days=1)},
            {"company": "Goodwell Health", "role": "Software Engineer", "status": "offer", "location": "Remote", "source": "Company site", "applied_on": today - timedelta(days=28), "notes": "Review role scope and benefits."},
            {"company": "Daybreak Systems", "role": "Platform Engineer", "status": "rejected", "location": "Remote", "source": "Careers page", "applied_on": today - timedelta(days=19)},
        ]
        for example in examples:
            create(db, example)
        print(f"Added {len(examples)} fictional demo applications.")


if __name__ == "__main__":
    main()
