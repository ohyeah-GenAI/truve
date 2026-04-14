import math
from typing import Any, Dict


class PuzzleValidator:
    """퍼즐 정답 검증 모듈."""

    SLIDER_TOLERANCE = 10  # pixels

    def validate(
        self,
        puzzle_type: str,
        correct_answer: Dict[str, Any],
        user_answer: Dict[str, Any],
    ) -> bool:
        if puzzle_type == "slider":
            return self._validate_slider(correct_answer, user_answer)
        elif puzzle_type == "dragdrop":
            return self._validate_dragdrop(correct_answer, user_answer)
        elif puzzle_type == "rotate":
            return self._validate_rotate(correct_answer, user_answer)
        elif puzzle_type == "dragdrop_easy":
            return self._validate_dragdrop(correct_answer, user_answer)
        elif puzzle_type == "clickseq":
            return self._validate_clickseq(correct_answer, user_answer)
        elif puzzle_type == "pathtrace":
            return self._validate_pathtrace(correct_answer, user_answer)
        elif puzzle_type == "pathtrace_v2":
            return self._validate_pathtrace(correct_answer, user_answer)
        return False

    def _validate_slider(self, correct: dict, user: dict) -> bool:
        user_x = user.get("offset_x")
        correct_x = correct.get("offset_x")
        if user_x is None or correct_x is None:
            return False
        return abs(float(user_x) - float(correct_x)) <= self.SLIDER_TOLERANCE

    def _validate_dragdrop(self, correct: dict, user: dict) -> bool:
        return user.get("positions") == correct.get("positions")

    def _validate_rotate(self, correct: dict, user: dict) -> bool:
        user_angles = user.get("angles", [])
        correct_angles = correct.get("angles", [])
        if len(user_angles) != len(correct_angles):
            return False
        return all(
            int(u) % 360 == int(c) % 360
            for u, c in zip(user_angles, correct_angles)
        )

    def _validate_clickseq(self, correct: dict, user: dict) -> bool:
        return user.get("sequence") == correct.get("sequence")

    def _validate_pathtrace(self, correct: dict, user: dict) -> bool:
        checkpoints = correct.get("checkpoints", [])
        user_points = user.get("points", [])
        if not checkpoints or not user_points:
            return False

        tolerance = float(correct.get("tolerance", 18))
        min_coverage = float(correct.get("min_coverage", 0.8))

        def has_near_point(cp: dict) -> bool:
            try:
                cx = float(cp.get("x", 0))
                cy = float(cp.get("y", 0))
            except (TypeError, ValueError, AttributeError):
                return False

            for p in user_points:
                try:
                    px = float(p.get("x", 0))
                    py = float(p.get("y", 0))
                except (TypeError, ValueError, AttributeError):
                    continue
                if math.hypot(px - cx, py - cy) <= tolerance:
                    return True
            return False

        hit_count = sum(1 for cp in checkpoints if has_near_point(cp))
        coverage = hit_count / len(checkpoints)

        # 시작점/끝점을 모두 지나갔는지 추가 확인
        start_ok = has_near_point(checkpoints[0])
        end_ok = has_near_point(checkpoints[-1])
        return coverage >= min_coverage and start_ok and end_ok
