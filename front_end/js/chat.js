const socket = window.io ? window.io() : null;

if (socket) {
    socket.on("presence", (payload) => {
        console.info("Presence update", payload);
    });
}
