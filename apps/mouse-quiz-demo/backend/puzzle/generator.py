import base64
import math
import random
from io import BytesIO
from typing import Any, Dict, List

from PIL import Image, ImageDraw


class PuzzleGenerator:
    """
    PIL을 이용해 세 가지 퍼즐(Slider / Drag&Drop / Rotate)을 동적으로 생성한다.
    생성된 이미지는 base64 PNG로 직렬화하여 반환한다.
    """

    IMAGE_W = 300
    IMAGE_H = 150
    PIECE_W = 50
    GRID = 3
    CELL_SIZE = 100

    # ── Public ────────────────────────────────────────────────────────────
    def generate(self, puzzle_type: str) -> Dict[str, Any]:
        if puzzle_type == "slider":
            return self._gen_slider()
        elif puzzle_type == "dragdrop":
            return self._gen_dragdrop()
        elif puzzle_type == "rotate":
            return self._gen_rotate()
        elif puzzle_type == "dragdrop_easy":
            return self._gen_dragdrop_easy()
        elif puzzle_type == "clickseq":
            return self._gen_clickseq()
        elif puzzle_type == "pathtrace":
            return self._gen_pathtrace()
        elif puzzle_type == "pathtrace_v2":
            return self._gen_pathtrace_v2()
        raise ValueError(f"Unknown puzzle type: {puzzle_type}")

    # ── 이미지 생성 헬퍼 ─────────────────────────────────────────────────
    def _create_scene(self, width: int, height: int) -> Image.Image:
        """랜덤 도형으로 구성된 배경 이미지를 생성한다."""
        img = Image.new("RGB", (width, height), (245, 245, 245))
        draw = ImageDraw.Draw(img)

        # 그라디언트 효과
        for y in range(0, height, 8):
            r = min(255, 180 + y // 4)
            g = min(255, 200 + y // 8)
            b = max(150, 230 - y // 4)
            draw.rectangle([0, y, width, y + 8], fill=(r, g, b))

        # 랜덤 도형 (매 호출마다 다른 시드)
        seed = random.randint(0, 0xFFFF)
        rng = random.Random(seed)
        for _ in range(10):
            x1 = rng.randint(0, width - 30)
            y1 = rng.randint(0, height - 30)
            x2 = x1 + rng.randint(20, 70)
            y2 = y1 + rng.randint(15, 50)
            color = (rng.randint(60, 210), rng.randint(60, 210), rng.randint(60, 210))
            if rng.random() > 0.5:
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(40, 40, 40), width=1)
            else:
                draw.ellipse([x1, y1, x2, y2], fill=color, outline=(40, 40, 40), width=1)

        # 워터마크
        draw.text((width // 2 - 32, height // 2 - 7), "CAPTCHA", fill=(160, 160, 160))
        return img

    @staticmethod
    def _to_b64(img: Image.Image) -> str:
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def _draw_grid(self, draw: ImageDraw.ImageDraw, canvas: int, cell: int, grid: int) -> None:
        """격자선을 그린다."""
        for i in range(1, grid):
            draw.line([(i * cell, 0), (i * cell, canvas)], fill=(60, 60, 60), width=2)
            draw.line([(0, i * cell), (canvas, i * cell)], fill=(60, 60, 60), width=2)

    # ── Slider 퍼즐 ──────────────────────────────────────────────────────
    def _gen_slider(self) -> Dict[str, Any]:
        img = self._create_scene(self.IMAGE_W, self.IMAGE_H)
        # 조각의 왼쪽 x 좌표 (조각 너비를 고려한 범위 내에서 랜덤 선택)
        correct_x = random.randint(self.PIECE_W + 10, self.IMAGE_W - self.PIECE_W - 10)

        piece = img.crop((correct_x, 0, correct_x + self.PIECE_W, self.IMAGE_H))

        bg = img.copy()
        draw = ImageDraw.Draw(bg)
        draw.rectangle(
            [correct_x, 0, correct_x + self.PIECE_W, self.IMAGE_H],
            fill=(190, 190, 190),
        )
        draw.rectangle(
            [correct_x, 0, correct_x + self.PIECE_W, self.IMAGE_H],
            outline=(100, 100, 100),
            width=2,
        )

        return {
            "config": {
                "background": self._to_b64(bg),
                "piece": self._to_b64(piece),
                "piece_width": self.PIECE_W,
                "image_width": self.IMAGE_W,
                "image_height": self.IMAGE_H,
            },
            "answer": {"offset_x": correct_x},
        }

    # ── Drag & Drop 퍼즐 ─────────────────────────────────────────────────
    def _gen_dragdrop(self) -> Dict[str, Any]:
        return self._gen_dragdrop_with_grid(self.GRID)

    def _gen_dragdrop_easy(self) -> Dict[str, Any]:
        return self._gen_dragdrop_with_grid(2)

    def _gen_dragdrop_with_grid(self, grid: int) -> Dict[str, Any]:
        canvas = grid * self.CELL_SIZE
        img = self._create_scene(canvas, canvas)
        draw = ImageDraw.Draw(img)
        self._draw_grid(draw, canvas, self.CELL_SIZE, grid)

        total = grid * grid
        # 각 피스 이미지 크롭
        piece_images: List[str] = []
        for idx in range(total):
            row, col = divmod(idx, grid)
            crop = img.crop((
                col * self.CELL_SIZE, row * self.CELL_SIZE,
                (col + 1) * self.CELL_SIZE, (row + 1) * self.CELL_SIZE,
            ))
            piece_images.append(self._to_b64(crop))

        # 위치 셔플
        shuffled = list(range(total))
        random.shuffle(shuffled)

        pieces = [
            {"id": i, "image": piece_images[i], "current_pos": shuffled[i]}
            for i in range(total)
        ]

        return {
            "config": {
                "pieces": pieces,
                "grid": grid,
                "piece_size": self.CELL_SIZE,
            },
            # positions[pieceId] = 정답 셀 인덱스 (피스 i는 셀 i에 있어야 함)
            "answer": {"positions": list(range(total))},
        }

    # ── Rotate 퍼즐 ─────────────────────────────────────────────────────
    def _gen_rotate(self) -> Dict[str, Any]:
        canvas = self.GRID * self.CELL_SIZE
        img = self._create_scene(canvas, canvas)
        draw = ImageDraw.Draw(img)
        self._draw_grid(draw, canvas, self.CELL_SIZE, self.GRID)

        total = self.GRID * self.GRID
        rotations = [90, 180, 270]
        pieces: List[Dict[str, Any]] = []
        initial_angles: List[int] = []

        for idx in range(total):
            row, col = divmod(idx, self.GRID)
            crop = img.crop((
                col * self.CELL_SIZE, row * self.CELL_SIZE,
                (col + 1) * self.CELL_SIZE, (row + 1) * self.CELL_SIZE,
            ))
            angle = random.choice(rotations)
            # PIL rotate는 CCW 기준 → CW angle을 얻으려면 -angle
            rotated = crop.rotate(-angle, expand=False)
            pieces.append({"id": idx, "image": self._to_b64(rotated), "initial_angle": angle})
            initial_angles.append(angle)

        return {
            "config": {
                "pieces": pieces,
                "grid": self.GRID,
                "piece_size": self.CELL_SIZE,
            },
            # 사용자가 각 피스에 적용해야 하는 CW 회전량 = (360 - initial) % 360
            "answer": {"angles": [(360 - a) % 360 for a in initial_angles]},
        }

    # ── Path Trace v2 퍼즐 (체크포인트 5개) ───────────────────────────────
    def _gen_pathtrace_v2(self) -> Dict[str, Any]:
        width, height = 360, 220
        left, right = 24, width - 24
        center_y = height // 2
        amplitude = 46
        period = 82

        path_points: List[Dict[str, int]] = []
        for x in range(left, right + 1, 8):
            base = center_y + amplitude * math.sin((x - left) / period)
            jitter = random.randint(-4, 4)
            y = int(max(18, min(height - 18, round(base + jitter))))
            path_points.append({"x": x, "y": y})

        # 정확히 5개: 시작/25%/50%/75%/끝
        n = len(path_points)
        indices = [int(i * (n - 1) / 4) for i in range(5)]
        checkpoints = [path_points[i] for i in indices]

        return {
            "config": {
                "width": width,
                "height": height,
                "path_points": path_points,
                "checkpoints": checkpoints,
                "stroke_width": 14,
            },
            "answer": {
                "checkpoints": checkpoints,
                "tolerance": 18,
                "min_coverage": 0.8,
            },
        }

    # ── Click Sequence 퍼즐 ──────────────────────────────────────────────
    def _gen_clickseq(self) -> Dict[str, Any]:
        width, height = 360, 220
        target_count = 5
        radius = 22
        padding = radius + 12

        targets: List[Dict[str, int]] = []
        attempts = 0
        while len(targets) < target_count and attempts < 500:
            attempts += 1
            x = random.randint(padding, width - padding)
            y = random.randint(padding, height - padding)

            # 타깃끼리 충분히 떨어져 있도록 배치
            if any(((x - t["x"]) ** 2 + (y - t["y"]) ** 2) < (radius * 2 + 18) ** 2 for t in targets):
                continue

            targets.append({"id": len(targets) + 1, "x": x, "y": y, "r": radius})

        if len(targets) < target_count:
            # 극단적으로 배치 실패한 경우를 위한 안전 폴백
            targets = [
                {"id": 1, "x": 50, "y": 50, "r": radius},
                {"id": 2, "x": 180, "y": 45, "r": radius},
                {"id": 3, "x": 310, "y": 70, "r": radius},
                {"id": 4, "x": 120, "y": 160, "r": radius},
                {"id": 5, "x": 270, "y": 165, "r": radius},
            ]

        sequence = [t["id"] for t in targets]
        return {
            "config": {
                "width": width,
                "height": height,
                "targets": targets,
                "sequence": sequence,
            },
            "answer": {"sequence": sequence},
        }

    # ── Path Trace 퍼즐 ─────────────────────────────────────────────────
    def _gen_pathtrace(self) -> Dict[str, Any]:
        width, height = 360, 220
        left, right = 24, width - 24
        center_y = height // 2
        amplitude = 46
        period = 82

        path_points: List[Dict[str, int]] = []
        for x in range(left, right + 1, 8):
            base = center_y + amplitude * math.sin((x - left) / period)
            jitter = random.randint(-4, 4)
            y = int(max(18, min(height - 18, round(base + jitter))))
            path_points.append({"x": x, "y": y})

        checkpoints = [path_points[i] for i in range(0, len(path_points), 5)]
        if checkpoints[-1] != path_points[-1]:
            checkpoints.append(path_points[-1])

        return {
            "config": {
                "width": width,
                "height": height,
                "path_points": path_points,
                "checkpoints": checkpoints,
                "stroke_width": 14,
            },
            "answer": {
                "checkpoints": checkpoints,
                "tolerance": 18,
                "min_coverage": 0.8,
            },
        }
