const API_URLS = {
    email: "https://email-x1cn.onrender.com",
    rag: "https://rag-gdzc.onrender.com",
    receipt: "http://127.0.0.1:8000" // Change this when Receipt is deployed to Render
};
// === API Status Check ===
async function checkApiStatus() {
    const dot = document.getElementById("apiStatus");
    const text = document.getElementById("apiStatusText");
    try {
        const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            dot.className = "status-dot online";
            text.textContent = "API Online";
        } else { throw new Error(); }
    } catch {
        dot.className = "status-dot offline";
        text.textContent = "API Offline";
    }
}
setInterval(checkApiStatus, 10000);
checkApiStatus();

// === Sample Emails ===
const samples = {
    complaint: `Dear Support Team,\n\nI am extremely frustrated. I placed an order (#ORD-4821) three weeks ago and still haven't received my refund of $450. I've called your office twice and was put on hold for over 30 minutes each time. This is completely unacceptable.\n\nIf this is not resolved within 48 hours, I will be filing a complaint with the consumer protection bureau.\n\nRegards,\nSarah Mitchell`,

    request: `Hi there,\n\nI'm looking into upgrading our team's subscription from the Basic to Enterprise plan. Could you please send me:\n\n1. A detailed comparison of features between plans\n2. Pricing for a team of 25 users\n3. Information about your API rate limits on Enterprise\n\nWe'd like to make a decision by end of month.\n\nThanks,\nDavid Chen\nCTO, TechFlow Inc.`,

    info: `Hello,\n\nJust a heads up — we've completed the migration of our staging environment to the new cluster. All services are running normally and the health checks are passing.\n\nNo action needed on your end. The production migration is still scheduled for next Friday.\n\nBest,\nOps Team`
};

function loadSample(type) {
    document.getElementById("emailInput").value = samples[type];
}

// === Process Email ===
async function processEmail() {
    const emailText = document.getElementById("emailInput").value.trim();
    if (!emailText) {
        document.getElementById("emailInput").focus();
        return;
    }

    document.getElementById("step1").querySelector(".btn").disabled = true;
    document.getElementById("demoLoading").style.display = "block";
    document.getElementById("step2").style.display = "none";
    document.getElementById("demoError").style.display = "none";

    try {
        const res = await fetch(`${API_URLS.email}/process`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email_text: emailText })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        document.getElementById("demoLoading").style.display = "none";
        document.getElementById("step2").style.display = "block";

        // Parse classification
        let classification = data.classification;
        let priority = "—";
        let type = "—";
        try {
            const parsed = typeof classification === "string" ? JSON.parse(classification) : classification;
            priority = parsed.priority || "—";
            type = parsed.type || "—";
            classification = JSON.stringify(parsed, null, 2);
        } catch {
            // classification might be raw text
        }

        const prBadge = document.getElementById("priorityBadge");
        prBadge.textContent = priority;
        prBadge.className = `class-value ${priority}`;
        document.getElementById("typeBadge").textContent = type;
        document.getElementById("rawClassification").textContent = classification;
        document.getElementById("draftResponse").textContent = data.response;

        const flag = document.getElementById("approvalFlag");
        flag.textContent = "⏳ Requires Approval";
        flag.className = "approval-flag";

        document.getElementById("step3").style.display = "block";
        document.getElementById("finalStatus").style.display = "none";

        document.getElementById("step2").scrollIntoView({ behavior: "smooth", block: "start" });

    } catch (err) {
        document.getElementById("demoLoading").style.display = "none";
        document.getElementById("demoError").style.display = "block";
        document.getElementById("errorMessage").textContent = err.message;
    }

    document.getElementById("step1").querySelector(".btn").disabled = false;
}

