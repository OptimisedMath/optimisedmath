"""
End-to-End Validation Suite for OptimisedMath
=============================================
Black-box tests that launch the FastAPI backend via TestClient, then simulate
a complete user session: login → navigate → solve problems → advance levels.

Verifies that the frontend's API calls (as defined in frontend/lib/api.ts)
align with the refactored backend routes.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app, ACTIVE_SESSIONS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_sessions():
    """Ensure a clean session store for every test."""
    ACTIVE_SESSIONS.clear()
    yield
    ACTIVE_SESSIONS.clear()


@pytest.fixture()
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Health & Root
# ---------------------------------------------------------------------------


class TestHealthAndRoot:
    def test_health_check(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data


# ---------------------------------------------------------------------------
# 2. Curriculum
# ---------------------------------------------------------------------------


class TestCurriculum:
    def test_get_curriculum(self, client: TestClient):
        """Frontend calls: getCurriculum() → GET /curriculum"""
        resp = client.get("/curriculum")
        assert resp.status_code == 200
        data = resp.json()
        assert "macro_topics" in data
        assert "topics" in data
        assert len(data["macro_topics"]) > 0

        for macro in data["macro_topics"]:
            assert macro in data["topics"]
            for topic in data["topics"][macro]:
                assert "order" in topic
                assert "name" in topic
                assert "max_level" in topic

    def test_curriculum_contains_expected_macros(self, client: TestClient):
        resp = client.get("/curriculum")
        macros = resp.json()["macro_topics"]
        assert "Ułamki Zwykłe" in macros
        assert "Ułamki Dziesiętne" in macros


# ---------------------------------------------------------------------------
# 3. Session Lifecycle
# ---------------------------------------------------------------------------


class TestSessionLifecycle:
    def test_start_session(self, client: TestClient):
        """Frontend calls: startSession({username}) → POST /session/start"""
        resp = client.post(
            "/session/start",
            json={
                "username": "test_student",
            },
        )
        assert resp.status_code == 200
        state = resp.json()
        assert "session_id" in state
        assert state["username"] == "test_student"
        assert state["xp"] >= 0
        assert state["streak"] >= 0
        assert "progress" in state

    def test_start_session_with_macro(self, client: TestClient):
        resp = client.post(
            "/session/start",
            json={
                "username": "test_student",
                "selected_macro": "Ułamki Zwykłe",
            },
        )
        assert resp.status_code == 200
        state = resp.json()
        assert state["selected_macro"] == "Ułamki Zwykłe"

    def test_start_session_invalid_macro(self, client: TestClient):
        resp = client.post(
            "/session/start",
            json={
                "username": "test_student",
                "selected_macro": "NonExistent",
            },
        )
        assert resp.status_code == 400

    def test_navigate_session(self, client: TestClient):
        """Frontend calls: navigateSession({...}) → POST /session/navigate"""
        start = client.post(
            "/session/start",
            json={
                "username": "nav_student",
                "selected_macro": "Ułamki Zwykłe",
            },
        ).json()

        curriculum = client.get("/curriculum").json()
        first_topic = curriculum["topics"]["Ułamki Zwykłe"][0]

        resp = client.post(
            "/session/navigate",
            json={
                "session_id": start["session_id"],
                "selected_macro": "Ułamki Zwykłe",
                "selected_topic_order": first_topic["order"],
                "selected_level": 1,
            },
        )
        assert resp.status_code == 200
        state = resp.json()
        assert state["selected_macro"] == "Ułamki Zwykłe"
        assert state["selected_topic_order"] == first_topic["order"]
        assert state["selected_level"] == 1

    def test_navigate_nonexistent_session(self, client: TestClient):
        resp = client.post(
            "/session/navigate",
            json={
                "session_id": "nonexistent-id",
                "selected_macro": "Ułamki Zwykłe",
                "selected_topic_order": 10,
                "selected_level": 1,
            },
        )
        assert resp.status_code == 404

    def test_reset_session(self, client: TestClient):
        """Frontend calls: resetSession({session_id}) → POST /session/reset"""
        start = client.post(
            "/session/start",
            json={
                "username": "reset_student",
            },
        ).json()

        resp = client.post(
            "/session/reset",
            json={
                "session_id": start["session_id"],
            },
        )
        assert resp.status_code == 200
        state = resp.json()
        assert state["xp"] == 0
        assert state["streak"] == 0

    def test_reset_nonexistent_session(self, client: TestClient):
        resp = client.post(
            "/session/reset",
            json={
                "session_id": "nonexistent-id",
            },
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 4. Problem Flow
# ---------------------------------------------------------------------------


class TestProblemFlow:
    def _start_session(self, client: TestClient, macro: str = "Ułamki Zwykłe"):
        return client.post(
            "/session/start",
            json={
                "username": "problem_student",
                "selected_macro": macro,
            },
        ).json()

    def test_get_next_problem(self, client: TestClient):
        """Frontend calls: getNextProblem(sessionId) → GET /problem/next"""
        state = self._start_session(client)
        resp = client.get("/problem/next", params={"session_id": state["session_id"]})
        assert resp.status_code == 200
        data = resp.json()
        assert "problem" in data
        assert "state" in data
        problem = data["problem"]
        assert "question" in problem
        assert "correct" in problem
        assert "problem_id" in problem
        assert "options" in problem

    def test_get_next_problem_nonexistent_session(self, client: TestClient):
        resp = client.get("/problem/next", params={"session_id": "bad-id"})
        assert resp.status_code == 404

    def test_submit_correct_answer_radio(self, client: TestClient):
        """Frontend calls: submitAnswer({...}) → POST /problem/submit"""
        state = self._start_session(client)
        prob_resp = client.get(
            "/problem/next", params={"session_id": state["session_id"]}
        ).json()
        problem = prob_resp["problem"]
        correct_answer = problem["correct"]

        resp = client.post(
            "/problem/submit",
            json={
                "session_id": state["session_id"],
                "user_input": correct_answer,
                "is_text_mode": False,
                "problem_id": problem["problem_id"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "state" in data
        assert "is_correct" in data
        assert "feedback" in data
        assert data["is_correct"] is True
        assert data["state"]["streak"] >= 1

    def test_submit_wrong_answer_radio(self, client: TestClient):
        state = self._start_session(client)
        prob_resp = client.get(
            "/problem/next", params={"session_id": state["session_id"]}
        ).json()
        problem = prob_resp["problem"]

        wrong_options = [o for o in problem["options"] if o != problem["correct"]]
        if wrong_options:
            resp = client.post(
                "/problem/submit",
                json={
                    "session_id": state["session_id"],
                    "user_input": wrong_options[0],
                    "is_text_mode": False,
                    "problem_id": problem["problem_id"],
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_correct"] is False

    def test_submit_already_answered(self, client: TestClient):
        state = self._start_session(client)
        prob_resp = client.get(
            "/problem/next", params={"session_id": state["session_id"]}
        ).json()
        problem = prob_resp["problem"]

        client.post(
            "/problem/submit",
            json={
                "session_id": state["session_id"],
                "user_input": problem["correct"],
                "is_text_mode": False,
                "problem_id": problem["problem_id"],
            },
        )

        resp = client.post(
            "/problem/submit",
            json={
                "session_id": state["session_id"],
                "user_input": problem["correct"],
                "is_text_mode": False,
                "problem_id": problem["problem_id"],
            },
        )
        assert resp.status_code == 409

    def test_submit_nonexistent_session(self, client: TestClient):
        resp = client.post(
            "/problem/submit",
            json={
                "session_id": "bad-id",
                "user_input": "x",
                "is_text_mode": False,
            },
        )
        assert resp.status_code == 404

    def test_auto_solve(self, client: TestClient):
        """Frontend calls: autoSolve(sessionId, problemId) → POST /problem/auto-solve"""
        state = self._start_session(client)
        prob_resp = client.get(
            "/problem/next", params={"session_id": state["session_id"]}
        ).json()
        problem = prob_resp["problem"]

        resp = client.post(
            "/problem/auto-solve",
            json={
                "session_id": state["session_id"],
                "problem_id": problem["problem_id"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_correct"] is True
        assert data["state"]["streak"] >= 1

    def test_auto_solve_nonexistent_session(self, client: TestClient):
        resp = client.post(
            "/problem/auto-solve",
            json={
                "session_id": "bad-id",
            },
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 5. Full User Journey (simulates the frontend flow end-to-end)
# ---------------------------------------------------------------------------


class TestFullUserJourney:
    """Simulates the exact sequence the Next.js frontend performs:
    1. GET /curriculum
    2. POST /session/start (with preferred macro)
    3. GET /problem/next
    4. POST /problem/submit (correct answer)
    5. Repeat submit until streak triggers level advancement
    6. Verify level/topic progression
    """

    def test_login_to_level_advance(self, client: TestClient):
        # Step 1: Fetch curriculum (like GameArena.initializeGame)
        curriculum = client.get("/curriculum").json()
        assert len(curriculum["macro_topics"]) > 0
        preferred_macro = "Ułamki Zwykłe"
        assert preferred_macro in curriculum["macro_topics"]

        # Step 2: Start session (like LoginForm.handleSubmit + GameArena)
        session = client.post(
            "/session/start",
            json={
                "username": "journey_student",
                "selected_macro": preferred_macro,
            },
        ).json()
        session_id = session["session_id"]
        assert session["selected_macro"] == preferred_macro
        initial_xp = session["xp"]

        # Step 3-5: Solve problems until level advances
        # max_streak=3 means 3 consecutive correct → level up
        for i in range(3):
            prob_resp = client.get(
                "/problem/next", params={"session_id": session_id}
            ).json()
            problem = prob_resp["problem"]
            assert "correct" in problem
            assert "problem_id" in problem

            submit_resp = client.post(
                "/problem/submit",
                json={
                    "session_id": session_id,
                    "user_input": problem["correct"],
                    "is_text_mode": False,
                    "problem_id": problem["problem_id"],
                },
            ).json()
            assert submit_resp["is_correct"] is True

        # Step 6: Verify XP increased and progression happened
        final_state = submit_resp["state"]
        assert final_state["xp"] > initial_xp

        # After 3 correct, either level advanced or topic completed
        level_advanced = final_state["selected_level"] > 1
        topic_completed = final_state["topic_completed"]
        balloons = final_state["show_balloons"]
        assert level_advanced or topic_completed
        assert balloons is True

    def test_navigate_between_macros(self, client: TestClient):
        """Simulate switching between Ułamki Zwykłe and Ułamki Dziesiętne."""
        session = client.post(
            "/session/start",
            json={
                "username": "switcher",
                "selected_macro": "Ułamki Zwykłe",
            },
        ).json()
        session_id = session["session_id"]

        curriculum = client.get("/curriculum").json()
        decimal_topic = curriculum["topics"]["Ułamki Dziesiętne"][0]

        nav_resp = client.post(
            "/session/navigate",
            json={
                "session_id": session_id,
                "selected_macro": "Ułamki Dziesiętne",
                "selected_topic_order": decimal_topic["order"],
                "selected_level": 1,
            },
        )
        assert nav_resp.status_code == 200
        state = nav_resp.json()
        assert state["selected_macro"] == "Ułamki Dziesiętne"

        prob_resp = client.get("/problem/next", params={"session_id": session_id})
        assert prob_resp.status_code == 200

    def test_auto_solve_streak_to_level_up(self, client: TestClient):
        """Use auto-solve (admin feature) to rapidly advance through a level."""
        session = client.post(
            "/session/start",
            json={
                "username": "admin_tester",
                "selected_macro": "Ułamki Zwykłe",
            },
        ).json()
        session_id = session["session_id"]

        for _ in range(3):
            prob_resp = client.get(
                "/problem/next", params={"session_id": session_id}
            ).json()
            problem = prob_resp["problem"]

            solve_resp = client.post(
                "/problem/auto-solve",
                json={
                    "session_id": session_id,
                    "problem_id": problem["problem_id"],
                },
            ).json()
            assert solve_resp["is_correct"] is True

        final = solve_resp["state"]
        assert final["show_balloons"] is True
        assert final["selected_level"] > 1 or final["topic_completed"]

    def test_reset_clears_progress(self, client: TestClient):
        """Verify POST /session/reset returns user to initial state."""
        session = client.post(
            "/session/start",
            json={
                "username": "reset_tester",
                "selected_macro": "Ułamki Zwykłe",
            },
        ).json()
        session_id = session["session_id"]

        # Gain some XP first
        prob_resp = client.get(
            "/problem/next", params={"session_id": session_id}
        ).json()
        client.post(
            "/problem/submit",
            json={
                "session_id": session_id,
                "user_input": prob_resp["problem"]["correct"],
                "is_text_mode": False,
                "problem_id": prob_resp["problem"]["problem_id"],
            },
        )

        # Now reset
        reset_resp = client.post(
            "/session/reset",
            json={
                "session_id": session_id,
            },
        ).json()
        assert reset_resp["xp"] == 0
        assert reset_resp["streak"] == 0


# ---------------------------------------------------------------------------
# 6. Frontend-Backend API Path Alignment
# ---------------------------------------------------------------------------


class TestAPIPathAlignment:
    """Verifies every path used by frontend/lib/api.ts exists and responds."""

    FRONTEND_ROUTES = [
        ("GET", "/curriculum"),
        ("POST", "/session/start"),
        ("POST", "/session/navigate"),
        ("POST", "/session/reset"),
        ("GET", "/problem/next"),
        ("POST", "/problem/submit"),
        ("POST", "/problem/auto-solve"),
    ]

    def test_all_frontend_routes_exist(self, client: TestClient):
        """Ensure no 405 (method not allowed) for any route the frontend expects.

        Some routes return 404 for missing sessions or 422 for missing body
        fields, which is expected — we only care that the *route* is registered.
        """
        for method, path in self.FRONTEND_ROUTES:
            if method == "GET":
                if path == "/problem/next":
                    resp = client.get(path, params={"session_id": "probe"})
                else:
                    resp = client.get(path)
            else:
                resp = client.post(path, json={})

            # 404 for /problem/next with a fake session_id is expected
            # (route exists, session does not). 422 is fine for missing fields.
            assert (
                resp.status_code != 405
            ), f"{method} {path} returned 405 (method not allowed)"
            if path not in ("/problem/next",):
                assert (
                    resp.status_code != 404
                ), f"{method} {path} returned 404 (route not found)"

    def test_openapi_schema_available(self, client: TestClient):
        """FastAPI docs should be accessible for debugging."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        paths = list(schema.get("paths", {}).keys())
        for _, path in self.FRONTEND_ROUTES:
            assert path in paths, f"Frontend route {path} missing from OpenAPI schema"


