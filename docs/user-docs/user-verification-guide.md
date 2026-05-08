# AI-Q Blueprint User Verification Guide

This guide helps you verify that your AI-Q Blueprint deployment is working correctly by testing the core features through the web interface.

## Prerequisites

- AI-Q Blueprint deployed to your cluster
- Frontend is deployed and route is available in OpenShift

## Step 1: Access the Application

1. Open your web browser
2. Navigate to the frontend app route under Networking/Routes in the OpenShift cluster:
3. The Red Hat Research interface should load

**Expected Result:** The chat interface appears with a text input box at the bottom and the Red Hat branding.
---

## Step 2: Test Simple Greeting (Meta Intent)

This tests the orchestrator's ability to classify and handle conversational queries.

**Action:** Type the following and press Enter:
```
Hello
```

**Expected Result:**
- Response appears within **2-5 seconds**
- Friendly greeting that explains AI-Q capabilities
- No research or citations shown (this is a meta/conversational response)

**What this verifies:** Orchestrator model is working and can classify intent correctly.

---

## Step 3: Test Shallow Research

This tests web search integration and the researcher agent.

**Action:** Type:
```
What is Red Hat OpenShift?
```

**Expected Result:**
- Response appears within **10-30 seconds**
- Answer includes factual information about OpenShift
- **Sources/citations** appear at the bottom or inline
- References to recent information (not outdated)

**What this verifies:**
- Intent classification (research vs meta)
- Researcher agent functionality
- Web search tool integration
- Citation generation

---

## Step 4: Test Deep Research

This tests the multi-step deep research workflow.

**Action:** Type:
```
Provide a comprehensive analysis of Kubernetes security best practices
```

**Expected Result:**
- Status indicator shows "Research in Progress" or similar
- You may see intermediate research steps/status updates
- Response takes **2-5 minutes** to complete
- Final output is a **structured report** with:
  - Multiple sections/headings
  - Detailed analysis
  - Citations throughout
  - Sources listed at the end

**What this verifies:**
- Deep research agent workflow
- Multi-step planning
- Long-form report generation
- Extended reasoning capability

---

## Step 5: Test Follow-Up and Context

This tests conversation memory and summarization.

**Action:** After any research response from Step 3 or 4, type:
```
Can you summarize that in 2-3 sentences?
```

**Expected Result:**
- Response appears within **5-15 seconds**
- Concise summary that references the previous answer
- Maintains context from the conversation

**What this verifies:**
- Conversation context retention
- Summary model functionality
- Follow-up query handling

---

## Step 6: Test Technical Query

This tests the system's ability to handle domain-specific questions.

**Action:** Type:
```
How do I deploy a containerized application on OpenShift?
```

**Expected Result:**
- Response within **15-30 seconds**
- Technical details with step-by-step guidance
- Sources from OpenShift documentation or trusted technical sites
- Code examples or commands (if applicable)

**What this verifies:**
- Technical domain knowledge
- Quality of research sources
- Practical answer generation

---

## Verification Checklist

After completing all steps, confirm the following:

- [ ] UI loads without errors
- [ ] Simple greeting works (Step 2)
- [ ] Shallow research returns cited answers (Step 3)
- [ ] Deep research generates long-form reports (Step 4)
- [ ] Follow-up questions maintain context (Step 5)
- [ ] Technical queries work correctly (Step 6)
- [ ] Response times are reasonable (not timing out)
- [ ] Citations/sources appear in research responses
- [ ] No error messages in the UI

---

## Common Issues and Solutions

### Issue: "Failed to fetch" or Connection Errors

**Possible Causes:**
- Backend pod is not running
- Network connectivity issues
- Route/ingress misconfiguration

**What to do:** Report to your administrator with the exact error message.

---

### Issue: Responses Have No Citations

**Possible Causes:**
- Web search tools not configured
- API keys missing for search services
- Researcher agent not using tools

**What to do:** Try Step 3 again. If still no citations, report to administrator.

---

### Issue: Very Slow Responses (>2 minutes for shallow research)

**Possible Causes:**
- Model servers under heavy load
- Insufficient GPU resources
- Network latency to model endpoints

**What to do:** Note the query that was slow and report to administrator.

---

### Issue: Generic or Incorrect Answers

**Possible Causes:**
- Models not loaded correctly
- Wrong configuration file
- Model endpoint mismatch

**What to do:** 
1. Try Step 2 (greeting) - if this works, models are responding
2. Try a different research query
3. Report specific incorrect responses to administrator

---

### Issue: Deep Research Never Completes

**Possible Causes:**
- Backend timeout settings
- Planning agent stuck in loop
- Model inference failure

**What to do:**
1. Refresh the page
2. Try a simpler deep research query: "What is machine learning?"
3. If still fails, report to administrator

---

## What to Report

If you encounter issues, provide your administrator with:

1. **Which step failed:** (e.g., "Step 3: Shallow Research")
2. **Exact query you entered:** Copy-paste what you typed
3. **What happened:** Describe the result or error message
4. **Screenshot:** If possible, capture the UI showing the issue
5. **Browser:** Which browser and version you're using
6. **Time:** When the issue occurred (helps correlate with logs)

---

## Success Criteria

Your deployment is **fully functional** if:

✅ All 6 test steps complete successfully  
✅ Citations appear in research responses  
✅ Deep research generates structured reports  
✅ Response times are reasonable  
✅ Follow-up questions work  
✅ No error messages appear  

Your deployment **needs attention** if:
3q
⚠️ Simple queries work but deep research fails  
⚠️ Responses work but have no citations  
⚠️ Some queries timeout but others work  
❌ UI doesn't load  
❌ All queries return errors  
❌ Responses are blank or nonsensical  
❌ Connection errors appear  

---

## Advanced Testing (Optional)

### Test Multi-Turn Conversation

Have a back-and-forth conversation:
1. "What is Kubernetes?"
2. "What are the main components?"
3. "How does the scheduler work?"
4. "Compare it to Docker Swarm"

**Expected:** Each response should build on previous context.

### Test Edge Cases

Try queries that might challenge the system:
- Very long questions (200+ words)
- Questions in different domains (science, history, technology)
- Questions asking for comparisons
- Questions asking for opinions (should acknowledge limitations)

### Test File Upload (if enabled)

If your deployment supports document upload:
1. Upload a PDF or text file
2. Ask questions about the document content
3. Verify responses reference the uploaded content

---

## Next Steps

For additional features and configuration options, see the [main README](../README.md) and [Deployment Guide](DEPLOYMENT-GUIDE.md).
