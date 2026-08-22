document.querySelectorAll('.prototype-select').forEach((button) => {
    button.addEventListener('click', () => {
        const card = button.closest('.prototype-card');
        const selectedName = card.dataset.prototype;

        document.querySelectorAll('.prototype-card').forEach((item) => {
            item.classList.remove('is-selected');
            item.querySelector('.prototype-select').setAttribute('aria-pressed', 'false');
            item.querySelector('.prototype-select').textContent = 'Escolher esta';
        });

        card.classList.add('is-selected');
        button.setAttribute('aria-pressed', 'true');
        button.textContent = 'Selecionada';
        document.querySelector('#prototype-status').textContent = `${selectedName} marcada como favorita.`;
    });
});