# ---------------------------------------------------------------------------
# 7. Response Schema Validation
# ---------------------------------------------------------------------------


class TestResponseSchemas:
    """Verify response shapes match frontend/lib/types.ts interfaces."""

    def test_game_state_shape(self, client: TestClient):
        """GameState from POST /session/start matches TypeScript interface."""
        resp = client.post("/session/start", json={"username": "schema_test"})
        state = resp.json()
        expected_keys = {
            "session_id",
            "username",
            "xp",
            "streak",
            "flawless_eligible",
            "max_streak",
            "selected_macro",
            "selected_topic_order",
            "selected_level",
            "problem_answered",
            "current_input_mode",
            "topic_completed",
            "feedback_type",
            "feedback_msg",
            "show_balloons",
            "progress",
            "current_problem",
        }
        missing = expected_keys - set(state.keys())
        assert not missing, f"GameState missing keys: {missing}"

    def test_problem_response_shape(self, client: TestClient):
        """ProblemResponse from GET /problem/next matches TypeScript interface."""
        session = client.post(
            "/session/start",
            json={
                "username": "schema_problem",
                "selected_macro": "Ułamki Zwykłe",
            },
        ).json()
        resp = client.get("/problem/next", params={"session_id": session["session_id"]})
        data = resp.json()
        assert "problem" in data
        assert "state" in data
        problem = data["problem"]
        assert "question" in problem
        assert "correct" in problem
        assert "problem_id" in problem

    def test_submission_response_shape(self, client: TestClient):
        """SubmissionResponse from POST /problem/submit matches TypeScript interface."""
        session = client.post(
            "/session/start",
            json={
                "username": "schema_submit",
                "selected_macro": "Ułamki Zwykłe",
            },
        ).json()
        prob = client.get(
            "/problem/next", params={"session_id": session["session_id"]}
        ).json()
        resp = client.post(
            "/problem/submit",
            json={
                "session_id": session["session_id"],
                "user_input": prob["problem"]["correct"],
                "is_text_mode": False,
                "problem_id": prob["problem"]["problem_id"],
            },
        )
        data = resp.json()
        assert "state" in data
        assert "is_correct" in data
        assert "feedback" in data

    def test_curriculum_response_shape(self, client: TestClient):
        """CurriculumResponse matches TypeScript CurriculumResponse interface."""
        data = client.get("/curriculum").json()
        assert isinstance(data["macro_topics"], list)
        assert isinstance(data["topics"], dict)
        for macro, topics in data["topics"].items():
            assert isinstance(topics, list)
            for t in topics:
                assert isinstance(t["order"], int)
                assert isinstance(t["name"], str)
                assert isinstance(t["max_level"], int)

    def test_topic_progress_shape(self, client: TestClient):
        """TopicProgress inside GameState.progress matches TypeScript interface."""
        state = client.post(
            "/session/start", json={"username": "progress_shape"}
        ).json()
        for macro, prog in state["progress"].items():
            assert "unlocked_order" in prog
            assert "unlocked_level" in prog
            assert isinstance(prog["unlocked_order"], int)
            assert isinstance(prog["unlocked_level"], int)
