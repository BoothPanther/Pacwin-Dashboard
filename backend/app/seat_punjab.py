from database import engine
from models import State
from sqlalchemy.orm import Session


def seed_punjab():
    with Session(engine) as session:
        existing_state = session.query(State).filter_by(code="PB").first()

        if existing_state:
            print("Punjab already exists.")
            return

        punjab = State(
            name="Punjab",
            code="PB"
        )

        session.add(punjab)
        session.commit()

        print("Punjab added successfully.")


if __name__ == "__main__":
    seed_punjab()