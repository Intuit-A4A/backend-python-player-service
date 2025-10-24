# Architecture Diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                           │
│                                                                          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│  │    Slack     │      │   Cursor     │      │   Claude     │         │
│  │   Messages   │      │     IDE      │      │   Desktop    │         │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘         │
│         │                     │                     │                  │
└─────────┼─────────────────────┼─────────────────────┼──────────────────┘
          │                     │                     │
          │ Natural Language    │ stdio               │ SSE
          │ + Attachments       │ transport           │ transport
          │                     │                     │
┌─────────▼─────────────────────┼─────────────────────┼──────────────────┐
│                     ORCHESTRATION LAYER              │                  │
│                                                      │                  │
│  ┌────────────────────────────────────┐             │                  │
│  │      N8N Workflow Engine            │             │                  │
│  │  ┌──────────────────────────────┐  │             │                  │
│  │  │   GPT-4 AI Agent             │  │             │                  │
│  │  │   - Plan execution           │  │             │                  │
│  │  │   - Discover tools           │  │             │                  │
│  │  │   - Execute calls            │  │             │                  │
│  │  └──────────────────────────────┘  │             │                  │
│  └────────────────┬───────────────────┘             │                  │
│                   │                                  │                  │
└───────────────────┼──────────────────────────────────┼──────────────────┘
                    │                                  │
                    │ HTTP POST (SSE)                  │ stdio/SSE
                    │ to port 3001                     │
                    │                                  │
┌───────────────────▼──────────────────────────────────▼──────────────────┐
│                    PROTOCOL BRIDGE LAYER (YOUR MCP SERVER)               │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                     MCP Server Core                             │    │
│  │  ┌─────────────────────────────────────────────────────────┐   │    │
│  │  │            Tool Registry (7 tools)                       │   │    │
│  │  │  • create_offer    • edit_offer    • approve_offer      │   │    │
│  │  │  • submit_offer    • get_offer     • list_offers        │   │    │
│  │  │  • get_country_config                                   │   │    │
│  │  └─────────────────────────────────────────────────────────┘   │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │    │
│  │  │   stdio      │  │     SSE      │  │  REST        │        │    │
│  │  │  Transport   │  │  Transport   │  │  Wrapper     │        │    │
│  │  │  (Port -)    │  │ (Port 3001)  │  │ (Port 3005)  │        │    │
│  │  │              │  │              │  │              │        │    │
│  │  │  Cursor IDE  │  │  N8N/HTTP    │  │  Legacy APIs │        │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Intelligent Resolution Layer                         │  │
│  │  ┌─────────────────────┐      ┌─────────────────────────────┐   │  │
│  │  │  Country/State      │      │  Configuration Defaults     │   │  │
│  │  │  Lookup Engine      │      │  Processor                  │   │  │
│  │  │  - GraphQL queries  │      │  - @velocity-global engine  │   │  │
│  │  │  - 200+ countries   │      │  - Country-specific rules   │   │  │
│  │  └─────────────────────┘      └─────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────┬──────────────┬────────────────────────────┘
                               │              │
                               │ GraphQL      │ REST
                               │ (Queries)    │ (Mutations)
                               │              │
┌──────────────────────────────▼──────────────▼────────────────────────────┐
│                          DATA & BUSINESS LOGIC LAYER                      │
│                                                                           │
│  ┌───────────────────────────────┐    ┌────────────────────────────────┐│
│  │     GraphQL API               │    │      REST API                   ││
│  │  - Countries lookup           │    │  - Create offer                 ││
│  │  - States lookup              │    │  - Update offer                 ││
│  │  - Configuration queries      │    │  - Approve/Submit offer         ││
│  └───────────────────────────────┘    └────────────────────────────────┘│
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    Offer API Business Logic                          ││
│  │  - Job creation              - Validation                            ││
│  │  - Candidate management      - Compliance checks                     ││
│  │  - Offer lifecycle           - Country-specific rules                ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Creating an Offer

