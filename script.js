const API_URLS = {
    email: "https://email-x1cn.onrender.com",
    rag: "https://rag-gdzc.onrender.com",
    evaluator: "http://127.0.0.1:8001", // Change when deployed
    receipt: "http://127.0.0.1:8002" // Change when deployed
};
// === API Status Check ===
async function checkApiStatus() {
    const dot = document.getElementById("apiStatus");
    const text = document.getElementById("apiStatusText");
    try {
        const res = await fetch(`${API_URLS.email}/health`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            dot.className = "status-dot online";
            text.textContent = "APIs Online";
        } else { throw new Error(); }
    } catch {
        dot.className = "status-dot offline";
        text.textContent = "APIs Offline";
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

        // Update Privacy Badge
        const privBadge = document.getElementById("privacyBadge");
        privBadge.textContent = data.privacy_scan || "PASSED";
        privBadge.style.color = (data.privacy_scan && data.privacy_scan.includes("FLAGGED")) ? "var(--accent-red)" : "var(--accent-green)";

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
const ragSamples = {
    ai_policy: "What are the key principles of the UK's AI regulation policy?",
    data_protection: "How does the AI framework intersect with existing GDPR and data protection laws?",
    compute: "What is the government's strategy regarding AI compute infrastructure?"
};

function loadRagSample(type) {
    document.getElementById("ragInput").value = ragSamples[type];
}

async function processRag() {
    const question = document.getElementById("ragInput").value.trim();
    if (!question) return;

    document.getElementById("processRagBtn").disabled = true;
    document.getElementById("ragLoading").style.display = "block";
    document.getElementById("ragStep2").style.display = "none";
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
        document.getElementById("ragStep2").style.display = "block";
        
        document.getElementById("ragAnswer").textContent = data.answer;
        
        // Render sources nicely
        const sourcesHtml = (data.sources || []).map((src, index) => `
            <div class="result-card" style="padding: 16px;">
                <div class="result-header" style="margin-bottom: 8px;">
                    <span class="result-icon">📄</span>
                    <h4 style="font-size: 0.9rem; margin: 0;">Source ${index + 1}: ${src.metadata?.source || 'Unknown'}</h4>
                </div>
                <div class="result-body">
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 8px;">Page/Section: ${src.metadata?.page || src.metadata?.section || 'N/A'}</p>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); background: var(--bg-primary); padding: 12px; border-radius: 6px; border: 1px solid var(--border);">
                        "${src.content ? src.content.substring(0, 150) : ''}${src.content && src.content.length > 150 ? '...' : ''}"
                    </div>
                </div>
            </div>
        `).join('');
        document.getElementById("ragSourcesGrid").innerHTML = sourcesHtml || '<p style="color: var(--text-muted); font-size: 0.9rem;">No sources returned.</p>';

        document.getElementById("ragStep3").style.display = "block";
        document.getElementById("ragFinalStatus").style.display = "none";
        document.getElementById("ragStep2").scrollIntoView({ behavior: "smooth", block: "start" });

    } catch (err) {
        document.getElementById("ragLoading").style.display = "none";
        document.getElementById("ragError").style.display = "block";
        document.getElementById("ragErrorMessage").textContent = err.message;
    }
    document.getElementById("processRagBtn").disabled = false;
}

async function feedbackRag(isAccurate) {
    const question = document.getElementById("ragInput").value.trim();
    const answer = document.getElementById("ragAnswer").textContent;
    
    document.getElementById("ragStep3").style.display = "none";
    const final = document.getElementById("ragFinalStatus");
    final.style.display = "block";

    if (isAccurate) {
        document.getElementById("ragFinalIcon").textContent = "✅";
        document.getElementById("ragFinalMessage").textContent = "Feedback Recorded: Accurate";
        document.getElementById("ragFinalDetail").textContent = "Thank you! This QA pair will be added to the positive evaluation dataset.";
    } else {
        try {
            await fetch(`${API_URLS.rag}/flag`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, answer, reason: "bad_answer" })
            });
        } catch(e) {
            console.error("Failed to flag:", e);
        }
        document.getElementById("ragFinalIcon").textContent = "🚩";
        document.getElementById("ragFinalMessage").textContent = "Answer Flagged for Review";
        document.getElementById("ragFinalDetail").textContent = "This query and context have been flagged. The retrieval chunking strategy will be reviewed.";
    }
}

