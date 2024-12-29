let menu_btn = document.querySelector('button#menu');
let menu_block = document.querySelector('.menu_block');

let main = document.querySelector('.main');

menu_btn.addEventListener('click', () => {
    menu_block.hidden = !menu_block.hidden;
});

if (main.hasAttribute('hidden')) {
    let guideLine = document.querySelector('.guide .block p');
    let guideBlock = document.querySelector('.guide .block');

    guideBlock.style.opacity = 1;

    let totalTime = 0;

    let word = 'Привет';
    for (let i = 0; i < word.length; i++) {
        setTimeout(() => {
            guideLine.innerHTML += word[i];
        }, 100 * (i + 1) + 750);
    }

    totalTime += 100 * word.length + 750 + 1000;

    setTimeout(() => {
        for (let i = 0; i < word.length; i++) {
            setTimeout(() => {
                guideLine.innerHTML = guideLine.innerHTML.slice(0, -1);
            }, 75 * (i + 1) + 750);
        }
    }, totalTime);

    totalTime += 75 * word.length + 750;

    setTimeout(() => {
        word = 'Это oneCode — место, где один код пишут сразу много кодеров';
        guideBlock.style.height = '120px';
        for (let i = 0; i < word.length; i++) {
            setTimeout(() => {
                guideLine.innerHTML += word[i];
            }, 50 * (i + 1) + 750);
        }
    }, totalTime);

    totalTime += 50 * word.length + 750 + 5000;

    setTimeout(() => {
        for (let i = 0; i < word.length; i++) {
            setTimeout(() => {
                guideLine.innerHTML = guideLine.innerHTML.slice(0, -1);
            }, 25 * (i + 1) + 750);
        }
    }, totalTime);

    totalTime += 25 * word.length + 1500;

    setTimeout(() => {
        word = 'Вступай в канал — там инструкции и другие участники';
        for (let i = 0; i < word.length; i++) {
            setTimeout(() => {
                guideLine.innerHTML += word[i];
            }, 50 * (i + 1) + 750);
        }
        setTimeout(() => {
            word = '@oneCode_eleday';
            for (let i = 0; i < word.length; i++) {
                setTimeout(() => {
                    guideBlock.querySelector('a').innerHTML += word[i];
                }, 50 * (i + 1) + 750);
            }
        }, 50 * word.length + 750);
    }, totalTime);

    totalTime += 50 * word.length + 750 + 10000;

    setTimeout(() => {
        guideLine.style.opacity = 0;
        guideBlock.querySelector('a').style.opacity = 0;
        setTimeout(() => {
            guideBlock.style.width = '200px';
            guideBlock.style.height = '60px';
            guideBlock.querySelector('div').style.left = 0;
            guideBlock.querySelector('div').style.width = '200px';
            guideLine.style.width = '200px';
            guideBlock.querySelector('a').remove();
            guideLine.innerHTML = 'by eleday';
            guideLine.style.textAlign = 'center';
            guideLine.style.opacity = 1;
        }, 1000);

        setTimeout(() => {
            guideLine.style.opacity = 0;
            guideBlock.style.width = '60vw';
            guideBlock.style.height = '94vh';
            setTimeout(() => {
                window.location.href = '/'
            }, 1000);
        }, 6000);
    }, totalTime);

}

(function createSnow() {
    const snowflakeCount = 100; // Количество снежинок

    function createSnowflake() {
        const snowflake = document.createElement('div');
        snowflake.classList.add('snowflake');

        // Устанавливаем начальное положение
        if (Math.round(Math.random())) snowflake.style.left = Math.random() * 20 + 'vw';
        else snowflake.style.right = Math.random() * 20 + 'vw';
        snowflake.style.animationDuration = (Math.random() * 10 + 5) + 's';
        let d =  Math.random() * 5 + 5 + 'px';
        snowflake.style.width = d;
        snowflake.style.height = d;
        document.body.appendChild(snowflake);

        // Удаляем снежинку после окончания анимации
        setTimeout(() => {
            snowflake.remove();
        }, 15000);
    }

    function startSnowfall() {
        setInterval(() => {
            createSnowflake();
        }, 1000); // Интервал появления новых снежинок
    }

    startSnowfall();
})();