'use strict';

/**
 * ClickSequencePuzzleV2
 * v2: 순서/진행 라벨을 보드 밖(위)으로 분리하여 숫자 원과 겹치지 않도록 개선.
 */
const ClickSequencePuzzleV2 = (() => {
    let _clicked = [];

    function render(container, config, tracker) {
        const { width, height, targets, sequence } = config;
        _clicked = [];

        // ── 전체 래퍼 (라벨 + 보드) ────────────────────────────
        const wrapper = document.createElement('div');
        wrapper.className = 'clickseq-wrapper-v2';

        // ── 라벨 영역 (보드 위에 별도 배치) ────────────────────
        const labelsEl = document.createElement('div');
        labelsEl.className = 'clickseq-labels-v2';

        const guide = document.createElement('span');
        guide.className = 'clickseq-guide-v2';
        guide.textContent = '순서: ' + sequence.join(' → ');
        labelsEl.appendChild(guide);

        const progress = document.createElement('span');
        progress.className = 'clickseq-progress-v2';
        progress.textContent = `진행: 0 / ${sequence.length}`;
        labelsEl.appendChild(progress);

        wrapper.appendChild(labelsEl);

        // ── 타깃 보드 (라벨 없음) ───────────────────────────────
        const board = document.createElement('div');
        board.className = 'clickseq-board';
        board.style.cssText = `width:${width}px; height:${height}px;`;

        targets.forEach((t) => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'clickseq-target';
            btn.textContent = String(t.id);
            btn.style.width = `${t.r * 2}px`;
            btn.style.height = `${t.r * 2}px`;
            btn.style.left = `${t.x - t.r}px`;
            btn.style.top = `${t.y - t.r}px`;

            btn.addEventListener('click', () => {
                if (btn.classList.contains('done')) return;

                const expected = sequence[_clicked.length];
                if (t.id !== expected) {
                    _clicked = [];
                    progress.textContent = `진행: 0 / ${sequence.length}`;
                    board.classList.remove('shake');
                    void board.offsetWidth;
                    board.classList.add('shake');
                    board.querySelectorAll('.clickseq-target.done').forEach(el => el.classList.remove('done'));
                    return;
                }

                _clicked.push(t.id);
                btn.classList.add('done');
                progress.textContent = `진행: ${_clicked.length} / ${sequence.length}`;
            });

            board.appendChild(btn);
        });

        wrapper.appendChild(board);
        container.appendChild(wrapper);
        tracker.start(board);
    }

    function getAnswer() {
        return { sequence: [..._clicked] };
    }

    return { render, getAnswer };
})();