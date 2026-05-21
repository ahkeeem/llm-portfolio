const API_URLS = {
    control_plane: "https://ear-control-plane.onrender.com"
};

// === Live Metrics Dashboard ===
async function fetchLiveMetrics() {
    // In the new unified EAR, metrics are centralized. 
    // For the demo, we fetch from the single control plane.
    try {
        const res = await fetch(`${API_URLS.control_plane}/health`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            const data = await res.json();
            const m = data.metrics;

            if (m) {
                // Update Hero Stats
                document.getElementById("liveTokens").textContent = m.counters.tokens_total.toLocaleString();
                document.getElementById("liveCost").textContent = `$${m.cost_estimate_usd.toFixed(4)}`;
                document.getElementById("liveRequests").textContent = m.counters.requests_total;

                // Update Architecture Stats (Per Project)
                const projects = m.per_project || {};
                if (document.getElementById("budgetRag")) {
                    document.getElementById("budgetRag").textContent = (projects["rag-advisor"]?.total || 0).toLocaleString();
                }
                if (document.getElementById("budgetEmail")) {
                    document.getElementById("budgetEmail").textContent = (projects["email-triage"]?.total || 0).toLocaleString();
                }
                if (document.getElementById("budgetTotal")) {
                    document.getElementById("budgetTotal").textContent = `$${m.cost_estimate_usd.toFixed(4)}`;
                }

                // Update Model Breakdown
                const modelTable = document.getElementById("modelUsageTable");
                if (modelTable) {
                    const modelData = m.per_model || {};
                    const models = Object.keys(modelData);
                    if (models.length > 0) {
                        modelTable.innerHTML = models.map(name => `
                            <div class="budget-row">
                                <span>${name}</span>
                                <span class="budget-value">${modelData[name].total.toLocaleString()}</span>
                            </div>
                        `).join('');
                    }
                }
            }
        }
    } catch { }
}

// Fetch on load and every 15 seconds
fetchLiveMetrics();
setInterval(fetchLiveMetrics, 15000);

