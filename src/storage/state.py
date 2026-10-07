import os
import pickle


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

SAVE_FILE = os.path.join(
    BASE_DIR,
    "data",
    ".saved_session.pkl"
)


# الأشياء اللي نبي نحفظها بعد الـ Refresh
KEYS_TO_SAVE = [
    "df",
    "name",
    "detections",
    "config",
    "config_profile",
    "profile",
    "result",
    "report_md",
    "nav",
]


def save_state(session_state):
    """Save the important Streamlit state locally."""

    data = {}

    for key in KEYS_TO_SAVE:
        if key in session_state:
            data[key] = session_state[key]

    with open(SAVE_FILE, "wb") as file:
        pickle.dump(data, file)


def load_state(session_state):
    """Restore the previous saved state."""

    if not os.path.exists(SAVE_FILE):
        return False

    try:
        with open(SAVE_FILE, "rb") as file:
            data = pickle.load(file)

        for key, value in data.items():
            if key not in session_state:
                session_state[key] = value

        return True

    except Exception:
        return False


def clear_state():
    """Delete the saved state."""

    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)