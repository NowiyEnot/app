document.addEventListener('DOMContentLoaded', function() {
    const menuIcon = document.querySelector('.menu-icon');
    const menu = document.querySelector('nav ul');

    menuIcon.addEventListener('click', function() {
        menu.classList.toggle('menu-active');
    });

    // Добавляем обработчик события для закрытия меню при клике вне его области
    document.addEventListener('click', function(event) {
        if (!menu.contains(event.target) && !menuIcon.contains(event.target)) {
            menu.classList.remove('menu-active');
        }
    });
});