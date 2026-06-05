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
    
    const tStatus = document.getElementById("tooltipStatus");
    const tLatency = document.getElementById("tooltipLatency");
    const tEngine = document.getElementById("tooltipEngine");
    const tRequests = document.getElementById("tooltipRequests");
    const tCost = document.getElementById("tooltipCost");
    
    const start = performance.now();
    try {
        const res = await fetch(`${API_URLS.control_plane}/health`, { signal: AbortSignal.timeout(3000) });
        const latency = Math.round(performance.now() - start);
        if (res.ok) {
            const data = await res.json();
            
            dot.className = "status-dot online";
            text.textContent = `Control Plane Online (${latency}ms)`;
            
            if (tStatus) {
                tStatus.textContent = "Online";
                tStatus.className = "online";
            }
            if (tLatency) tLatency.textContent = `${latency}ms`;
            
            // Format LLM Engine info nicely
            if (tEngine) {
                const provider = (data.llm_provider || "unknown").toUpperCase();
                const model = data.llm_model || "unknown";
                tEngine.textContent = `${provider} (${model})`;
            }
            
            if (data.metrics) {
                if (tRequests) tRequests.textContent = (data.metrics.counters?.requests_total || 0).toLocaleString();
                if (tCost) tCost.textContent = `$${(data.metrics.cost_estimate_usd || 0).toFixed(4)}`;
            }
        } else { throw new Error(); }
    } catch {
        dot.className = "status-dot offline";
        text.textContent = "Control Plane Offline";
        if (tStatus) {
            tStatus.textContent = "Offline";
            tStatus.className = "offline";
        }
        if (tLatency) tLatency.textContent = "—";
        if (tEngine) tEngine.textContent = "—";
        if (tRequests) tRequests.textContent = "—";
        if (tCost) tCost.textContent = "—";
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
        document.getElementById("demoError").style.display = "block";
        document.getElementById("errorMessage").textContent = err.message;
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
                const targetWidth = bar.dataset.width || bar.style.width;
                bar.style.width = "0%";
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        bar.style.width = targetWidth;
                    });
                });
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

    if (type === "bi") {
        initGenieSpace();
    }
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
        const res = await fetch(`${API_URLS.control_plane}/api/v1/workflows/invoke`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                workflow_id: "evaluation-workflow",
                session_id: "eval-" + Date.now(),
                inputs: { context: { mode: "evaluate" } }
            })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const responseData = await res.json();
        const data = responseData.state;

        document.getElementById("evalLoading").style.display = "none";
        document.getElementById("evalResults").style.display = "block";

        const aggregate = data.aggregate || {};
        const flagged = data.flagged || [];

        const displayScores = {
            avg_faithfulness: aggregate.avg_faithfulness,
            avg_relevance: aggregate.avg_relevance,
            avg_correctness: aggregate.avg_correctness,
            total_evaluated: aggregate.total_evaluated
        };

        const scoresHtml = Object.entries(displayScores).map(([key, value]) => `
            <div class="class-badge">
                <span class="class-label">${key.replace(/_/g, ' ')}</span>
                <span class="class-value ${typeof value === 'number' && key.startsWith('avg_') ? (value >= 0.85 ? 'low' : (value >= 0.7 ? 'normal' : 'urgent')) : 'info'}">${typeof value === 'number' && key.startsWith('avg_') ? (value * 100).toFixed(1) + '%' : (value !== undefined ? value : '0')}</span>
            </div>
        `).join('');

        document.getElementById("evalScores").innerHTML = scoresHtml;

        if (flagged.length > 0) {
            document.getElementById("evalFlagged").textContent = JSON.stringify(flagged, null, 2);
        } else {
            document.getElementById("evalFlagged").textContent = "No items flagged for manual review. All tests passed above the threshold.";
        }

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
    if (!receipt_text) return;

    document.getElementById("processReceiptBtn").disabled = true;
    document.getElementById("receiptLoading").style.display = "block";
    document.getElementById("receiptStep2").style.display = "none";
    document.getElementById("receiptError").style.display = "none";

    try {
        const res = await fetch(`${API_URLS.control_plane}/api/v1/workflows/invoke`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                workflow_id: "extraction-workflow",
                session_id: "receipt-" + Date.now(),
                inputs: { context: { receipt_text } }
            })
        });
        if (!res.ok) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server Error (HTTP ${res.status})`);
        }
        const responseData = await res.json();
        const fields = responseData.state.fields || {};

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

// ===================================================================
// GENIE DATA ROOM — Conversational Data Agent
// ===================================================================

let genieHistory = [];         // conversation history [{role, content}]
let genieChartInstance = null; // current Chart.js instance
let genieSchemaCache = null;   // cached schema from /api/v1/bi-schema

// -- Reset session ---------------------------------------------------
function resetGenieSession() {
    genieHistory = [];
    if (genieChartInstance) {
        genieChartInstance.destroy();
        genieChartInstance = null;
    }
    const messages = document.getElementById("genieMessages");
    if (messages) {
        messages.innerHTML = "";
        messages.style.display = "none";
    }
    const welcome = document.getElementById("genieWelcome");
    if (welcome) welcome.style.display = "block";
    const input = document.getElementById("genieInput");
    if (input) {
        input.value = "";
        input.style.height = "44px";
    }
}

// -- Schema Sidebar Exploration --------------------------------------

async function initGenieSpace() {
    if (genieSchemaCache) return;

    const schemaInfo = document.getElementById("genieSchemaInfo");
    const tableList = document.getElementById("genieTableList");
    if (schemaInfo) schemaInfo.textContent = "Loading schema…";

    try {
        const res = await fetch(`${API_URLS.control_plane}/api/v1/bi-schema`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        genieSchemaCache = data;

        if (tableList) {
            tableList.innerHTML = "";
            const schema = data.schema || {};
            for (const [tableName, columns] of Object.entries(schema)) {
                // Table item
                const li = document.createElement("li");
                li.className = "genie-table-item";
                
                // Get record count if available in previews
                const rows = data.previews?.[tableName]?.rows?.length || 0;
                const rowBadge = rows > 0 ? `<span class="genie-badge" style="font-size:0.75rem; background:rgba(99,102,241,0.2); color:var(--accent-blue); padding:2px 6px; border-radius:10px; margin-left:8px;">${rows}+ rows</span>` : "";
                
                // Create table header collapse toggle
                li.innerHTML = `
                    <div class="genie-table-header" onclick="toggleGenieTableSchema('${tableName}')" style="cursor: pointer; display: flex; align-items: center; padding: 6px 8px; border-radius: var(--radius-sm); transition: background 0.2s;">
                        <span class="genie-table-icon" style="margin-right: 8px;">📂</span>
                        <span class="genie-table-name" style="font-weight: 500; color: var(--text-primary); font-size: 0.9rem;">${tableName}</span>
                        ${rowBadge}
                    </div>
                    <ul class="genie-column-list" id="genieColList-${tableName}" style="display: none; list-style: none; padding-left: 24px; margin-top: 4px; margin-bottom: 8px;">
                        ${columns.map(col => `
                            <li style="display: flex; align-items: center; gap: 6px; padding: 3px 0; color: var(--text-muted); font-size: 0.82rem;">
                                <span class="genie-col-icon" style="opacity: 0.5;">#</span>
                                <span class="genie-col-name">${col}</span>
                            </li>
                        `).join("")}
                    </ul>
                `;
                
                // Hover effect for table header
                const header = li.querySelector(".genie-table-header");
                header.addEventListener("mouseenter", () => header.style.background = "rgba(255,255,255,0.04)");
                header.addEventListener("mouseleave", () => header.style.background = "transparent");

                tableList.appendChild(li);
            }
        }
        if (schemaInfo) schemaInfo.style.display = "none";
    } catch (err) {
        if (schemaInfo) schemaInfo.textContent = "Failed to load schema: " + err.message;
    }
}

function toggleGenieTableSchema(tableName) {
    const list = document.getElementById(`genieColList-${tableName}`);
    if (list) {
        const isHidden = list.style.display === "none";
        list.style.display = isHidden ? "block" : "none";
        const header = list.previousElementSibling;
        if (header) {
            const icon = header.querySelector(".genie-table-icon");
            if (icon) icon.textContent = isHidden ? "📁" : "📂";
        }
    }
}

function toggleGenieSidebar() {
    const sidebar = document.getElementById("genieSidebar");
    if (sidebar) {
        sidebar.classList.toggle("open");
    }
}

// -- Keyboard: Enter sends, Shift+Enter newline ----------------------

function genieInputKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendGenieChat();
    }
}

// -- Quick question buttons ------------------------------------------

function sendGenieQuestion(text) {
    document.getElementById("genieInput").value = text;
    sendGenieChat();
}

// -- Core send -------------------------------------------------------

async function sendGenieChat() {
    const input = document.getElementById("genieInput");
    const question = input.value.trim();
    if (!question) return;

    input.value = "";
    input.style.height = "44px";

    // Hide welcome, show messages
    document.getElementById("genieWelcome").style.display = "none";

    // Append user bubble
    appendGenieMessage("user", question);

    // Disable send button, show loading
    document.getElementById("genieSendBtn").disabled = true;
    document.getElementById("genieThinking").style.display = "block";

    // Add to history
    genieHistory.push({ role: "user", content: question });

    try {
        const res = await fetch(`${API_URLS.control_plane}/api/v1/bi-chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question,
                session_id: "genie-" + Date.now(),
                history: genieHistory.slice(-8)  // last 4 turns
            })
        });

        const data = await res.json();
        document.getElementById("genieThinking").style.display = "none";

        if (!res.ok || data.status === "error") {
            const errMsg = data.error || data.detail || `HTTP ${res.status}`;
            appendGenieErrorMessage(data.generated_sql || "", errMsg);
            genieHistory.push({ role: "assistant", content: `Error: ${errMsg}` });
        } else {
            appendGenieResultMessage(data, question);
            genieHistory.push({ role: "assistant", content: data.summary || "" });
        }

    } catch (err) {
        document.getElementById("genieThinking").style.display = "none";
        appendGenieErrorMessage("", err.message);
    }

    document.getElementById("genieSendBtn").disabled = false;
    // Auto-scroll chat window
    const win = document.getElementById("genieMessages");
    if (win) win.scrollTop = win.scrollHeight;
}

