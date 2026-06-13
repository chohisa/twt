const startBtn = document.getElementById("startBtn");

startBtn.onclick = () => {

    document.body.style.transition = "0.8s";
    document.body.style.opacity = "0";

    setTimeout(() => {

        alert("다음 단계 : 코인 토스 화면");

        document.body.style.opacity = "1";

    }, 800);

};
