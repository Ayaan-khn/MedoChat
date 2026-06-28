// ============================
// Buttons
// ============================

const loginBtn = document.getElementById("loginBtn");
const signupBtn = document.getElementById("signupBtn");

loginBtn.addEventListener("click", () => {

    window.location.href = "login.html";

});

signupBtn.addEventListener("click", () => {

    window.location.href = "signup.html";

});


// ============================
// Fake Chat Messages
// ============================

const chatFeed = document.getElementById("chatFeed");

const messages = [

    {
        user: "Mike",
        text: "Hey everyone 👋"
    },

    {
        user: "Sarah",
        text: "Ready for tomorrow? ✈️"
    },

    {
        user: "Medo AI",
        text: "Rain expected tomorrow ☔"
    },

    {
        user: "Alex",
        text: "Meet at 7 PM!"
    },

    {
        user: "Emily",
        text: "Can't wait 😂"
    },

    {
        user: "David",
        text: "Joining in 5 mins."
    },

    {
        user: "Medo AI",
        text: "All systems online 🤖"
    }

];

let index = 0;

function updateChat(){

    chatFeed.innerHTML = "";

    for(let i = 0; i < 4; i++){

        const current = messages[(index + i) % messages.length];

        const message = document.createElement("div");

        message.className = "message";

        if(current.user === "Medo AI"){

            message.classList.add("ai");

        }

        message.innerHTML = `

            <span class="user">${current.user}</span>
            <p>${current.text}</p>

        `;

        chatFeed.appendChild(message);

    }

    index++;

}

setInterval(updateChat,3000);


// ============================
// Animated Stats
// ============================

const statNumbers = document.querySelectorAll(".stat h2");

const finalNumbers = [

    1842,
    25000,
    42,
    24

];

statNumbers.forEach((stat,index)=>{

    let count = 0;

    let target = finalNumbers[index];

    let speed = target / 100;

    const timer = setInterval(()=>{

        count += speed;

        if(count >= target){

            count = target;

            clearInterval(timer);

        }

        if(index==1){

            stat.innerText = Math.floor(count).toLocaleString() + "+";

        }

        else if(index==3){

            stat.innerText = "24/7";

        }

        else{

            stat.innerText = Math.floor(count).toLocaleString();

        }

    },20);

});