```
┌────────┐   Natural Language                    ┌─────────────┐
│ User   │   "Create offer for Jane Smith        │   Slack     │
│        │    as Software Engineer in CA         │   Message   │
└───┬────┘    with $150k salary"                 └──────┬──────┘
    │                                                    │
    │                                                    │
    ▼                                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│                        N8N Workflow                                │
│                                                                    │
│  Step 1: Parse Message                                            │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Extract: firstName="Jane", lastName="Smith",                 │ │
│  │          jobTitle="Software Engineer",                        │ │
│  │          state="CA", payrollSalary=150000                    │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                               ↓                                    │
│  Step 2: AI Agent Planning                                        │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ GPT-4 discovers available tools:                             │ │
│  │ • create_offer (has required fields)                         │ │
│  │ • Need: firstName, lastName, email, jobTitle,                │ │
│  │        country, payrollSalary                                │ │
│  │ Missing: email (will ask), country (infer from "CA")         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                               ↓                                    │
│  Step 3: Execute MCP Tool                                         │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Call: create_offer({                                         │ │
│  │   firstName: "Jane",                                         │ │
│  │   lastName: "Smith",                                         │ │
│  │   email: "jane@example.com",  // obtained via conversation   │ │
│  │   jobTitle: "Software Engineer",                             │ │
│  │   country: "United States",   // inferred from "CA"          │ │
│  │   state: "CA",                                               │ │
│  │   payrollSalary: 150000                                      │ │
│  │ })                                                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬───────────────────────────────────┘
                                 │ HTTP POST to /message
                                 │ (SSE session established)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Server (SSE Mode)                        │
│                                                                      │
│  Step 4: Validate Input                                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Zod Schema Validation:                                         │ │
│  │ ✓ firstName: string                                            │ │
│  │ ✓ email: valid email format                                    │ │
│  │ ✓ payrollSalary: number                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               ↓                                      │
│  Step 5: Resolve Location IDs                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ GraphQL Query: countriesByName(name: "United States")         │ │
│  │ → Returns: { id: "US_ID_123", name: "United States" }         │ │
│  │                                                                │ │
│  │ GraphQL Query: statesByCountry(countryId: "US_ID_123")        │ │
│  │ → Filter by name="CA" or iso_alpha_code="CA"                  │ │
│  │ → Returns: { id: "CA_ID_456", name: "California" }            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               ↓                                      │
│  Step 6: Apply Smart Defaults                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Config Engine:                                                 │ │
│  │ • startDate: today + 15 days (minimum required)                │ │
│  │ • isWorkerInCountry: true (default)                            │ │
│  │ • workingHoursPerWeek: 40 (CA default)                         │ │
│  │ • compensationModel: "SALARY" (always)                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               ↓                                      │
│  Step 7: Execute GraphQL Mutation                                   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ mutation startEmployeeOnboardingFromSkipQuote {                │ │
│  │   firstName: "Jane"                                            │ │
│  │   lastName: "Smith"                                            │ │
│  │   email: "jane@example.com"                                    │ │
│  │   jobTitle: "Software Engineer"                                │ │
│  │   countryId: "US_ID_123"                                       │ │
│  │   stateId: "CA_ID_456"                                         │ │
│  │   payrollSalary: 150000                                        │ │
│  │   startDate: "2025-11-08"                                      │ │
│  │   clientId: "CLIENT_ID"                                        │ │
│  │   isWorkerInCountry: true                                      │ │
│  │   compensationModel: "SALARY"                                  │ │
│  │   ... (20+ more fields)                                        │ │
│  │ }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ GraphQL mutation
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Offer API (Backend)                          │
│                                                                      │
│  Step 8: Create Job, Candidate, and Offer                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Transaction: {                                                 │ │
│  │   1. Create Job record                                         │ │
│  │      → jobId: "JOB_789"                                        │ │
│  │                                                                │ │
│  │   2. Create Candidate record                                   │ │
│  │      → candidateId: "CAND_012"                                 │ │
│  │                                                                │ │
│  │   3. Create Offer record                                       │ │
│  │      → offerId: "OFFER_345"                                    │ │
│  │      → status: "draft"                                         │ │
│  │      → links to Job and Candidate                              │ │
│  │ }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               ↓                                      │
│  Step 9: Return Response                                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ {                                                              │ │
│  │   "id": "OFFER_345",                                           │ │
│  │   "status": "draft",                                           │ │
│  │   "candidate": { "id": "CAND_012", ... },                      │ │
│  │   "job": { "id": "JOB_789", ... },                             │ │
│  │   "compensation": { "payrollSalary": 150000, ... }             │ │
│  │ }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ GraphQL response
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Server (SSE Mode)                        │
│                                                                      │
│  Step 10: Format Response                                           │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ "✅ Offer created successfully via GraphQL!                    │ │
│  │                                                                │ │
│  │ Offer ID: OFFER_345                                            │ │
│  │ Candidate: Jane Smith (jane@example.com)                       │ │
│  │ Position: Software Engineer                                    │ │
│  │ Location: California, United States                            │ │
│  │ Salary: $150,000                                               │ │
│  │ Start Date: 2025-11-08                                         │ │
│  │ Status: draft"                                                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ SSE response
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        N8N Workflow                                  │
│                                                                      │
│  Step 11: Send Confirmation                                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Post to Slack:                                                 │ │
│  │ "✅ Offer created successfully!                                 │ │
│  │                                                                │ │
│  │ Offer ID: OFFER_345                                            │ │
│  │ View offer: [link]                                             │ │
│  │                                                                │ │
│  │ Next steps:                                                    │ │
│  │ • Review offer details                                         │ │
│  │ • Type 'approve OFFER_345' to approve                          │ │
│  │ • Type 'edit OFFER_345' to make changes"                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
                             ┌────────┐
                             │  User  │
                             │ (Slack)│
                             └────────┘
                        "Offer created in 2 min!"
```