// -- Render helpers --------------------------------------------------

function appendGenieMessage(role, text) {
    const container = document.getElementById("genieMessages");
    const div = document.createElement("div");
    div.className = `genie-msg genie-msg-${role}`;
    const label = role === "user" ? "You" : "Genie Agent";
    div.innerHTML = `
        <div class="genie-msg-label">${label}</div>
        <div class="genie-bubble-${role}">${escapeHtml(text)}</div>
    `;
    container.appendChild(div);
    container.style.display = "block";
}

function appendGenieResultMessage(data, question) {
    const container = document.getElementById("genieMessages");
    const msgId = "genieMsg" + Date.now();
    const chartId = "genieChart" + Date.now();

    // Build table HTML
    let tableHtml = "";
    if (data.columns && data.columns.length > 0) {
        const headerCells = data.columns.map((c, idx) => 
            `<th onclick="sortGenieTable('${msgId}', ${idx})" style="cursor: pointer; user-select: none;" title="Click to sort">${escapeHtml(c)} ↕</th>`
        ).join("");
        const bodyRows = (data.rows || []).map(row =>
            `<tr>${row.map(v => `<td title="${escapeHtml(String(v || ''))}">${escapeHtml(String(v ?? "—"))}</td>`).join("")}</tr>`
        ).join("");
        tableHtml = `
            <div class="genie-row-count">${data.row_count || data.rows?.length || 0} row(s) returned</div>
            <div class="genie-results-table-wrap">
                <table class="genie-results-table">
                    <thead><tr>${headerCells}</tr></thead>
                    <tbody>${bodyRows}</tbody>
                </table>
            </div>`;
    }

    // Build chart HTML placeholder
    let chartHtml = "";
    if (data.chart_config && data.chart_config.labels && data.chart_config.labels.length > 0) {
        chartHtml = `<div class="genie-chart-wrap"><canvas id="${chartId}"></canvas></div>`;
    }

    // Generate context-aware follow-ups
    const followUpsHtml = generateFollowUps(question || "", data);

    const div = document.createElement("div");
    div.className = "genie-msg genie-msg-agent";
    div.id = msgId;
    div.innerHTML = `
        <div class="genie-msg-label">Genie Agent</div>
        <div class="genie-bubble-agent">
            <div class="genie-sql-label">Generated SQL</div>
            <pre class="genie-sql-block">${escapeHtml(data.generated_sql || "")}</pre>
            <div class="genie-summary">${escapeHtml(data.summary || "")}</div>
            ${tableHtml}
            ${chartHtml}
            ${followUpsHtml}
        </div>
    `;
    container.appendChild(div);
    container.style.display = "block";

    // Render chart after DOM insertion
    if (chartHtml && data.chart_config) {
        requestAnimationFrame(() => renderGenieChart(chartId, data.chart_config));
    }
}

