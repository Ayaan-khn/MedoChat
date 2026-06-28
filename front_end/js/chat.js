(function initializeMedoChat(){
    const state = {
        csrfToken: "",
        user: null,
        friends: [],
        friendRequests: [],
        groups: [],
        conversations: [],
        notifications: [],
        activeConversation: null,
        messages: [],
        socket: null,
        friendFilter: "online"
    };

    const els = {
        profileAvatar: document.getElementById("profileAvatar"),
        profileName: document.getElementById("profileName"),
        profileUsername: document.getElementById("profileUsername"),
        profileId: document.getElementById("profileId"),
        globalSearch: document.getElementById("globalSearch"),
        friendList: document.getElementById("friendList"),
        groupList: document.getElementById("groupList"),
        activeAvatar: document.getElementById("activeAvatar"),
        activeTitle: document.getElementById("activeTitle"),
        activeStatus: document.getElementById("activeStatus"),
        messageList: document.getElementById("messageList"),
        messageSearch: document.getElementById("messageSearch"),
        messageComposer: document.getElementById("messageComposer"),
        messageInput: document.getElementById("messageInput"),
        typingIndicator: document.getElementById("typingIndicator"),
        rightPanel: document.getElementById("rightPanel"),
        socketStatus: document.getElementById("socketStatus"),
        notificationMenu: document.getElementById("notificationMenu"),
        notificationList: document.getElementById("notificationList"),
        notificationCount: document.getElementById("notificationCount"),
        notificationBadge: document.getElementById("notificationBadge"),
        friendModal: document.getElementById("friendModal"),
        groupModal: document.getElementById("groupModal"),
        friendRequestForm: document.getElementById("friendRequestForm"),
        friendQuery: document.getElementById("friendQuery"),
        userSearchResults: document.getElementById("userSearchResults"),
        groupForm: document.getElementById("groupForm"),
        toggleSidebar: document.getElementById("toggleSidebar")
    };

    function isStaticPreview(){
        return window.location.protocol === "file:" || window.location.pathname.endsWith(".html");
    }

    function initials(name){
        return (name || "M").split(" ").map((part) => part[0]).join("").slice(0,2).toUpperCase();
    }

    function formatTime(value){
        if (!value) {
            return "";
        }
        return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function fallbackAvatar(name){
        return `<div class="avatar-fallback">${escapeHtml(initials(name))}</div>`;
    }

    function escapeHtml(value){
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    async function api(path, options = {}){
        const headers = {
            "Accept": "application/json",
            ...(options.headers || {})
        };

        if (options.body && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }

        if (state.csrfToken) {
            headers["X-CSRFToken"] = state.csrfToken;
        }

        const response = await fetch(path, {
            credentials: "same-origin",
            ...options,
            headers
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || "Request failed.");
        }
        return data;
    }

    async function loadCsrf(){
        if (isStaticPreview()) {
            return;
        }
        const response = await fetch("/auth/csrf-token", { credentials: "same-origin" });
        const data = await response.json();
        state.csrfToken = data.csrfToken || "";
    }

    function renderProfile(){
        if (!state.user) {
            return;
        }
        els.profileName.textContent = state.user.displayName;
        els.profileUsername.textContent = `@${state.user.username}`;
        els.profileId.textContent = `ID ${state.user.id}`;
        if (state.user.avatar) {
            els.profileAvatar.src = state.user.avatar;
        }
        document.getElementById("verifiedBadge").textContent = state.user.emailVerified ? "Email verified" : "Email not verified";
    }

    function contactButton(user, extra = {}){
        const unread = user.unread ? `<span class="unread-badge">${user.unread}</span>` : "";
        const statusClass = user.online ? "online" : "";
        const preview = extra.preview || user.lastMessage || user.status || "";
        return `
            <button class="contact-item ${extra.active ? "active" : ""}" type="button" data-user-id="${user.id}">
                <span class="avatar-ring small ${statusClass}">${user.avatar ? `<img src="${escapeHtml(user.avatar)}" alt="${escapeHtml(user.displayName)}">` : fallbackAvatar(user.displayName)}</span>
                <span class="contact-body">
                    <span class="contact-title"><strong>${escapeHtml(user.displayName)}</strong>${unread}</span>
                    <span class="contact-subtitle">@${escapeHtml(user.username)}</span>
                    <span class="contact-preview">${escapeHtml(preview)}</span>
                </span>
                <span aria-hidden="true">›</span>
            </button>
        `;
    }

    function renderFriends(){
        const search = (els.globalSearch.value || "").toLowerCase();
        let friends = state.friends.filter((friend) => {
            const matchesSearch = `${friend.displayName} ${friend.username} ${friend.id}`.toLowerCase().includes(search);
            if (!matchesSearch) {
                return false;
            }
            if (state.friendFilter === "online") {
                return friend.online;
            }
            if (state.friendFilter === "pending") {
                return false;
            }
            if (state.friendFilter === "blocked") {
                return false;
            }
            return true;
        });

        if (state.friendFilter === "pending") {
            els.friendList.innerHTML = state.friendRequests.length
                ? state.friendRequests.map((request) => `
                    <div class="contact-item">
                        <span class="avatar-ring small">${fallbackAvatar(request.user.displayName)}</span>
                        <span class="contact-body">
                            <strong>${escapeHtml(request.user.displayName)}</strong>
                            <span class="contact-subtitle">${escapeHtml(request.direction)} request</span>
                        </span>
                        ${request.direction === "incoming" ? `<button class="icon-btn" type="button" data-request-id="${request.id}" data-request-action="accept">Accept</button>` : `<button class="icon-btn" type="button" data-request-id="${request.id}" data-request-action="cancel">Cancel</button>`}
                    </div>
                `).join("")
                : `<div class="empty-state">No pending requests.</div>`;
            return;
        }

        els.friendList.innerHTML = friends.length
            ? friends.map((friend) => contactButton(friend)).join("")
            : `<div class="empty-state">No friends match this view.</div>`;
    }

    function renderGroups(){
        const search = (els.globalSearch.value || "").toLowerCase();
        const groups = state.groups.filter((group) => `${group.name} ${group.description}`.toLowerCase().includes(search));
        els.groupList.innerHTML = groups.length
            ? groups.map((group) => `
                <button class="contact-item" type="button" data-group-id="${group.id}">
                    <span class="avatar-ring small">${fallbackAvatar(group.name)}</span>
                    <span class="contact-body">
                        <strong>${escapeHtml(group.name)}</strong>
                        <span class="contact-subtitle">${escapeHtml(group.members)} members</span>
                        <span class="contact-preview">${escapeHtml(group.description || `Invite ${group.inviteCode}`)}</span>
                    </span>
                    <span aria-hidden="true">›</span>
                </button>
            `).join("")
            : `<div class="empty-state">Create a group to start a team chat.</div>`;
    }

    function renderNotifications(){
        const unread = state.notifications.filter((item) => !item.read).length;
        els.notificationCount.textContent = unread;
        els.notificationBadge.textContent = `${unread} unread`;
        els.notificationList.innerHTML = state.notifications.length
            ? state.notifications.map((item) => `
                <button class="notification-item" type="button" data-notification-id="${item.id}">
                    <span class="unread-badge">${item.read ? "✓" : "!"}</span>
                    <span class="contact-body">
                        <strong>${escapeHtml(item.title)}</strong>
                        <span class="contact-preview">${escapeHtml(item.body)}</span>
                    </span>
                    <small>${formatTime(item.createdAt)}</small>
                </button>
            `).join("")
            : `<div class="empty-state">No notifications.</div>`;
    }

    function renderMessages(){
        const search = (els.messageSearch.value || "").toLowerCase();
        const messages = state.messages.filter((message) => message.body.toLowerCase().includes(search));

        if (!state.activeConversation) {
            els.messageList.innerHTML = `
                <div class="day-separator">Today</div>
                <div class="system-card">Select a friend, search for a user, or create a group to begin messaging.</div>
            `;
            return;
        }

        els.messageList.innerHTML = `
            <div class="day-separator">Today</div>
            <div class="unread-separator">Unread messages</div>
            ${messages.map((message) => `
                <article class="message-row ${message.isOwn ? "outgoing" : "incoming"}">
                    <div class="message-bubble">
                        <div class="message-author">${escapeHtml(message.senderName)}</div>
                        <div class="message-body">${escapeHtml(message.body)}</div>
                        <div class="message-meta">
                            <span>${formatTime(message.createdAt)}</span>
                            <span>${message.seenAt ? "Seen" : message.deliveredAt ? "Delivered" : "Sent"}</span>
                        </div>
                    </div>
                </article>
            `).join("")}
        `;
        els.messageList.scrollTop = els.messageList.scrollHeight;
    }

    function renderInfoForUser(user){
        document.getElementById("infoName").textContent = user.displayName;
        document.getElementById("infoUsername").textContent = `@${user.username}`;
        document.getElementById("infoUserId").textContent = `ID ${user.id}`;
        document.getElementById("infoBio").textContent = user.bio || user.status || "Available on MedoChat.";
        if (user.avatar) {
            document.getElementById("infoAvatar").src = user.avatar;
        }
    }

    function setActiveConversation(conversation){
        state.activeConversation = conversation;
        const other = conversation.participants.find((user) => user.id !== state.user.id) || state.user;
        els.activeTitle.textContent = conversation.title;
        els.activeStatus.textContent = conversation.isGroup ? `${conversation.participants.length} members` : other.status;
        if (other.avatar) {
            els.activeAvatar.src = other.avatar;
        }
        renderInfoForUser(other);
    }

    async function openConversationWith(userId){
        const created = await api("/api/conversations", {
            method: "POST",
            body: JSON.stringify({ participantId: userId })
        });
        setActiveConversation(created.conversation);
        if (state.socket) {
            state.socket.emit("join_conversation", { conversationId: created.conversation.id });
        }
        if (!state.conversations.find((item) => item.id === created.conversation.id)) {
            state.conversations.unshift(created.conversation);
        }
        const payload = await api(`/api/conversations/${created.conversation.id}/messages`);
        state.messages = payload.messages;
        renderMessages();
    }

    async function sendMessage(body){
        if (!state.activeConversation) {
            setTransientMessage("Choose a conversation first.");
            return;
        }
        const payload = await api(`/api/conversations/${state.activeConversation.id}/messages`, {
            method: "POST",
            body: JSON.stringify({ body })
        });
        state.messages.push(payload.message);
        renderMessages();
        if (state.socket) {
            state.socket.emit("join_conversation", { conversationId: state.activeConversation.id });
        }
    }

    function setTransientMessage(message){
        const card = document.createElement("div");
        card.className = "system-card";
        card.textContent = message;
        els.messageList.appendChild(card);
        window.setTimeout(() => card.remove(), 2800);
    }

    async function bootstrap(){
        if (isStaticPreview()) {
            state.user = {
                id: "preview-user",
                username: "preview",
                displayName: "Preview User",
                emailVerified: true,
                status: "Static preview"
            };
            state.friends = [];
            state.groups = [];
            state.notifications = [];
            renderAll();
            return;
        }

        await loadCsrf();
        const payload = await api("/api/bootstrap");
        Object.assign(state, payload);
        renderAll();
        initializeSocket();
    }

    function renderAll(){
        renderProfile();
        renderFriends();
        renderGroups();
        renderNotifications();
        renderMessages();
    }

    function openModal(modal){
        modal.hidden = false;
    }

    function closeModals(){
        document.querySelectorAll(".modal").forEach((modal) => {
            modal.hidden = true;
        });
    }

    async function searchUsers(query){
        if (query.trim().length < 2) {
            els.userSearchResults.innerHTML = "";
            return;
        }
        const payload = await api(`/api/users/search?q=${encodeURIComponent(query)}`);
        els.userSearchResults.innerHTML = payload.users.length
            ? payload.users.map((user) => `
                <button class="search-result" type="button" data-search-user-id="${user.id}">
                    <span class="avatar-ring small">${fallbackAvatar(user.displayName)}</span>
                    <span class="contact-body">
                        <strong>${escapeHtml(user.displayName)}</strong>
                        <span class="contact-subtitle">@${escapeHtml(user.username)}</span>
                    </span>
                    <span>Add</span>
                </button>
            `).join("")
            : `<div class="empty-state">No matching users.</div>`;
    }

    function initializeSocket(){
        const script = document.createElement("script");
        script.src = "/socket.io-client.js";
        script.async = true;
        script.onload = () => {
            state.socket = window.io({
                transports: ["websocket", "polling"],
                withCredentials: true,
                reconnectionAttempts: 8,
                timeout: 10000
            });
            state.socket.on("connected", (payload) => {
                els.socketStatus.textContent = "Socket online";
                document.body.dataset.presenceUser = payload.userId || "";
            });
            state.socket.on("presence_update", () => renderFriends());
            state.socket.on("typing", () => {
                els.typingIndicator.hidden = false;
                window.clearTimeout(state.typingTimer);
                state.typingTimer = window.setTimeout(() => {
                    els.typingIndicator.hidden = true;
                }, 1800);
            });
            state.socket.on("message_created", (message) => {
                if (state.activeConversation && message.conversationId === state.activeConversation.id && !state.messages.find((item) => item.id === message.id)) {
                    message.isOwn = message.senderId === state.user.id;
                    state.messages.push(message);
                    renderMessages();
                }
            });
            state.socket.on("connect_error", (error) => {
                els.socketStatus.textContent = error.message || "Socket error";
            });
            state.socket.emit("test_message", { message: "MedoChat connected" });
        };
        script.onerror = () => {
            els.socketStatus.textContent = "Socket client unavailable";
        };
        document.head.appendChild(script);
    }

    document.addEventListener("click", async (event) => {
        const friendItem = event.target.closest("[data-user-id]");
        if (friendItem) {
            await openConversationWith(friendItem.dataset.userId);
        }

        const searchItem = event.target.closest("[data-search-user-id]");
        if (searchItem) {
            els.friendQuery.value = searchItem.dataset.searchUserId;
            await api("/api/friend-requests", {
                method: "POST",
                body: JSON.stringify({ query: searchItem.dataset.searchUserId })
            });
            closeModals();
            await bootstrap();
        }

        const requestAction = event.target.closest("[data-request-action]");
        if (requestAction) {
            await api(`/api/friend-requests/${requestAction.dataset.requestId}/${requestAction.dataset.requestAction}`, { method: "POST" });
            await bootstrap();
        }

        if (event.target.id === "openFriendModal") {
            openModal(els.friendModal);
        }

        if (event.target.id === "openGroupModal") {
            openModal(els.groupModal);
        }

        if (event.target.id === "toggleInfoPanel") {
            els.rightPanel.classList.toggle("open");
        }

        if (event.target.id === "toggleSidebar") {
            document.querySelector(".left-sidebar").classList.toggle("open");
        }

        if (event.target.id === "toggleNotifications") {
            els.notificationMenu.hidden = !els.notificationMenu.hidden;
        }

        if (event.target.matches("[data-close-modal]")) {
            closeModals();
        }

        const friendFilter = event.target.closest("[data-friend-filter]");
        if (friendFilter) {
            state.friendFilter = friendFilter.dataset.friendFilter;
            document.querySelectorAll("[data-friend-filter]").forEach((tab) => tab.classList.remove("active"));
            friendFilter.classList.add("active");
            renderFriends();
        }

        const nav = event.target.closest("[data-view]");
        if (nav) {
            document.querySelectorAll(".nav-btn").forEach((button) => button.classList.remove("active"));
            nav.classList.add("active");
        }

        if (event.target.closest("[data-tool], [data-call], [data-ai], [data-action]")) {
            const label = event.target.textContent.trim();
            setTransientMessage(`${label} is wired in the MedoChat interface.`);
        }
    });

    els.globalSearch.addEventListener("input", () => {
        renderFriends();
        renderGroups();
    });

    els.messageSearch.addEventListener("input", renderMessages);

    els.friendQuery.addEventListener("input", () => {
        searchUsers(els.friendQuery.value).catch((error) => setTransientMessage(error.message));
    });

    els.friendRequestForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await api("/api/friend-requests", {
            method: "POST",
            body: JSON.stringify({ query: els.friendQuery.value })
        });
        closeModals();
        await bootstrap();
    });

    els.groupForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(els.groupForm);
        await api("/api/groups", {
            method: "POST",
            body: JSON.stringify({
                name: formData.get("name"),
                description: formData.get("description")
            })
        });
        closeModals();
        els.groupForm.reset();
        await bootstrap();
    });

    els.messageComposer.addEventListener("submit", async (event) => {
        event.preventDefault();
        const body = els.messageInput.value.trim();
        if (!body) {
            return;
        }
        els.messageInput.value = "";
        await sendMessage(body);
    });

    els.messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            els.messageComposer.requestSubmit();
            return;
        }
        if (state.socket && state.activeConversation) {
            state.socket.emit("typing", { conversationId: state.activeConversation.id });
        }
    });

    bootstrap().catch((error) => {
        setTransientMessage(error.message);
    });
}());