**Total Time: ~2 minutes** (down from 9.5 days!)

---

## MCP Protocol Communication Flow

```
┌──────────────┐                           ┌──────────────┐
│   MCP Client │                           │  MCP Server  │
│   (N8N/GPT4) │                           │  (Your Code) │
└──────┬───────┘                           └──────┬───────┘
       │                                          │
       │  1. Establish SSE Connection             │
       │─────────────────────────────────────────>│
       │  GET /sse                                │
       │                                          │
       │<─────────────────────────────────────────│
       │  event: endpoint                         │
       │  data: { "uri": "/message?sessionId=..." }│
       │                                          │
       │  2. Initialize MCP Session               │
       │─────────────────────────────────────────>│
       │  POST /message                           │
       │  { "jsonrpc": "2.0",                     │
       │    "method": "initialize",               │
       │    "params": { "capabilities": {...} }}  │
       │                                          │
       │<─────────────────────────────────────────│
       │  { "jsonrpc": "2.0",                     │
       │    "result": {                           │
       │      "serverInfo": { "name": "offer..." },│
       │      "capabilities": { "tools": {...} }  │
       │    }}                                    │
       │                                          │
       │  3. List Available Tools                 │
       │─────────────────────────────────────────>│
       │  POST /message                           │
       │  { "jsonrpc": "2.0",                     │
       │    "method": "tools/list" }              │
       │                                          │
       │<─────────────────────────────────────────│
       │  { "tools": [                            │
       │      { "name": "create_offer",           │
       │        "description": "...",             │
       │        "inputSchema": {...} },           │
       │      ...                                 │
       │    ]}                                    │
       │                                          │
       │  4. Call Tool (create_offer)             │
       │─────────────────────────────────────────>│
       │  POST /message                           │
       │  { "jsonrpc": "2.0",                     │
       │    "method": "tools/call",               │
       │    "params": {                           │
       │      "name": "create_offer",             │
       │      "arguments": {                      │
       │        "firstName": "Jane",              │
       │        "lastName": "Smith",              │
       │        ...                               │
       │      }                                   │
       │    }}                                    │
       │                                          │
       │         [MCP Server processes:]          │
       │         - Validates with Zod             │
       │         - Resolves country/state IDs     │
       │         - Applies defaults               │
       │         - Calls GraphQL API              │
       │         - Formats response               │
       │                                          │
       │<─────────────────────────────────────────│
       │  { "jsonrpc": "2.0",                     │
       │    "result": {                           │
       │      "content": [{                       │
       │        "type": "text",                   │
       │        "text": "✅ Offer created..."     │
       │      }],                                 │
       │      "isError": false                    │
       │    }}                                    │
       │                                          │
       │  5. Close Connection                     │
       │─────────────────────────────────────────>│
       │  (SSE connection closed)                 │
       │                                          │
       └──────────────────────────────────────────┘
```