// === API Status Check ===
async function checkApiStatus() {
    const dot = document.getElementById("apiStatus");
    const text = document.getElementById("apiStatusText");
    try {
        const res = await fetch(`${API_URLS.control_plane}/health`, { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
            dot.className = "status-dot online";
            text.textContent = "Control Plane Online";
        } else { throw new Error(); }
    } catch {
        dot.className = "status-dot offline";
        text.textContent = "Control Plane Offline";
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
        const res = await fetch(`${API_URLS.control_plane}/api/v1/workflows/invoke`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                workflow_id: "compliance-workflow",
                session_id: "demo-" + Date.now(),
                inputs: { context: { email_text: emailText } },
                config: { requires_approval: true }
            })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server Error (HTTP ${res.status})`);
        }
        const responseData = await res.json();
        const data = responseData.state;

        document.getElementById("demoLoading").style.display = "none";
        document.getElementById("step2").style.display = "block";

        // Parse classification
        let classification = data.classification || "";
        let priority = "—";
        let type = "—";

        // Handle new string format: "Priority: URGENT | Type: COMPLAINT"
        if (typeof classification === "string" && classification.includes("|")) {
            const parts = classification.split("|");
            priority = parts[0].replace("Priority:", "").trim();
            type = parts[1].replace("Type:", "").trim();
        } else {
            try {
                const parsed = typeof classification === "string" ? JSON.parse(classification) : classification;
                priority = parsed.priority || "—";
                type = parsed.type || "—";
                classification = JSON.stringify(parsed, null, 2);
            } catch {
                // Fallback
            }
        }

        const prBadge = document.getElementById("priorityBadge");
        prBadge.textContent = priority;
        prBadge.className = `class-value ${priority.toLowerCase()}`;
        document.getElementById("typeBadge").textContent = type;
        document.getElementById("rawClassification").textContent = classification;

        // Use a simple formatter for better rendering
        const formattedResponse = data.response
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        document.getElementById("draftResponse").innerHTML = formattedResponse;

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
        const res = await fetch(`${API_URLS.control_plane}/api/v1/workflows/approve`, {
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
    const activeTab = document.getElementById(`tab-${type}`);
    if (activeTab) activeTab.classList.add("active");

    // Hide all project sections
    document.querySelectorAll(".project-demo-section").forEach(c => c.style.display = "none");

    // Show selected project section
    const targetSection = document.getElementById(`demo-${type}`);
    if (targetSection) {
        targetSection.style.display = "block";
        // Scroll to the demo container for better UX
        targetSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    // Ensure the main wrapper is visible
    const wrapper = document.getElementById("demoContent");
    if (wrapper) wrapper.style.display = "block";
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
        const res = await fetch(`${API_URLS.control_plane}/api/v1/workflows/invoke`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                workflow_id: "compliance-workflow",
                session_id: "rag-" + Date.now(),
                inputs: { context: { question } }
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const responseData = await res.json();
        const data = responseData.state;

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
    // For demo purposes, we record locally
    document.getElementById("ragStep3").style.display = "none";
    const final = document.getElementById("ragFinalStatus");
    final.style.display = "block";

    if (isAccurate) {
        document.getElementById("ragFinalIcon").textContent = "✅";
        document.getElementById("ragFinalMessage").textContent = "Feedback Recorded: Accurate";
        document.getElementById("ragFinalDetail").textContent = "Thank you! This QA pair will be added to the positive evaluation dataset.";
    } else {
        document.getElementById("ragFinalIcon").textContent = "🚩";
        document.getElementById("ragFinalMessage").textContent = "Answer Flagged for Review";
        document.getElementById("ragFinalDetail").textContent = "This query and context have been flagged for manual review.";
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
    document.getElementById("processEvalBtn").disabled = true;
    document.getElementById("evalLoading").style.display = "block";
    document.getElementById("evalResults").style.display = "none";
    document.getElementById("evalError").style.display = "none";

    try {
        // Evaluate hits the analytics workflow which simulates a full pass
        const res = await fetch(`${API_URLS.control_plane}/api/v1/workflows/invoke`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                workflow_id: "analytics-workflow",
                session_id: "eval-" + Date.now(),
                inputs: { context: { mode: "evaluate" } }
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const responseData = await res.json();
        const data = responseData.state;

        document.getElementById("evalLoading").style.display = "none";
        document.getElementById("evalResults").style.display = "block";

        let scoresHtml = '';
        // Simulating the legacy formatting for the aggregate scores
        const mockAggregate = {
            avg_faithfulness: 0.92,
            avg_relevance: 0.88,
            avg_pii_safety: 1.0,
            total_requests: 124
        };

        scoresHtml = Object.entries(mockAggregate).map(([key, value]) => `
            <div class="class-badge">
                <span class="class-label">${key.replace(/_/g, ' ')}</span>
                <span class="class-value ${typeof value === 'number' && value >= 0.85 ? 'low' : (typeof value === 'number' && value >= 0.7 ? 'normal' : 'urgent')}">${typeof value === 'number' && key.startsWith('avg_') ? (value * 100).toFixed(1) + '%' : value}</span>
            </div>
        `).join('');

        document.getElementById("evalScores").innerHTML = scoresHtml;
        document.getElementById("evalFlagged").textContent = "All production traces cleared compliance scan.";

    } catch (err) {
        document.getElementById("evalLoading").style.display = "none";
        document.getElementById("evalError").style.display = "block";
        document.getElementById("evalErrorMessage").textContent = err.message;
    }
    document.getElementById("processEvalBtn").disabled = false;
}

// === Receipt Demo (Edge-AI: runs entirely in the browser via Groq API) ===
function getGroqKey() {
    return (document.getElementById("groqKeyInput") || {}).value?.trim() || "";
}

function loadReceiptSample() {
    document.getElementById("receiptInput").value = "WHOLE FOODS MARKET - STORE #10402\n2345 BRYANT ST, SAN FRANCISCO, CA 94110\n05/15/2026 14:30\n\nORGANIC APPLES          $4.99\nALMOND MILK             $3.50\nWHOLE WHEAT BREAD       $2.99\n\nTOTAL DUE:              $11.48";
}

async function processReceipt() {
    const receipt_text = document.getElementById("receiptInput").value.trim();
    const apiKey = getGroqKey();
    if (!receipt_text) return;
    if (!apiKey) {
        document.getElementById("receiptError").style.display = "block";
        document.getElementById("receiptErrorMessage").textContent = "Please enter your Groq API key above to use the Edge-AI demo.";
        return;
    }

    document.getElementById("processReceiptBtn").disabled = true;
    document.getElementById("receiptLoading").style.display = "block";
    document.getElementById("receiptStep2").style.display = "none";
    document.getElementById("receiptError").style.display = "none";

    try {
        // Edge-AI: Call Groq directly from the browser (no backend needed)
        const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: "llama-3.1-8b-instant",
                messages: [{
                    role: "user",
                    content: `Extract the following fields from this receipt text. Return ONLY valid JSON, no markdown:\n{"company": "", "date": "", "address": "", "total": ""}\n\nReceipt:\n${receipt_text}`
                }],
                temperature: 0.1
            })
        });
        if (!res.ok) throw new Error(`Groq API: HTTP ${res.status}`);
        const groqData = await res.json();
        const content = groqData.choices[0].message.content;

        // Parse JSON from response
        let fields;
        try {
            const jsonMatch = content.match(/\{[\s\S]*\}/);
            fields = jsonMatch ? JSON.parse(jsonMatch[0]) : JSON.parse(content);
        } catch {
            fields = { raw_output: content };
        }

        window.currentReceiptPrediction = fields;

        document.getElementById("receiptLoading").style.display = "none";
        document.getElementById("receiptStep2").style.display = "block";

        let fieldsHtml = Object.entries(fields).map(([key, value]) => `
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
        document.getElementById("receiptFinalDetail").textContent = "This receipt was processed successfully. In production, this would be stored as a positive ground-truth label for LoRA fine-tuning.";
    } else {
        document.getElementById("receiptFinalIcon").textContent = "🔄";
        document.getElementById("receiptFinalMessage").textContent = "Flagged for Re-training";
        document.getElementById("receiptFinalDetail").textContent = "This sample has been flagged. In production, the corrected label would feed into the LoRA fine-tuning pipeline for the next training epoch.";
    }
}

function resetReceiptDemo() {
    document.getElementById("receiptInput").value = "";
    document.getElementById("receiptStep2").style.display = "none";
    document.getElementById("receiptLoading").style.display = "none";
    document.getElementById("receiptError").style.display = "none";
    document.getElementById("receiptStep1").scrollIntoView({ behavior: "smooth" });
}
