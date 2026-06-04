document.addEventListener('DOMContentLoaded', () => {

    const alerts = document.querySelectorAll('.alert');

    if (!alerts.length) {
        return;
    }

    setTimeout(() => {

        alerts.forEach(alert => {

            alert.style.transition =
                'opacity 0.4s ease, transform 0.4s ease';

            alert.style.opacity = '0';

            alert.style.transform = 'translateY(-10px)';

            setTimeout(() => {

                alert.remove();

            }, 400);

        });

    }, 4000);

});