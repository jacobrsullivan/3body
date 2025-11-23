# C4 Context Diagram Rules

## Core Principle

C4 Context diagrams show **WHAT exists** and **who/what talks to whom**, NOT how things are implemented.

**Target Audience**: Non-technical stakeholders who need to understand system boundaries and dependencies.

## Mandatory Elements

### 1. People
- Users and stakeholders who interact with the system
- Use `Person(id, "Name", "Description")`
- Examples: Research Scientist, Administrator, CI System

### 2. Systems (Internal)
- Major subsystems within the project boundary
- Use `System(id, "Name", "Description")`
- Group related modules into 3-7 logical systems (not every file)

### 3. System_Ext (External)
- Dependencies outside the project boundary
- Separate processes, external APIs, datastores
- Use `System_Ext(id, "Name", "Description")`
- Examples: HDF5 Storage, PySR Engine, External API

### 4. Relationships
- Cross-boundary interactions
- Use `Rel(source, target, "Plain English description")`
- Show WHAT happens, not HOW

## Strict Rules

### ✓ ALLOWED
- Plain English descriptions
- Business/domain terminology
- Conceptual names ("Storage", "Integration Service")
- Purpose-based labels ("Stores trajectories", "Validates integrals")

### ✗ FORBIDDEN

#### Technology/Protocol Details
- Protocol names: HTTP, REST, gRPC, SOAP, WebSocket, AMQP
- Data formats: JSON, XML, Protobuf, Avro
- Transport: TCP, UDP, SSL/TLS
- Authentication: OAuth, JWT, API keys

**Violation**: "REST API on port 8080"
**Fix**: "Integration Service"

#### Vendor/Product Names
- Cloud providers: AWS, Azure, GCP, DigitalOcean
- Databases: PostgreSQL, MongoDB, Redis, Cassandra
- Infrastructure: Kubernetes, Docker, Nomad
- Services: S3, Lambda, Cloud Functions

**Violation**: "AWS S3 bucket for storage"
**Fix**: "Trajectory Storage"

#### Implementation Details
- Port numbers: 8080, 5432, 27017
- IP addresses: 192.168.1.1, localhost:3000
- Hostnames: api.example.com, db-01.internal
- API endpoints: /api/v1/validate, /health
- Class names: IntegrationEngine, ValidationGauntlet (in code sense)
- File paths: src/python/integrators/, /data/trajectories/

**Violation**: "Sends POST to /api/v1/validate"
**Fix**: "Requests validation"

#### Physical Architecture
- Deployment topology: master-slave, active-passive
- Scaling: horizontal scaling, load balancing
- Infrastructure: virtual machines, containers, serverless

**Violation**: "Kubernetes cluster with 3 nodes"
**Fix**: "Integration Platform"

## Abstraction Level

### Correct Level: Conceptual
```mermaid
System(validator, "Validation Service", "Validates candidate integrals")
System_Ext(storage, "Trajectory Storage", "Persists orbital data")
Rel(validator, storage, "Reads trajectories")
```

### Too Detailed: Implementation
```mermaid
✗ System(validator_api, "FastAPI REST service on port 8000", "...")
✗ System_Ext(s3, "AWS S3 bucket s3://trajectories-prod", "...")
✗ Rel(validator_api, s3, "HTTP GET via boto3 SDK")
```

### Too Vague: Not Helpful
```mermaid
✗ System(thing, "The System", "Does stuff")
✗ Rel(user, thing, "Interacts")
```

## Relationship Labels

### Good Labels
- "Configures experiments"
- "Stores trajectories"
- "Requests validation"
- "Reports results to"
- "Uses for computation"

### Bad Labels
- "Calls /api/validate" (implementation)
- "Sends JSON via HTTPS" (technical)
- "POST request" (protocol)
- "Uses" (too vague)

## System Boundary

### What Goes Inside `System_Boundary`
- Code developed for THIS project
- Custom subsystems in `src/`
- Project-specific modules

### What Goes Outside (System_Ext)
- Third-party libraries invoked as separate processes
- External APIs and services
- Datastores (file-based, databases)
- Separate codebases (even if open source)