function appendGenieErrorMessage(sql, errMsg) {
    const container = document.getElementById("genieMessages");
    const div = document.createElement("div");
    div.className = "genie-msg genie-msg-agent";
    div.innerHTML = `
        <div class="genie-msg-label">Genie Agent</div>
        <div class="genie-bubble-agent">
            ${sql ? `<div class="genie-sql-label">Generated SQL</div><pre class="genie-sql-block">${escapeHtml(sql)}</pre>` : ""}
            <div class="genie-error-msg">⚠️ ${escapeHtml(errMsg)}</div>
        </div>
    `;
    container.appendChild(div);
    container.style.display = "block";
}

function renderGenieChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (typeof Chart === "undefined") return;

    // Theme-aware colors
    const textColor = getComputedStyle(document.body).getPropertyValue("--text-secondary") || "#a0a0b8";
    const gridColor = "rgba(255,255,255,0.06)";

    const chartConfig = {
        type: config.type || "bar",
        data: {
            labels: config.labels,
            datasets: config.datasets || []
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: { duration: 500 },
            plugins: {
                legend: {
                    display: config.datasets && config.datasets.length > 1,
                    labels: { color: textColor, font: { size: 11 } }
                },
                title: {
                    display: !!config.title,
                    text: config.title || "",
                    color: textColor,
                    font: { size: 12, weight: "600" }
                }
            },
            scales: config.type === "doughnut" || config.type === "pie" ? {} : {
                x: {
                    ticks: { color: textColor, font: { size: 10 }, maxRotation: 45 },
                    grid: { color: gridColor }
                },
                y: {
                    ticks: { color: textColor, font: { size: 10 } },
                    grid: { color: gridColor }
                }
            }
        }
    };

    // Destroy existing chart instance to prevent memory leaks
    if (genieChartInstance) {
        genieChartInstance.destroy();
    }
    genieChartInstance = new Chart(canvas, chartConfig);
}

