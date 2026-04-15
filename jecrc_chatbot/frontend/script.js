document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chat-window");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
    const threadList = document.getElementById("thread-list");
    const newChatBtn = document.getElementById("new-chat-btn");
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const toggleIcon = document.getElementById("toggle-icon");
    const welcomeMsg = document.getElementById("welcome-msg");

    // ── Session & Thread State ──────────────────────────────────────────────
    let sessionId = localStorage.getItem("current_session_id") || crypto.randomUUID();
    localStorage.setItem("current_session_id", sessionId);

    // threads stored as: { id, title, timestamp }[]
    function getThreads() {
        try { return JSON.parse(localStorage.getItem("jecrc_threads") || "[]"); }
        catch { return []; }
    }

    function saveThread(id, title) {
        const threads = getThreads();
        const existing = threads.find(t => t.id === id);
        if (existing) {
            existing.title = title;
            existing.timestamp = Date.now();
        } else {
            threads.unshift({ id, title: title || "New Chat", timestamp: Date.now() });
        }
        localStorage.setItem("jecrc_threads", JSON.stringify(threads.slice(0, 50)));
    }

    function deleteThread(id) {
        const threads = getThreads().filter(t => t.id !== id);
        localStorage.setItem("jecrc_threads", JSON.stringify(threads));
        if (id === sessionId) {
            switchThread(crypto.randomUUID());
        }
        renderThreads();
    }

    function renderThreads() {
        const threads = getThreads();
        if (threads.length === 0) {
            threadList.innerHTML = `<p class="text-[11px] text-gray-600 px-3 py-2 italic">No chats yet</p>`;
            return;
        }
        threadList.innerHTML = threads.map(t => `
            <div class="thread-item ${t.id === sessionId ? 'thread-active' : ''}" onclick="switchThread('${t.id}')">
                <span class="thread-title">${escapeHtml(t.title)}</span>
                <button class="thread-delete" onclick="event.stopPropagation(); deleteThreadById('${t.id}')" title="Delete">&#10005;</button>
            </div>
        `).join('');
    }

    window.switchThread = (id) => {
        sessionId = id;
        localStorage.setItem("current_session_id", id);
        chatWindow.innerHTML = '';
        welcomeMsg && chatWindow.appendChild(welcomeMsg);
        loadHistory(id);
        renderThreads();
    };

    window.deleteThreadById = (id) => deleteThread(id);

    newChatBtn.addEventListener("click", () => {
        const newId = crypto.randomUUID();
        saveThread(newId, "New Chat");
        switchThread(newId);
    });

    // ── Sidebar Toggle ──────────────────────────────────────────────────────
    let sidebarOpen = true;

    sidebarToggle.addEventListener("click", () => {
        sidebarOpen = !sidebarOpen;
        sidebar.classList.toggle("sidebar-hidden", !sidebarOpen);
        toggleIcon.innerHTML = sidebarOpen ? "&#9664;" : "&#9654;";
        sidebarToggle.style.left = sidebarOpen ? "0" : "0";
    });

    // ── History Loading ─────────────────────────────────────────────────────
    async function loadHistory(id) {
        try {
            const res = await fetch(`http://localhost:8000/history/${id}`);
            const data = await res.json();
            if (data.messages && data.messages.length > 0) {
                hideWelcome();
                data.messages.forEach(m => appendMessage(m.content, m.role));
            }
        } catch (e) {
            console.log("New session or backend offline.");
        }
    }

    function hideWelcome() {
        const w = document.getElementById("welcome-msg");
        if (w) w.style.display = "none";
    }

    // ── Message Rendering ───────────────────────────────────────────────────
    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function appendMessage(text, role) {
        hideWelcome();
        const wrapper = document.createElement("div");
        wrapper.className = `flex w-full ${role === 'user' ? 'justify-end' : 'justify-start'}`;

        if (role === 'user') {
            wrapper.innerHTML = `
                <div class="user-bubble">
                    ${escapeHtml(text)}
                </div>`;
        } else {
            wrapper.innerHTML = `
                <div class="bot-row">
                    <div class="bot-icon">J</div>
                    <div class="bot-bubble prose">
                        ${marked.parse(text)}
                    </div>
                </div>`;
        }
        chatWindow.appendChild(wrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        if (role === 'assistant') {
            return wrapper.querySelector('.bot-bubble');
        }
        return null;
    }

    // ── Typewriter effect ───────────────────────────────────────────────────
    function typewriterEffect(bubble, fullText, onDone) {
        const words = fullText.split(" ");
        let i = 0;
        let accumulated = "";
        function step() {
            if (i >= words.length) {
                bubble.classList.remove("streaming");
                bubble.innerHTML = marked.parse(fullText);
                chatWindow.scrollTop = chatWindow.scrollHeight;
                if (onDone) onDone();
                return;
            }
            accumulated += (i === 0 ? "" : " ") + words[i];
            i++;
            bubble.innerHTML = marked.parse(accumulated) + '<span class="cursor">▋</span>';
            chatWindow.scrollTop = chatWindow.scrollHeight;
            setTimeout(step, 20);
        }
        step();
    }

    // ── Sending Messages ────────────────────────────────────────────────────
    async function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        messageInput.value = "";
        messageInput.disabled = true;
        sendButton.disabled = true;
        appendMessage(text, "user");

        hideWelcome();
        const wrapper = document.createElement("div");
        wrapper.className = "flex w-full justify-start";
        wrapper.innerHTML = `
            <div class="bot-row">
                <div class="bot-icon">J</div>
                <div class="bot-bubble prose" id="streaming-bubble"></div>
            </div>`;
        chatWindow.appendChild(wrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        const botBubble = document.getElementById("streaming-bubble");
        botBubble.innerHTML = '<span class="cursor">▋</span>';

        try {
            const response = await fetch("http://localhost:8000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, message: text })
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            const answerText = data.response || data.answer || "Sorry, I could not process that.";
            botBubble.removeAttribute("id");

            typewriterEffect(botBubble, answerText, () => {
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.focus();

                const threadTitle = text.length > 40 ? text.substring(0, 40) + "\u2026" : text;
                const threads = getThreads();
                const exists = threads.find(t => t.id === sessionId);
                if (!exists || exists.title === "New Chat") {
                    saveThread(sessionId, threadTitle);
                }
                renderThreads();
            });

        } catch (error) {
            botBubble.classList.add("error-bubble");
            botBubble.innerText = "The support desk is offline. Please check the backend server.";
            botBubble.removeAttribute("id");
            messageInput.disabled = false;
            sendButton.disabled = false;
            console.error(error);
        }
    }

    sendButton.addEventListener("click", sendMessage);
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) sendMessage();
    });

    // ── Init ────────────────────────────────────────────────────────────────
    // Ensure current session is in thread list
    const threads = getThreads();
    if (!threads.find(t => t.id === sessionId)) {
        saveThread(sessionId, "New Chat");
    }
    renderThreads();
    loadHistory(sessionId);
});