---

## Session Management Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      SSE Server (Port 3001)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Session Management                             │  │
│  │                                                           │  │
│  │  Map<sessionId, {                                        │  │
│  │    transport: SSEServerTransport,                        │  │
│  │    createdAt: timestamp                                  │  │
│  │  }>                                                      │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │  │
│  │  │  Session 1  │  │  Session 2  │  │  Session 3  │     │  │
│  │  │  (Active)   │  │  (Active)   │  │  (Stale)    │     │  │
│  │  │  Age: 30s   │  │  Age: 45s   │  │  Age: 6min  │     │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │  │
│  │                                            ↓              │  │
│  │                                    Cleanup Timer          │  │
│  │                                    (every 60s)            │  │
│  │                                                           │  │
│  │  Cleanup Strategy:                                       │  │
│  │  1. On new connection: remove old sessions               │  │
│  │  2. Periodic: remove stale (>5min)                       │  │
│  │  3. On close: remove immediately                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Request Routing                                │  │
│  │                                                           │  │
│  │  POST /message receives request                          │  │
│  │          ↓                                               │  │
│  │  Find sessionId from:                                    │  │
│  │    1. x-mcp-session-id header                           │  │
│  │    2. Query param (?sessionId=...)                      │  │
│  │    3. URL path (/message/:sessionId)                    │  │
│  │    4. Use single active session (if only 1)             │  │
│  │    5. Use most recent session (if multiple)             │  │
│  │          ↓                                               │  │
│  │  Route to correct transport                              │  │
│  │          ↓                                               │  │
│  │  Handle MCP message                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

           Challenge: N8N creates new session per request
                           ↓
             Solution: Aggressive session cleanup
                     + Smart session routing
```

---

## Error Handling Flow

```
User Request
    ↓
┌───────────────────────────────────────┐
│  Validation Layer (Zod)               │
│  ├─ Type checking                     │
│  ├─ Required field validation         │
│  ├─ Format validation (email, etc)    │
│  └─ Custom business rules             │
└───────┬───────────────────────────────┘
        │
        ├──[Valid]──────────────────────┐
        │                               │
        ├──[Invalid]──> Return error    │
        │               with hint       │
        │                               │
        ▼                               ▼
┌───────────────────────────────────────┐
│  Location Resolution (GraphQL)        │
│  ├─ Country lookup                    │
│  ├─ State lookup                      │
│  └─ Nationality lookup                │
└───────┬───────────────────────────────┘
        │
        ├──[Found]─────────────────────┐
        │                              │
        ├──[Not Found]──> Return error │
        │                with suggestion│
        │                              │
        ▼                              ▼