// === Approve / Reject ===
async function approveEmail(approved) {
    const emailText = document.getElementById("emailInput").value.trim();

    try {
        const res = await fetch(`${API_URLS.email}/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email_text: emailText, approved })
        });
        const data = await res.json();

        document.getElementById("step3").style.display = "none";
        const final = document.getElementById("finalStatus");
        final.style.display = "block";

        const flag = document.getElementById("approvalFlag");

        if (approved) {
            document.getElementById("finalIcon").textContent = "✅";
            document.getElementById("finalMessage").textContent = "Email Approved & Sent";
            document.getElementById("finalDetail").textContent = "The drafted response has been approved and would be sent in production.";
            flag.textContent = "✓ Approved";
            flag.className = "approval-flag approved";
        } else {
            document.getElementById("finalIcon").textContent = "🗂️";
            document.getElementById("finalMessage").textContent = "Email Rejected & Archived";
            document.getElementById("finalDetail").textContent = "The draft has been archived for human review. No email was sent.";
            flag.textContent = "✗ Rejected";
            flag.className = "approval-flag rejected";
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// === Reset Demo ===
function resetDemo() {
    document.getElementById("emailInput").value = "";
    document.getElementById("step2").style.display = "none";
    document.getElementById("demoLoading").style.display = "none";
    document.getElementById("demoError").style.display = "none";
    document.getElementById("step1").scrollIntoView({ behavior: "smooth" });
}

// === Animate skill bars on scroll ===
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.querySelectorAll(".bar-fill").forEach(bar => {
                bar.style.width = bar.style.width; // trigger animation
            });
        }
    });
}, { threshold: 0.2 });

document.querySelectorAll(".skill-group").forEach(el => observer.observe(el));

// === Tab Switching ===
function switchDemo(type) {
    // Update tabs
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.getElementById(`tab-${type}`).classList.add("active");

    // Hide all containers
    document.querySelectorAll(".demo-container").forEach(c => c.style.display = "none");
    
    // Show selected
    document.getElementById(`demo-${type}`).style.display = "block";
}

// === RAG Demo ===
async function processRag() {
    const question = document.getElementById("ragInput").value.trim();
    if (!question) return;

    document.getElementById("processRagBtn").disabled = true;
    document.getElementById("ragLoading").style.display = "block";
    document.getElementById("ragResults").style.display = "none";
    document.getElementById("ragError").style.display = "none";

    try {
        const res = await fetch(`${API_URLS.rag}/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        document.getElementById("ragLoading").style.display = "none";
        document.getElementById("ragResults").style.display = "block";
        
        document.getElementById("ragAnswer").textContent = data.answer;
        document.getElementById("ragSources").textContent = JSON.stringify(data.sources, null, 2);

    } catch (err) {
        document.getElementById("ragLoading").style.display = "none";
        document.getElementById("ragError").style.display = "block";
        document.getElementById("ragErrorMessage").textContent = err.message;
    }
    document.getElementById("processRagBtn").disabled = false;
}

// === Receipt Demo ===
function loadReceiptSample() {
    document.getElementById("receiptInput").value = "WHOLE FOODS MARKET - STORE #10402\n2345 BRYANT ST, SAN FRANCISCO, CA 94110\n05/15/2026 14:30\n\nORGANIC APPLES          $4.99\nALMOND MILK             $3.50\nWHOLE WHEAT BREAD       $2.99\n\nTOTAL DUE:              $11.48";
}

async function processReceipt() {
    const receipt_text = document.getElementById("receiptInput").value.trim();
    if (!receipt_text) return;

    document.getElementById("processReceiptBtn").disabled = true;
    document.getElementById("receiptLoading").style.display = "block";
    document.getElementById("receiptResults").style.display = "none";
    document.getElementById("receiptError").style.display = "none";

    try {
        const res = await fetch(`${API_URLS.receipt}/extract`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ receipt_text })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        document.getElementById("receiptLoading").style.display = "none";
        document.getElementById("receiptResults").style.display = "block";
        
        document.getElementById("receiptJson").textContent = JSON.stringify(data, null, 2);

    } catch (err) {
        document.getElementById("receiptLoading").style.display = "none";
        document.getElementById("receiptError").style.display = "block";
        document.getElementById("receiptErrorMessage").textContent = err.message;
    }
    document.getElementById("processReceiptBtn").disabled = false;
}
