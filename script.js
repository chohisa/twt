const menu = document.getElementById("menu");

const coinScene = document.getElementById("coinScene");

const startBtn = document.getElementById("startBtn");

const coin = document.getElementById("coin");

const result = document.getElementById("result");

const battleBtn = document.getElementById("battleBtn");

startBtn.onclick = () => {

    menu.classList.add("hidden");

    coinScene.classList.remove("hidden");

    startCoinToss();

};

function startCoinToss(){

    result.innerHTML = "";

    battleBtn.classList.add("hidden");

    coin.classList.add("spin");

    let count = 0;

    const frames = ["🪙","🥇"];

    const timer = setInterval(()=>{

        coin.textContent = frames[count%2];

        count++;

    },100);

    setTimeout(()=>{

        clearInterval(timer);

        coin.classList.remove("spin");

        const playerFirst =
            Math.random() < 0.5;

        coin.textContent = "🪙";

        if(playerFirst){

            result.innerHTML =
            `
            HEAD

            <br><br>

            당신이 선공입니다.
            `;

        }
        else{

            result.innerHTML =
            `
            TAIL

            <br><br>

            AI가 선공입니다.
            `;

        }

        battleBtn.classList.remove("hidden");

    },3000);

}

battleBtn.onclick = ()=>{

    alert(
        "3단계에서는 실제 전장 UI가 표시됩니다."
    );

};
