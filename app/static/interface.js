let menu_btn = document.querySelector('button#menu');
let menu_block = document.querySelector('.menu_block');

menu_btn.addEventListener('click', () => {
    menu_block.hidden = !menu_block.hidden;
});