┌───────────────────────────────────────┐
│  GraphQL Mutation                     │
│  ├─ startEmployeeOnboarding...       │
│  └─ Create job/candidate/offer       │
└───────┬───────────────────────────────┘
        │
        ├──[Success]────────────────────┐
        │                               │
        ├──[401 Unauthorized]──┐        │
        │                      ▼        │
        │            ┌─────────────────┐│
        │            │ Refresh Token   ││
        │            │ Retry Request   ││
        │            └─────────────────┘│
        │                      │        │
        ├──[400 Bad Request]───┼────────┤
        │                      │        │
        ├──[500 Server Error]──┼────────┤
        │                      │        │
        │                      ▼        ▼
        │            ┌─────────────────────┐
        │            │ Structured Error    │
        │            │ Response with:      │
        │            │ - Error message     │
        │            │ - Helpful hint      │
        │            │ - What to fix       │
        │            └─────────────────────┘
        │                      │
        ▼                      ▼
┌───────────────────────────────────────┐
│  Success Response                     │
│  ├─ Formatted text                    │
│  ├─ Offer ID                          │
│  ├─ Status                            │
│  └─ Next steps                        │
└───────────────────────────────────────┘
        │
        ▼
    User sees result
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Environment                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Docker Compose                           │ │
│  │                                                             │ │
│  │  ┌──────────────────────┐    ┌──────────────────────────┐ │ │
│  │  │  Container 1:        │    │  Container 2:            │ │ │
│  │  │  MCP SSE Server      │    │  N8N REST Wrapper        │ │ │
│  │  │                      │    │                          │ │ │
│  │  │  - Port: 3001        │    │  - Port: 3005            │ │ │
│  │  │  - Image: node:20    │◄───┤  - Image: node:20        │ │ │
│  │  │  - Env: API_TOKEN    │    │  - Env: MCP_URL          │ │ │
│  │  │  - Health: /health   │    │  - Health: /health       │ │ │
│  │  │  - Restart: always   │    │  - Restart: always       │ │ │
│  │  └──────────────────────┘    └──────────────────────────┘ │ │
│  │            ▲                           ▲                   │ │
│  └────────────┼───────────────────────────┼───────────────────┘ │
│               │                           │                     │
│  ┌────────────┼───────────────────────────┼───────────────────┐ │
│  │  Monitoring & Logging                  │                   │ │
│  │  - Health check endpoints              │                   │ │
│  │  - Structured JSON logs                │                   │ │
│  │  - Active session count                │                   │ │
│  │  - Error rate tracking                 │                   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS (Production)
                               │ HTTP (Development)
                               │
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  N8N Cloud   │    │ Offer API    │    │  Slack API   │     │
│  │  (Workflows) │    │  (Backend)   │    │  (Messages)  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                           │
│  • Slack UI                                                      │
│  • Natural language input                                        │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                           │
│  • N8N Workflow Engine                                          │
│  • OpenAI GPT-4 (AI Agent)                                      │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer (YOUR CODE)                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Runtime:    Node.js 20.x                                    ││
│  │ Language:   TypeScript 5.9                                  ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Frameworks:                                                 ││
│  │  • @modelcontextprotocol/sdk (MCP protocol)                 ││
│  │  • Express 4.18 (HTTP server)                               ││
│  │  • graphql-request 6.1 (GraphQL client)                     ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Validation & Types:                                         ││
│  │  • Zod 3.24 (Runtime validation)                            ││
│  │  • TypeScript (Compile-time types)                          ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Testing:                                                    ││
│  │  • Jest 29.7 (Unit tests)                                   ││
│  │  • ts-jest (TypeScript integration)                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Layer                           │
│  • Axios (HTTP client)                                          │
│  • EventSource (SSE client for REST wrapper)                    │
│  • @velocity-global/fields-engine (Config defaults)             │
└─────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────┐
│                       External APIs                              │
│  • GraphQL API (Queries: countries, states)                     │
│  • REST API (Mutations: create, update offers)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

These diagrams can be used in your presentation or drawn on a whiteboard during discussions. They clearly show the architecture, data flow, and technical decisions you made.

