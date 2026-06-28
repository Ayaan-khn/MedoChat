// Fade cards while scrolling

const cards = document.querySelectorAll(".card");

const observer = new IntersectionObserver((entries)=>{

    entries.forEach(entry=>{

        if(entry.isIntersecting){

            entry.target.style.opacity="1";

            entry.target.style.transform="translateY(0)";

        }

    });

});

cards.forEach(card=>{

    card.style.opacity="0";

    card.style.transform="translateY(60px)";

    card.style.transition="all .8s ease";

    observer.observe(card);

});

// Title typing effect

const title=document.querySelector("header h1");

const text=title.innerText;

title.innerText="";

let i=0;

function typing(){

    if(i<text.length){

        title.innerHTML+=text.charAt(i);

        i++;

        setTimeout(typing,80);

    }

}

typing();