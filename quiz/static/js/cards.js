document.addEventListener("DOMContentLoaded", function() {
    const circles = [];
    const numCircles = 20;
    for (let i = 0; i < numCircles; i++) {
        let circle = document.createElement('img');
        circle.classList.add("circle");
        let size = Math.floor(Math.random() * 5) + 1; // случайный размер от 1 до 5
        let imageIndex = Math.floor(Math.random() * 5) + 1; // случайный индекс изображения от 1 до 5
        circle.src = "/static/img/sheet" + imageIndex + ".png";// использование случайного индекса для выбора изображения
        circle.style.width = size * 20 + "px";
        circle.style.height = size * 20 + "px";
        let x = Math.random() * (window.innerWidth - size * 20);
        let y = Math.random() * (window.innerHeight - size * 20);
        circle.style.left = x + "px";
        circle.style.top = y + "px";
        circles.push({ element: circle, dx: Math.random() * 2 - 1, dy: Math.random() * 2 - 1 });
        document.body.appendChild(circle);
    }
    function checkCollision(circle1, circle2) {
        let rect1 = circle1.getBoundingClientRect();
        let rect2 = circle2.getBoundingClientRect();
        return !(rect1.right < rect2.left ||
                 rect1.left > rect2.right ||
                 rect1.bottom < rect2.top ||
                 rect1.top > rect2.bottom);
    }
    function update() {
        circles.forEach(function(circleObj1) {
            let circle1 = circleObj1.element;
            let dx1 = circleObj1.dx;
            let dy1 = circleObj1.dy;
            let x1 = parseFloat(circle1.style.left);
            let y1 = parseFloat(circle1.style.top);
            circles.forEach(function(circleObj2) {
                let circle2 = circleObj2.element;
                if (circle1 !== circle2 && checkCollision(circle1, circle2)) {
                    // Обработка столкновения
                    let dx2 = circleObj2.dx;
                    let dy2 = circleObj2.dy;
                    let dx = x1 - parseFloat(circle2.style.left);
                    let dy = y1 - parseFloat(circle2.style.top);
                    let dist = Math.sqrt(dx * dx + dy * dy);
                    dx /= dist;
                    dy /= dist;
                    // Уменьшаем скорость после столкновения
                    dx1 *= 0.8;
                    dy1 *= 0.8;
                    dx2 *= 0.8;
                    dy2 *= 0.8;
                    dx1 += dx;
                    dy1 += dy;
                    dx2 -= dx;
                    dy2 -= dy;
                    circleObj2.dx = dx2;
                    circleObj2.dy = dy2;
                }
            });
            if (x1 < 0 || x1 > window.innerWidth - parseFloat(circle1.style.width)) {
                dx1 *= -1;
            }
            if (y1 < 0 || y1 > window.innerHeight - parseFloat(circle1.style.height)) {
                dy1 *= -1;
            }
            x1 += dx1;
            y1 += dy1;
            circle1.style.left = x1 + "px";
            circle1.style.top = y1 + "px";
            circleObj1.dx = dx1;
            circleObj1.dy = dy1;
        });
        requestAnimationFrame(update);
    }
    update();
});