// -- Follow-up and Sorting Helpers -----------------------------------

function generateFollowUps(question, data) {
    const qLower = question.toLowerCase();
    const suggestions = [];

    if (qLower.includes("transaction") || qLower.includes("fraud") || qLower.includes("class")) {
        suggestions.push("Compare average transaction amount for fraud vs non-fraud cases");
        suggestions.push("Show details of the top 5 largest fraud transactions");
        suggestions.push("Show transaction count by class");
    } else if (qLower.includes("sec") || qLower.includes("filing") || qLower.includes("form") || qLower.includes("ticker") || qLower.includes("symbol")) {
        suggestions.push("Show the trend of SEC filings filed by year");
        suggestions.push("Which ticker symbol has the most SEC filings?");
        suggestions.push("List the unique forms filed by symbol 'TSLA'");
    } else {
        suggestions.push("Show summary statistics of this dataset");
        suggestions.push("Can you plot this data as a line chart?");
    }

    if (suggestions.length === 0) return "";
    
    return `
        <div class="genie-followups">
            ${suggestions.map(s => `<span class="genie-followup-chip" onclick="sendGenieQuestion('${escapeHtml(s)}')">${escapeHtml(s)}</span>`).join("")}
        </div>
    `;
}

let sortDirections = {}; // Cache to keep track of sort direction for each message and column index

function sortGenieTable(msgId, colIdx) {
    const msgDiv = document.getElementById(msgId);
    if (!msgDiv) return;
    const table = msgDiv.querySelector(".genie-results-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll("tr"));

    // Toggle direction
    const sortKey = `${msgId}-${colIdx}`;
    const desc = !sortDirections[sortKey];
    sortDirections[sortKey] = desc;

    // Sort rows
    rows.sort((a, b) => {
        const aVal = a.cells[colIdx].textContent.trim();
        const bVal = b.cells[colIdx].textContent.trim();
        
        // Try numerical sort
        const aNum = parseFloat(aVal.replace(/,/g, ""));
        const bNum = parseFloat(bVal.replace(/,/g, ""));
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return desc ? bNum - aNum : aNum - bNum;
        }
        
        // Fallback string sort
        return desc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
    });

    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));

    // Update header icons for visual feedback
    const headers = table.querySelectorAll("th");
    headers.forEach((th, idx) => {
        const baseText = th.textContent.replace(/[↕▲▼]/g, "").trim();
        if (idx === colIdx) {
            th.textContent = baseText + (desc ? " ▼" : " ▲");
        } else {
            th.textContent = baseText + " ↕";
        }
    });
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