function resetRagDemo() {
    document.getElementById("ragInput").value = "";
    document.getElementById("ragStep2").style.display = "none";
    document.getElementById("ragLoading").style.display = "none";
    document.getElementById("ragError").style.display = "none";
    document.getElementById("ragStep1").scrollIntoView({ behavior: "smooth" });
}

// === Evaluator Demo ===
async function processEval() {
    const endpoint = document.getElementById("evalEndpoint").value.trim();
    if (!endpoint) return;

    document.getElementById("processEvalBtn").disabled = true;
    document.getElementById("evalLoading").style.display = "block";
    document.getElementById("evalResults").style.display = "none";
    document.getElementById("evalError").style.display = "none";

    try {
        const res = await fetch(`${API_URLS.evaluator}/evaluate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rag_endpoint: endpoint })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        document.getElementById("evalLoading").style.display = "none";
        document.getElementById("evalResults").style.display = "block";
        
        let scoresHtml = '';
        if (data.aggregate_scores) {
            scoresHtml = Object.entries(data.aggregate_scores).map(([key, value]) => `
                <div class="class-badge">
                    <span class="class-label">${key.replace('_', ' ')}</span>
                    <span class="class-value ${value >= 0.85 ? 'low' : (value >= 0.7 ? 'normal' : 'urgent')}">${(value * 100).toFixed(1)}%</span>
                </div>
            `).join('');
        }
        document.getElementById("evalScores").innerHTML = scoresHtml || '<p>No aggregate scores available</p>';

        document.getElementById("evalFlagged").textContent = JSON.stringify(data.flagged_items || [], null, 2);

    } catch (err) {
        document.getElementById("evalLoading").style.display = "none";
        document.getElementById("evalError").style.display = "block";
        document.getElementById("evalErrorMessage").textContent = err.message;
    }
    document.getElementById("processEvalBtn").disabled = false;
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
    document.getElementById("receiptStep2").style.display = "none";
    document.getElementById("receiptError").style.display = "none";

    try {
        const res = await fetch(`${API_URLS.receipt}/extract`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ receipt_text })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        window.currentReceiptPrediction = data;

        document.getElementById("receiptLoading").style.display = "none";
        document.getElementById("receiptStep2").style.display = "block";
        
        let fieldsHtml = Object.entries(data).map(([key, value]) => `
            <div class="class-badge" style="flex-basis: 45%; margin-bottom: 12px;">
                <span class="class-label">${key}</span>
                <span class="class-value">${value}</span>
            </div>
        `).join('');
        document.getElementById("receiptFields").innerHTML = fieldsHtml || '<p>No data extracted</p>';

        document.getElementById("receiptStep3").style.display = "block";
        document.getElementById("receiptFinalStatus").style.display = "none";
        document.getElementById("receiptStep2").scrollIntoView({ behavior: "smooth", block: "start" });

    } catch (err) {
        document.getElementById("receiptLoading").style.display = "none";
        document.getElementById("receiptError").style.display = "block";
        document.getElementById("receiptErrorMessage").textContent = err.message;
    }
    document.getElementById("processReceiptBtn").disabled = false;
}

async function feedbackReceipt(isCorrect) {
    document.getElementById("receiptStep3").style.display = "none";
    const final = document.getElementById("receiptFinalStatus");
    final.style.display = "block";

    if (isCorrect) {
        document.getElementById("receiptFinalIcon").textContent = "✅";
        document.getElementById("receiptFinalMessage").textContent = "Extraction Verified";
        document.getElementById("receiptFinalDetail").textContent = "This receipt was processed successfully and will be used as a positive ground-truth label.";
    } else {
        const receipt_text = document.getElementById("receiptInput").value.trim();
        try {
            await fetch(`${API_URLS.receipt}/review`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    receipt_text, 
                    predicted: window.currentReceiptPrediction || {}, 
                    corrected: {} 
                })
            });
        } catch(e) { console.error(e); }
        document.getElementById("receiptFinalIcon").textContent = "🔄";
        document.getElementById("receiptFinalMessage").textContent = "Flagged for Re-training";
        document.getElementById("receiptFinalDetail").textContent = "This sample has been sent to the correction queue. The LoRA fine-tuning pipeline will use it in the next epoch.";
    }
}

function resetReceiptDemo() {
    document.getElementById("receiptInput").value = "";
    document.getElementById("receiptStep2").style.display = "none";
    document.getElementById("receiptLoading").style.display = "none";
    document.getElementById("receiptError").style.display = "none";
    document.getElementById("receiptStep1").scrollIntoView({ behavior: "smooth" });
}