### Judgment Calls

**Case**: Integrated library (e.g., numpy, scipy)
- **Decision**: NOT shown (it's a code dependency, not a system)
- **Rationale**: Imported directly, not a separate runtime entity

**Case**: External process (e.g., PySR via Julia)
- **Decision**: System_Ext (separate process)
- **Rationale**: IPC communication, different runtime

**Case**: File-based storage (e.g., HDF5 files)
- **Decision**: System_Ext (external data store)
- **Rationale**: Persistent storage outside application boundary

## Naming Conventions

### People
- Use roles, not names: "Research Scientist" not "Dr. Smith"
- Capitalize each word: "CI System", "Admin User"

### Systems
- Use descriptive names: "Integration Engine", "Validation Service"
- Avoid code module names: "integrators.py" → "Integration Engine"
- Capitalize each word

### Descriptions
- Complete sentences: "Generates high-precision trajectories"
- Focus on purpose: WHAT it does for users
- Avoid implementation: HOW it does it

## Validation Checklist

Before submitting diagram, verify:

- [ ] No protocol names (HTTP, REST, gRPC, etc.)
- [ ] No vendor names (AWS, Docker, Kubernetes, etc.)
- [ ] No port numbers or IP addresses
- [ ] No API endpoints or URLs
- [ ] No class names or file paths
- [ ] All labels understandable by non-developers
- [ ] Relationships show purpose, not mechanism
- [ ] 3-7 internal systems (not too granular)
- [ ] External systems are truly separate entities
- [ ] System_Boundary clearly defined

## Examples: Before and After

### Example 1: Integration System

**Before** (violates rules):
```mermaid
System(api, "Python FastAPI app on port 8080", "REST endpoints for integration")
System_Ext(hpc, "SLURM cluster with 64 cores", "Runs parallel jobs")
Rel(api, hpc, "Submits jobs via SSH")
```

**After** (compliant):
```mermaid
System(integration, "Integration Service", "Manages trajectory generation")
System_Ext(compute, "HPC Platform", "Executes parallel computations")
Rel(integration, compute, "Submits computational jobs")
```

### Example 2: Data Storage

**Before** (violates rules):
```mermaid
System_Ext(s3, "AWS S3 bucket in us-east-1", "Object storage")
Rel(app, s3, "Uploads HDF5 files via boto3")
```

**After** (compliant):
```mermaid
System_Ext(storage, "Trajectory Storage", "Persistent data repository")
Rel(app, storage, "Stores trajectory data")
```

### Example 3: External Services

**Before** (violates rules):
```mermaid
System_Ext(julia, "Julia 1.9 process running PySR", "Symbolic regression")
Rel(ml, julia, "Sends data via JSON-RPC")
```

**After** (compliant):
```mermaid
System_Ext(pysr, "PySR Engine", "Symbolic regression service")
Rel(ml, pysr, "Discovers candidate integrals")
```

## Common Mistakes

### Mistake 1: Showing Libraries as Systems
```
✗ System_Ext(numpy, "NumPy 1.24", "Array operations")
```
**Why Wrong**: NumPy is imported code, not a separate system
**Fix**: Don't show it in C4 Context

### Mistake 2: Implementation in Relationships
```
✗ Rel(a, b, "HTTP POST with JSON payload to /validate endpoint")
```
**Why Wrong**: Describes HOW, not WHAT
**Fix**: Rel(a, b, "Requests validation")

### Mistake 3: Too Many Internal Systems
```
✗ Showing 20+ Systems (one per Python module)
```
**Why Wrong**: Too granular, loses big picture
**Fix**: Group into 3-7 logical subsystems

### Mistake 4: Missing System Boundary
```
✗ All systems at same level, no boundary distinction
```
**Why Wrong**: Unclear what's inside vs outside project
**Fix**: Use System_Boundary to group internal systems

---

**Rules Version**: 1.0
**Created**: 2025-11-23
**Authority**: 4 Abstractions Implementation Guide
