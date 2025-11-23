

# **Automated Forensic Architecture Recovery: A Systematic Process for Deriving Software Models from Artifacts**

## **1\. The Imperative for Forensic Architecture Recovery**

The divergence between the documented architecture of a software system and its deployed reality is a fundamental entropy problem in software engineering. Traditional architectural recovery methods—relying on stakeholder interviews, whiteboard workshops, and manual documentation updates—are inherently flawed due to the limitations of human memory and the rapid velocity of modern Continuous Integration/Continuous Deployment (CI/CD) pipelines. As systems grow in complexity, shifting toward microservices and distributed infrastructures, the cognitive load required to maintain a mental model of the system exceeds human capacity. Consequently, the only reliable source of truth regarding a system's structure, behavior, and intent is the artifact itself: the source code, configuration manifests, infrastructure definitions, and runtime telemetry.

This report establishes a comprehensive, systematic process for "Forensic Architecture Recovery," a methodology that treats the software repository and its runtime environment as a crime scene from which architectural evidence must be extracted, correlated, and reconstructed. By eschewing subjective interpretation in favor of algorithmic derivation, this process leverages advanced techniques from code forensics, abstract syntax tree (AST) analysis, and distributed tracing to reconstruct high-fidelity representations of the system. We focus specifically on deriving four critical architectural views—the C4 System Context, Dynamic Sequence Diagrams, Conceptual Entity Relationship Diagrams (ERD), and Finite State Machine (FSM) diagrams—strictly from artifacts, eliminating the need for human intervention or workshops.

The methodology presented herein moves beyond simple visualization. It introduces a rigorous extraction pipeline that utilizes Infrastructure as Code (IaC) state files to define system boundaries, Object-Relational Mapping (ORM) metadata to construct conceptual data models, OpenTelemetry traces to map interaction sequences, and static control-flow analysis to uncover state transitions. Furthermore, we introduce verification techniques utilizing architectural fitness functions and runtime monitoring to ensure the derived models accurately reflect the operational system, providing a mechanism for continuous architectural observability.1

## **2\. Deriving the C4 System Context: Infrastructure and Dependency Forensics**

The C4 Context diagram represents the highest level of abstraction in the C4 model, depicting the software system in relation to its users and external systems. In a workshop-free environment, identifying these boundaries requires analyzing the "connective tissue" of the application—specifically, its deployment configurations and external dependency manifests. This layer of extraction focuses on the "System" and "Container" levels, identifying what the software is, where it runs, and what it talks to.

### **2.1. Infrastructure as Code (IaC) as the Source of Truth**

Modern cloud-native applications define their environment through code. Terraform, Kubernetes manifests, and Docker Compose files are authoritative sources for identifying the "Containers" and "External Systems" that constitute the C4 landscape. Unlike documentation, which describes what the system *should* be, IaC describes what the system *is*.

#### **2.1.1. Terraform State Analysis for System Boundaries**

The Terraform state file (terraform.tfstate) is a JSON representation of the deployed infrastructure. It serves as a definitive catalog of external resources—databases, message queues, third-party SaaS integrations—that the system interacts with. While static .tf configuration files describe the *intent* of the infrastructure, including conditional logic and variables that may not be resolved until runtime, the state file represents the *actual* resolved infrastructure after application. It contains the unique identifiers, connection endpoints, and configuration parameters of every live resource.4

To extract the C4 Context, one must parse the state file to identify resources that act as architectural boundaries. This involves filtering the massive JSON structure of the state file to locate specific resource types that denote external systems. Resources such as aws\_db\_instance, aws\_sqs\_queue, google\_sql\_database\_instance, or azurerm\_cosmosdb\_account represent persistent state stores or asynchronous messaging channels that form the nodes of a Context diagram. These resources are distinct from compute resources like EC2 instances or Lambda functions, which typically represent the internal processing nodes (Containers) of the system.6

The extraction logic employs tools like jq to traverse the state file's document object model. The process begins by iterating through the resources array. For each resource, the type field provides the semantic classification necessary to determine if the resource is an external dependency or an internal component. For instance, a resource type of pagerduty\_service or datadog\_monitor explicitly reveals a dependency on an external monitoring or alerting system, necessitating a relationship edge in the C4 diagram pointing to "PagerDuty" or "Datadog" respectively.8

Furthermore, the connectivity between these systems—the edges of the C4 diagram—can often be inferred from security group rules and IAM policies defined within the same state file. An aws\_security\_group\_rule that permits egress traffic on port 5432 to a specific CIDR block or peer security group ID establishes a verified communication path between the compute layer and a PostgreSQL database. Similarly, an IAM policy granting sqs:SendMessage permission to a specific Lambda function role confirms a directional relationship from the function to the queue. By extracting these "permission edges," the forensic analysis reconstructs the allowed pathways of data flow, often revealing connections that developers may have forgotten or implicitly assumed.10

**Table 1: Terraform Resource Mapping to C4 Context Elements**

| Terraform Resource Type | C4 Element Type | Inferred Relationship | Description |
| :---- | :---- | :---- | :---- |
| aws\_db\_instance | External System / Container | "Reads from / Writes to" | Represents a relational database dependency. |
| aws\_sqs\_queue | External System | "Publishes to / Consumes from" | Represents an asynchronous message broker. |
| aws\_s3\_bucket | Container (File Store) | "Stores blobs in" | Represents unstructured data storage. |
| pagerduty\_service | External System | "Alerts" | Represents a 3rd-party SaaS integration. |
| aws\_security\_group\_rule | Relationship Edge | "Connects via \[Port\]" | Defines network reachability between components. |
| aws\_iam\_role\_policy | Relationship Edge | "Authorized to \[Action\]" | Defines logical permission to interact. |

#### **2.1.2. Docker Compose for Localized Container Mapping**

For local development environments or simplified deployments, docker-compose.yml provides a self-contained view of the system context. It explicitly defines the services (Containers), their dependencies (depends\_on), and the networks they share. While Terraform manages the macro-infrastructure, Docker Compose often orchestrates the micro-service interactions.

The extraction strategy here employs yq (a YAML wrapper for jq) to parse the services keys in the compose file. Each key typically represents a "Container" in the C4 model. The analysis distinguishes between internal containers and external infrastructure based on the image directive. Services that build from a local context (build:.) are internal application containers. Services that use standard library images (e.g., postgres:14, redis:alpine, rabbitmq:management) represent "Infrastructure Containers" or external systems required for the local environment to function.12

The networks section of the Docker Compose file defines the explicit boundaries of communication. Services that share a common network have a pathway for communication, establishing potential edges in the C4 diagram. Moreover, the depends\_on directive provides a topological ordering of startup, which often implies a functional dependency—Service A cannot start until Database B is ready because Service A depends on Database B. This explicit dependency declaration allows for the automated generation of directional edges in the resulting diagram.14

### **2.2. Dependency Manifest Analysis: The Software Supply Chain**

Infrastructure code tells us about the hardware and cloud layer, but it often misses SaaS integrations that occur purely at the application level. An application might talk to the Stripe API or SendGrid via HTTP without ever provisioning a "resource" in Terraform. To find these hidden external systems, one must analyze the application's package manifests (package.json, pom.xml, go.mod). This technique, known as "System Dependency Mapping," correlates the presence of specific software libraries with the external systems they are designed to communicate with.16

#### **2.2.1. Semantic Dependency Mapping**

The presence of a client library SDK is a strong forensic indicator of an architectural relationship. If a project imports stripe-node, it is architecturally significant; it implies the system processes payments. This process relies on a "Knowledge Base" or a mapping table that correlates library names with the external systems they represent.

The extraction process involves scanning the dependencies section of package.json or the dependency nodes of pom.xml. For each dependency, the extractor checks against a curated list of known service providers. For example, finding aws-sdk implies a general dependency on AWS, but finding specifically boto3 or google-cloud-storage provides more granular insight. This semantic mapping allows the automated generation of "External System" boxes in the C4 Context diagram for SaaS providers that have no physical footprint in the user's own infrastructure.18

This static analysis is highly effective but susceptible to false positives—a library might be present in package.json but unused in the code (dead code). To mitigate this, advanced forensic analysis can cross-reference the manifest with import statements in the source code using tools like grep or ast-grep. If stripe is listed in dependencies but never imported in any .js or .ts file, the relationship is marked as "Potential Zombie Dependency" and excluded from the primary architectural view to reduce noise.21

#### **2.2.2. Code Forensics and Temporal Coupling**

Beyond explicit dependencies, forensic analysis of the version control history (Git logs) reveals hidden architectural coupling that static analysis might miss. This technique, popularized by Adam Tornhill's "Code as a Crime Scene" methodology, analyzes "Temporal Coupling"—the tendency of files to change together over time. If a change in BillingService.java is frequently accompanied by a change in ShippingService.java within the same commit, there is a high probability of a logical coupling between these components, even if no direct code dependency exists (e.g., they might share a common database schema or configuration file implicitly).1

By mining the git log, we can generate a "Coupling Graph." When extracting the C4 Context, strong temporal coupling between two distinct modules suggests they might need to be grouped into the same System or Container, or conversely, that an undocumented shared library exists between them. This historical data acts as a "behavioral" layer on top of the static "structural" layer derived from IaC and manifests, highlighting where the architectural boundaries are porous or ill-defined.24

### **2.3. Verification: Network Forensics and Drift Detection**

To verify that the statically derived C4 Context is accurate, one must confirm that the identified relationships actually exist in the runtime environment. This is "Verification by Execution." Static analysis models intent; dynamic analysis models reality.

In a running environment (e.g., staging or production), network connection tracking tools like netstat, ss, or eBPF-based monitors provide the ground truth of active connections. By aggregating established TCP connections and resolving the destination IP addresses, we can validate the external systems identified in the IaC and manifest analysis. If the static analysis predicts a dependency on a MySQL database (port 3306\) but the runtime analysis shows zero traffic to that port over a significant period, the dependency may be obsolete. Conversely, if netstat shows sustained traffic to an IP address owned by "Salesforce" but no Salesforce SDK appears in the package.json (perhaps because the interaction is done via raw fetch calls), the dynamic analysis uncovers a "Shadow Dependency" that must be added to the diagram.27

This verification step also serves as a "Drift Detection" mechanism. By querying the cloud provider's API (e.g., aws ec2 describe-instances) and comparing the result against the terraform.tfstate, we can identify unmanaged infrastructure. Any resource present in the live environment but missing from the state file represents "Shadow IT." Integrating this drift analysis into the architectural recovery process ensures that the diagram reflects the *actual* deployment, capturing manual changes made by operations teams outside of the standard IaC pipeline.6

## **3\. Deriving Conceptual ERDs: De-noising the Data Model**

Extracting an Entity Relationship Diagram (ERD) from a database schema is a trivial task supported by countless tools. However, extracting a *Conceptual* ERD—one that communicates business meaning without overwhelming the viewer with technical minutiae—is a significant challenge. A Physical ERD shows tables, columns, types, and indices; a Conceptual ERD must show Entities and Relationships. The "Conceptual" requirement implies a rigorous filtering process to hide implementation details like join tables, migration logs, technical auditing columns, and database-specific constraints.

### **3.1. Extraction Strategy: ORM Introspection over DDL**

Object-Relational Mapping (ORM) definitions, such as Hibernate Entities or Prisma Schemas, are superior to raw SQL Data Definition Language (DDL) for conceptual extraction because they often already encapsulate business intent. They define relationships as object references (e.g., @OneToMany) rather than mere foreign key constraints, providing a richer semantic basis for the diagram.

#### **3.1.1. Prisma Schema Analysis**

Prisma schemas (schema.prisma) are structurally concise and ideal for parsing. They explicitly define model (Entity) and relation (Relationship). To convert this physical schema into a conceptual view, we must apply strict "de-noising" algorithms during the generation process. Tools like prisma-erd-generator or prisma-markdown allow for configuration options that suppress technical details.29

The de-noising process involves several key heuristics. First, technical columns must be identified and stripped. We utilize ast-grep or regular expressions to identify fields named created\_at, updated\_at, deleted\_at, version, or audit\_id. These fields exist in almost every table for administrative purposes but add no value to a conceptual understanding of the domain. Removing them reduces the visual noise significantly, allowing the viewer to focus on business attributes like price, sku, or email.30

Second, "Join Models" must be collapsed. In a physical Many-to-Many relationship (e.g., Users and Groups), a join table (e.g., UserGroups) is required. In a conceptual diagram, this intermediate table is clutter; the relationship should be represented as a direct line between User and Group. The extraction algorithm identifies models that contain *only* two foreign keys (and perhaps a primary key/timestamp) and no other business data. These models are suppressed, and the relationships pointing to them are merged into a single Many-to-Many edge between the substantive entities.30

#### **3.1.2. Hibernate/JPA Entity Parsing**

For Java ecosystems, Hibernate entities annotated with @Entity provide the structural definitions. The challenge lies in distinguishing between "data fields" and "relationship fields." We employ static analysis using tools like Semgrep or JavaParser to extract relationships based on annotations rather than raw field types.

The extraction rule targets classes annotated with @Entity. Within these classes, it scans for fields annotated with relationship markers: @OneToMany, @ManyToOne, @OneToOne, and @ManyToMany. The targetEntity attribute or the field's type signature reveals the connected entity. Crucially, the mappedBy attribute in bidirectional relationships identifies the "owner" of the relationship, allowing the diagram generator to draw the arrow direction correctly (typically pointing toward the owner or parent entity). Fields annotated with @Transient or matching specific naming patterns (.\*Audit, .\*Log) are ignored, ensuring the generated Mermaid erDiagram syntax reflects the domain model rather than the persistence layer.32

**Table 2: Annotation to Diagram Mapping Logic**

| JPA Annotation | Diagram Cardinality | Extraction Logic |
| :---- | :---- | :---- |
| @OneToOne | \` |  |
| \-- |  |  |
| or | o-- |  |
| \` | Check @JoinColumn for optionality (nullable). |  |
| @OneToMany | \` |  |
| \--o{\` | Usually the inverse side; look for mappedBy. |  |
| @ManyToOne | \`}o-- |  |
| \` | The owning side; contains the Foreign Key logic. |  |
| @ManyToMany | }o--o{ | Implies a hidden join table; draw direct link. |
| @Transient | (Hidden) | Exclude field from diagram entirely. |

### **3.2. Extraction Strategy: Refining DDL for Conceptual Views**

In scenarios where ORM code is unavailable, we must fall back to reverse-engineering the SQL DDL. However, visualizing raw DDL results in diagrams cluttered with hundreds of columns. To achieve a conceptual view, we employ a "Key-Only" extraction strategy.

This heuristic suggests that for a high-level understanding of the database topology, one only needs to see the tables, the Primary Keys (PK), and the Foreign Keys (FK). All other columns are treated as attributes that can be hidden. This dramatically simplifies the visualization, highlighting the structural web of the database without the density of the row data. Tools like SchemaSpy support this through schemaMeta configuration files, which allow for regex-based column exclusion. By configuring a regex such as excludeColumns="(.\*\_id|created\_.\*|updated\_.\*|version)", we can systematically hide redundant FK columns (which are already represented by relationship lines) and audit columns, resulting in a clean, readable box for each entity.35

### **3.3. Verification: Data Integrity and Architectural Consistency**

A "Conceptual" ERD is a claim about the system's data rules (e.g., "Every Order must have a Customer"). To verify this claim, we compare the derived model against the actual data and the code that manages it.

We employ architectural fitness functions using tools like ArchUnit to verify that the relationships depicted in the ERD are respected in the codebase. For example, if the ERD implies a mandatory relationship, the code should not allow the persistence of an entity if the related entity is missing. ArchUnit can enforce rules such as "Entities annotated with @ManyToOne must have a non-nullable join column unless explicitly marked optional." Furthermore, we can run data quality queries against the live database (e.g., SELECT count(\*) FROM orders WHERE customer\_id IS NULL). If the count is greater than zero, the conceptual model's claim of a "Mandatory" relationship is falsified by the data, and the diagram must be updated to reflect the "Optional" reality. This aligns the architectural model with the empirical evidence of the data integrity.38

## **4\. Deriving Sequence Diagrams: Dynamic Behavior Analysis**

Sequence diagrams represent the "Fourth Dimension" of architecture: Time. They describe the runtime interaction between components, the order of operations, and the flow of messages. Deriving these statically from source code is notoriously difficult due to polymorphism, dynamic dispatch, and dependency injection, which obscure the actual call graph until runtime. Therefore, the systematic process for deriving sequence diagrams relies heavily on **Dynamic Analysis** via observability traces.

### **4.1. The OpenTelemetry Data Model as a Sequence Graph**

OpenTelemetry (OTel) traces provide a data structure that maps nearly one-to-one with the requirements of a sequence diagram. A "Trace" corresponds to a specific interaction scenario (e.g., "Checkout Flow"), and "Spans" correspond to the messages passed between participants.

The extraction process treats the trace as a directed acyclic graph (DAG) of operations. The traceId identifies the scenario bounding box. The process.serviceName or resource.attributes.service.name identifies the "Participants" (the lifelines in the diagram). The spanId and parentSpanId establish the causality and hierarchy—identifying who called whom. The startTime and endTime of spans determine the vertical sequence of events. By iterating over a JSON export of a trace, we can algorithmically reconstruct the sequence of execution.41

### **4.2. Algorithmic Trace-to-Mermaid Conversion**

The conversion of a trace into a Mermaid sequence diagram involves transforming the tree structure of the trace into the linear script format of Mermaid. This requires a specific algorithm to handle the ordering and nesting of calls.

**The Conversion Algorithm:**

1. **Participant Identification:** The algorithm iterates through all spans in the trace to collect unique service.name values. These are declared as participant elements in the Mermaid header. Heuristics are applied to distinguish between generic services and databases; spans with db.system attributes (e.g., postgresql) are mapped to database shapes in Mermaid to visually distinguish persistence calls from RPC calls.42
2. **Temporal Sorting:** Spans are sorted by their startTime. This ensures the visual flow of the diagram matches the chronological execution.
3. **Interaction Mapping:** For each span S, the algorithm looks up its parent span P. If P exists and belongs to a different service than S, an interaction arrow is generated: P.serviceName \-\>\> S.serviceName : S.operationName. This represents the request.
4. **Return Mapping:** The completion of span S implicitly represents a return of control to P. While Mermaid handles the lifeline activation automatically, explicit dotted return arrows (--\>\>) can be generated to indicate the response, potentially annotated with the HTTP status code found in the span attributes (http.status\_code).43
5. **Concurrency Handling:** Traces often capture asynchronous or parallel behavior. If two child spans (A and B) share the same parent and their time ranges overlap (i.e., A.start \< B.end and B.start \< A.end), they represent parallel execution. The extraction tool detects this overlap and wraps the corresponding Mermaid interactions in a par... end block, accurately visualizing the concurrency that manual diagrams often miss.44

Python Implementation Logic:
The core logic for this transformation involves a traversal of the span list. The following pseudo-code illustrates the extraction:

Python

def trace\_to\_mermaid(trace\_json):
    print("sequenceDiagram")
    \# Sort by start time to ensure chronological order
    spans \= sorted(trace\_json\['spans'\], key=lambda x: x)

    for span in spans:
        parent \= find\_span\_by\_id(spans, span)
        if parent:
            source \= parent\['serviceName'\]
            target \= span\['serviceName'\]
            action \= span\['operationName'\]

            \# Only map cross-service calls
            if source\!= target:
                 print(f"{source}\-\>\>{target}: {action}")
                 \# Check for attributes like HTTP status or DB queries
                 if 'db.statement' in span\['attributes'\]:
                     print(f"Note right of {target}: {span\['attributes'\]\['db.statement'\]}")

This automated generation allows specific traces—such as those capturing error conditions or high-latency requests—to be instantly visualized for debugging.43

### **4.3. Integration Tests as "Living Documentation"**

We cannot always rely on production traffic to generate diagrams for every possible scenario. To ensure comprehensive coverage, we utilize Integration Tests as proxies for user behavior. Integration tests are essentially "codified scenarios," forcing the system through specific paths (e.g., "User Login," "Password Reset").

We can instrument the test runner (e.g., JUnit for Java, Jest for Node.js) with a custom listener that acts as an observability hook. When a test begins, the listener generates a unique TraceID. As the test executes, the standard OpenTelemetry instrumentation collects spans associated with that ID. Upon test completion, the listener fetches all spans for that TraceID and passes them to the conversion algorithm described above. The result is a generated .mmd (Mermaid) file saved alongside the test code. This creates a "Living Documentation" loop: whenever the tests run (e.g., in CI/CD), the sequence diagrams are regenerated. If a developer changes the logic to add a new API call, the test will pass, and the diagram will automatically update to reflect the new call, ensuring the documentation never drifts from the code.47

### **4.4. Verification: Trace Comparison and Drift Analysis**

To verify the accuracy of the derived sequence diagrams, we employ a technique of "Diffing." We establish a "Golden Master" diagram for critical flows (e.g., the Checkout sequence), which is manually reviewed and approved. On subsequent builds, the diagram generated from the integration tests is compared against this Golden Master. If the hash of the new diagram differs—indicating a change in the sequence of calls—the build system flags a "Architectural Drift" warning. This alerts architects to unintended side effects, such as an N+1 query problem introduced by a seemingly innocent code change, where a loop in the code creates a loop in the sequence diagram that was not present before.49

## **5\. Deriving State Machine Diagrams: Extracting Logic from Code**

State Machines are often implicit, buried in boolean flags, switch statements, or conditional logic chains. They represent the rules of the road for entities, dictating valid transitions (e.g., an Order cannot move from PENDING to SHIPPED without passing through PAID). The goal of forensic recovery here is to make these implicit machines explicit via Static Analysis.

### **5.1. Static Analysis of Control Flow and Enums**

Explicit state machines usually revolve around enum types and the control structures that manipulate them. The switch statement is the canonical implementation of a Finite State Machine (FSM) in imperative languages.

#### **5.1.1. Enum-Driven Extraction via ast-grep**

We utilize Abstract Syntax Tree (AST) analysis tools like ast-grep to find the definition of states and the transitions between them. The analysis focuses on identifying the "State Variable"—typically a field named status, state, or stage—and the methods that mutate it.

The extraction logic searches for the "Switch-Case" pattern. In this pattern, a service method switches on the current state of an entity and, within a specific case block, performs an assignment to a new state. This assignment represents a transition.

**Analysis Pattern:**

1. **Identify States:** Scan the codebase for Enum definitions (e.g., enum OrderStatus { NEW, PAID, SHIPPED }). These constitute the nodes of the state machine.
2. **Identify Transitions:** Use ast-grep to find assignments where the Enum value is updated.
3. **Contextual Analysis:** Analyze the Control Flow Graph (CFG) surrounding the assignment. If the assignment order.status \= SHIPPED occurs inside a case PAID: block, or inside an if (order.status \== PAID) block, we have forensically identified a transition PAID \--\> SHIPPED.50

Implementation with ast-grep Rules:
We can write structural search rules to automate this. A YAML configuration for ast-grep can target these patterns specifically using relational rules like inside and pattern.

YAML

id: extract-state-transition
language: java
rule:
  kind: assignment\_expression
  pattern: $OBJ.setStatus($NEW\_STATE)
  inside:
    kind: if\_statement
    has:
      kind: binary\_expression
      pattern: $OBJ.getStatus() \== $OLD\_STATE

The matches from this rule provide a tuple ($OLD\_STATE, $NEW\_STATE), which can be trivially converted into Mermaid syntax: OLD\_STATE \--\> NEW\_STATE.52

#### **5.1.2. Symbolic Execution for Implicit Machines**

In legacy code, state is often not represented by a single Enum but by clusters of boolean flags (e.g., is\_paid, is\_shipped, is\_cancelled). This constitutes an "Implicit State Machine." Extracting this requires more advanced techniques like Symbolic Execution.

The forensic logic involves identifying "mutually exclusive" updates. If the code sets is\_processing to false and is\_complete to true within the same transactional block, this represents a state transition. We analyze the code to find all reachable combinations of these boolean flags. Each unique combination (e.g., Paid=False, Shipped=False) represents a discrete state (e.g., "New"). Methods that change these boolean values represent the transitions. By mapping all possible boolean permutations and the code paths that connect them, we can reverse-engineer the implicit state table into an explicit state diagram, revealing the hidden complexity of the legacy logic.54

### **5.2. Verification: Model Checking and Reachability Analysis**

Once a State Machine is extracted, we must verify it against logical consistency and business rules. The generated diagram is treated as a directed graph, allowing us to apply standard graph algorithms.

Reachability Analysis:
We perform Breadth-First Search (BFS) or Depth-First Search (DFS) on the extracted graph to identify anomalies.

* **Dead States:** States that can be entered but have no outgoing transitions (sinks). While "Cancelled" might be a valid dead state, "Processing" should likely not be.
* **Unreachable States:** States that have no incoming transitions (islands). If the analysis finds an Enum value that is never assigned in the code (except perhaps in initialization), it represents dead code or an unreachable state.

Logical Consistency Check:
We check for forbidden transitions defined by business requirements. If the business rule states "You cannot go from REFUNDED to SHIPPED," but the extracted model shows a path (perhaps via a transient intermediate state like PENDING\_SHIPMENT), the code contains a logical bug. This verification step turns the State Machine diagram into a diagnostic tool for logic errors.3

## **6\. Synthesis: The Architecture-as-Code Pipeline**

The individual diagrams—Context, Sequence, ERD, and State—are not isolated artifacts; they are interconnected views of the same system. The C4 Context defines *where* the Sequence happens; the Sequence shows *how* the ERD entities are manipulated; and the State Machine dictates *when* specific Sequence flows are valid.

To make this process systematic and sustainable, these extraction strategies must be integrated into the CI/CD pipeline, creating a "Architecture-as-Code" feedback loop.

1. **Commit:** A developer pushes code to the repository.
2. **Static Extraction:** The build pipeline runs ast-grep to extract state transitions and parses terraform.tfstate and package.json to update the C4 Context. The Conceptual ERD is regenerated from the Prisma/Hibernate definitions.
3. **Dynamic Generation:** The integration test suite executes. The OTel listener captures trace logs for every test scenario, generating updated Sequence Diagrams for critical flows.
4. **Drift Analysis:** The newly generated diagrams are compared against the version stored in the main branch. Significant topological changes—such as a new edge in the C4 diagram (new dependency) or a new transition in the State Machine—trigger an "Architecture Review" warning on the Pull Request. This ensures that architectural changes are explicit and reviewed, preventing the silent erosion of the system's design.21

This "Forensic Architecture Recovery" methodology transforms architecture from a static, manually curated artifact into a dynamic, verifiable property of the system itself. By utilizing the tools of code forensics—Terraform parsers, OTel tracers, AST analyzers—we uncover the structural truth hidden within the codebase, allowing teams to understand their systems not as they *wish* them to be, but as they *actually* are.

#### **Works cited**

1. smontanari/code-forensics: A toolset for code analysis and report visualisation \- GitHub, accessed November 22, 2025, [https://github.com/smontanari/code-forensics](https://github.com/smontanari/code-forensics)
2. Your Architecture as a Crime Scene\! Forensic Analysis for Your Angular Solutions \- ANGULARarchitects \- Manfred Steyer, accessed November 22, 2025, [https://www.angulararchitects.io/blog/your-architecture-as-a-crime-scene-forensic-analysis-for-your-angular-solutions/](https://www.angulararchitects.io/blog/your-architecture-as-a-crime-scene-forensic-analysis-for-your-angular-solutions/)
3. On the Execution and Runtime Verification of UML Activity Diagrams \- MDPI, accessed November 22, 2025, [https://www.mdpi.com/2674-113X/4/1/4](https://www.mdpi.com/2674-113X/4/1/4)
4. AI Terraform Diagram Generator \- Eraser, accessed November 22, 2025, [https://www.eraser.io/ai/terraform-diagram-generator](https://www.eraser.io/ai/terraform-diagram-generator)
5. Best Tools to Visualize your Terraform \- DEV Community, accessed November 22, 2025, [https://dev.to/miketysonofthecloud/best-tools-to-visualize-your-terraform-252a](https://dev.to/miketysonofthecloud/best-tools-to-visualize-your-terraform-252a)
6. Output data from Terraform \- HashiCorp Developer, accessed November 22, 2025, [https://developer.hashicorp.com/terraform/tutorials/configuration-language/outputs](https://developer.hashicorp.com/terraform/tutorials/configuration-language/outputs)
7. Deep State: Extract Code and Resources From the Terraform State File | by Joe Tavin, accessed November 22, 2025, [https://betterprogramming.pub/deep-state-create-terraform-code-from-the-state-file-b64b3c924af3](https://betterprogramming.pub/deep-state-create-terraform-code-from-the-state-file-b64b3c924af3)
8. Infragram \- Visual Studio Marketplace, accessed November 22, 2025, [https://marketplace.visualstudio.com/items?itemName=infragram.infragram](https://marketplace.visualstudio.com/items?itemName=infragram.infragram)
9. How to use jq to extract a particular field from a terraform plan to show resources that are updated or changed? \- Stack Overflow, accessed November 22, 2025, [https://stackoverflow.com/questions/75263431/how-to-use-jq-to-extract-a-particular-field-from-a-terraform-plan-to-show-resour](https://stackoverflow.com/questions/75263431/how-to-use-jq-to-extract-a-particular-field-from-a-terraform-plan-to-show-resour)
10. System architecture diagram basics & best practices \- vFunction, accessed November 22, 2025, [https://vfunction.com/blog/architecture-diagram-guide/](https://vfunction.com/blog/architecture-diagram-guide/)
11. Get specific value out of the Terraform state file \- Stack Overflow, accessed November 22, 2025, [https://stackoverflow.com/questions/57811596/get-specific-value-out-of-the-terraform-state-file](https://stackoverflow.com/questions/57811596/get-specific-value-out-of-the-terraform-state-file)
12. The C4 Model Explained: Clearer Software Architecture Diagrams with Structurizr \- Devōt, accessed November 22, 2025, [https://devot.team/blog/c4-model](https://devot.team/blog/c4-model)
13. Yq: retrieve object keys names \- Stack Overflow, accessed November 22, 2025, [https://stackoverflow.com/questions/55280071/yq-retrieve-object-keys-names](https://stackoverflow.com/questions/55280071/yq-retrieve-object-keys-names)
14. Big feature: generate C4 from docker-compose.yml and ansible · Issue \#120 \- GitHub, accessed November 22, 2025, [https://github.com/plantuml-stdlib/C4-PlantUML/issues/120](https://github.com/plantuml-stdlib/C4-PlantUML/issues/120)
15. Combine docker compose files using yq : r/selfhosted \- Reddit, accessed November 22, 2025, [https://www.reddit.com/r/selfhosted/comments/v8jdw2/combine\_docker\_compose\_files\_using\_yq/](https://www.reddit.com/r/selfhosted/comments/v8jdw2/combine_docker_compose_files_using_yq/)
16. System Dependency Mapping \- Technique D3-SYSDM \- MITRE D3FEND, accessed November 22, 2025, [https://d3fend.mitre.org/technique/d3f:SystemDependencyMapping/](https://d3fend.mitre.org/technique/d3f:SystemDependencyMapping/)
17. Application Dependency Mapping: Tutorial & Best Practices | Multiplayer, accessed November 22, 2025, [https://www.multiplayer.app/system-architecture/application-dependency-mapping/](https://www.multiplayer.app/system-architecture/application-dependency-mapping/)
18. package.json \- npm Docs, accessed November 22, 2025, [https://docs.npmjs.com/files/package.json/](https://docs.npmjs.com/files/package.json/)
19. POM Reference \- Apache Maven, accessed November 22, 2025, [https://maven.apache.org/pom.html](https://maven.apache.org/pom.html)
20. package.json: Your Project's Navigator for Success\! | by Ravi Chandola | Medium, accessed November 22, 2025, [https://medium.com/@ravichandola/package-json-your-projects-navigator-for-success-c440f74a4277](https://medium.com/@ravichandola/package-json-your-projects-navigator-for-success-c440f74a4277)
21. About the dependency graph \- GitHub Docs, accessed November 22, 2025, [https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph](https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-the-dependency-graph)
22. How to Use a Dependency Graph to Analyze Dependencies \- Jit.io, accessed November 22, 2025, [https://www.jit.io/resources/app-security/how-to-use-a-dependency-graph-to-analyze-dependencies](https://www.jit.io/resources/app-security/how-to-use-a-dependency-graph-to-analyze-dependencies)
23. Your Code as a Crime Scene, accessed November 22, 2025, [http://www.r-5.org/files/books/computers/dev-teams/trenches/Adam\_Tornhill-Your\_Code\_as\_a\_Crime\_Scene-EN.pdf](http://www.r-5.org/files/books/computers/dev-teams/trenches/Adam_Tornhill-Your_Code_as_a_Crime_Scene-EN.pdf)
24. Your Code as a Crime Scene: Use Forensic Techniques to Arrest Defects, Bottlenecks, and Bad Design in Your Programs by Adam Tornhill, accessed November 22, 2025, [https://pragprog.com/titles/atcrime/your-code-as-a-crime-scene/](https://pragprog.com/titles/atcrime/your-code-as-a-crime-scene/)
25. Temporal Coupling — CodeScene 1.7.0 Documentation, accessed November 22, 2025, [https://docs.enterprise.codescene.io/versions/1.7.0/guides/technical/temporal-coupling.html](https://docs.enterprise.codescene.io/versions/1.7.0/guides/technical/temporal-coupling.html)
26. Kill the Clones: How Change Coupling helps you identify Design Problems in large-scale Systems \- Adam Tornhill, accessed November 22, 2025, [https://www.adamtornhill.com/articles/aspnetclones/killtheclones.html](https://www.adamtornhill.com/articles/aspnetclones/killtheclones.html)
27. Digital Forensics: Get Started with These 9 Open Source Tools \- BlueVoyant, accessed November 22, 2025, [https://www.bluevoyant.com/knowledge-center/get-started-with-these-9-open-source-tools](https://www.bluevoyant.com/knowledge-center/get-started-with-these-9-open-source-tools)
28. How to identify and map service dependencies \- Gremlin, accessed November 22, 2025, [https://www.gremlin.com/blog/how-to-identify-and-map-service-dependencies](https://www.gremlin.com/blog/how-to-identify-and-map-service-dependencies)
29. Stop drawing ERD, but just auto-generate by \`prisma-markdown\` \- DEV Community, accessed November 22, 2025, [https://dev.to/samchon/stop-drawing-erd-but-just-auto-generate-by-prisma-markdown-3ckj](https://dev.to/samchon/stop-drawing-erd-but-just-auto-generate-by-prisma-markdown-3ckj)
30. keonik/prisma-erd-generator: Generate an ER Diagram based on your Prisma schema every time you run npx prisma generate \- GitHub, accessed November 22, 2025, [https://github.com/keonik/prisma-erd-generator](https://github.com/keonik/prisma-erd-generator)
31. Think twice before you map entity associations with Hibernate | by Przemysław Żochowski, accessed November 22, 2025, [https://dev-vibe.medium.com/think-twice-before-you-map-entity-associations-with-hibernate-a09173dda9c0](https://dev-vibe.medium.com/think-twice-before-you-map-entity-associations-with-hibernate-a09173dda9c0)
32. Java Hibernate Reverse Engineering Tutorial with Eclipse and MySQL \- CodeJava.net, accessed November 22, 2025, [https://www.codejava.net/frameworks/hibernate/java-hibernate-reverse-engineering-tutorial-with-eclipse-and-mysql](https://www.codejava.net/frameworks/hibernate/java-hibernate-reverse-engineering-tutorial-with-eclipse-and-mysql)
33. Hibernate Inheritance Mapping | Baeldung, accessed November 22, 2025, [https://www.baeldung.com/hibernate-inheritance](https://www.baeldung.com/hibernate-inheritance)
34. Effective Relationship Mapping with Hibernate & JPA: @OneToMany \- Medium, accessed November 22, 2025, [https://medium.com/javarevisited/effective-relationship-mapping-with-hibernate-jpa-onetomany-c80324a94e53](https://medium.com/javarevisited/effective-relationship-mapping-with-hibernate-jpa-onetomany-c80324a94e53)
35. Removing clutter from ERD diagrams \-- suggestion : r/Database \- Reddit, accessed November 22, 2025, [https://www.reddit.com/r/Database/comments/xv05qo/removing\_clutter\_from\_erd\_diagrams\_suggestion/](https://www.reddit.com/r/Database/comments/xv05qo/removing_clutter_from_erd_diagrams_suggestion/)
36. Configuration — SchemaSpy 6.0.0 documentation \- Read the Docs, accessed November 22, 2025, [https://schemaspy.readthedocs.io/en/v6.0.0/configuration.html](https://schemaspy.readthedocs.io/en/v6.0.0/configuration.html)
37. SchemaMeta — SchemaSpy 6.0.0 documentation \- Read the Docs, accessed November 22, 2025, [https://schemaspy.readthedocs.io/en/master/configuration/schemaMeta.html](https://schemaspy.readthedocs.io/en/master/configuration/schemaMeta.html)
38. ArchUnit User Guide, accessed November 22, 2025, [https://www.archunit.org/userguide/html/000\_Index.html](https://www.archunit.org/userguide/html/000_Index.html)
39. Validating the Implementation against the Model (with ArchUnit) | Context Mapper, accessed November 22, 2025, [https://contextmapper.org/docs/architecture-validation-with-archunit/](https://contextmapper.org/docs/architecture-validation-with-archunit/)
40. Use cases of data and Schemaspy: Database Management | by Juilee Talele \- Medium, accessed November 22, 2025, [https://juileetalele.medium.com/use-cases-of-data-and-schemaspy-database-management-6e4c43c383e2](https://juileetalele.medium.com/use-cases-of-data-and-schemaspy-database-management-6e4c43c383e2)
41. Traces | OpenTelemetry, accessed November 22, 2025, [https://opentelemetry.io/docs/concepts/signals/traces/](https://opentelemetry.io/docs/concepts/signals/traces/)
42. How we used ClickHouse to store OpenTelemetry Traces and up our Observability Game, accessed November 22, 2025, [https://clickhouse.com/blog/how-we-used-clickhouse-to-store-opentelemetry-traces](https://clickhouse.com/blog/how-we-used-clickhouse-to-store-opentelemetry-traces)
43. How to Generate Mermaid Sequence Diagrams from Code Using GPT \- Medium, accessed November 22, 2025, [https://medium.com/@swapnil.more\_24578/how-to-generate-mermaid-sequence-diagrams-from-code-using-gpt-7800ace119c5](https://medium.com/@swapnil.more_24578/how-to-generate-mermaid-sequence-diagrams-from-code-using-gpt-7800ace119c5)
44. Understand sequence diagram and trace distributed applications with Open Telemetry/PlantUml SDK \- Medium, accessed November 22, 2025, [https://medium.com/@wirelesser/understand-sequence-diagram-and-trace-distributed-applications-with-open-telemetry-plantuml-sdk-ace13688de74](https://medium.com/@wirelesser/understand-sequence-diagram-and-trace-distributed-applications-with-open-telemetry-plantuml-sdk-ace13688de74)
45. Fun project of the week, Mermaid flowcharts generator\! | by Alain Airom (Ayrom) | Medium, accessed November 22, 2025, [https://alain-airom.medium.com/fun-project-of-the-week-mermaid-flowcharts-generator-0bc74404e9e6](https://alain-airom.medium.com/fun-project-of-the-week-mermaid-flowcharts-generator-0bc74404e9e6)
46. Is there anyone with better idea for parsing Mermaid sequence diagrams : r/golang \- Reddit, accessed November 22, 2025, [https://www.reddit.com/r/golang/comments/1lx1mtk/is\_there\_anyone\_with\_better\_idea\_for\_parsing/](https://www.reddit.com/r/golang/comments/1lx1mtk/is_there_anyone_with_better_idea_for_parsing/)
47. \[1302.5170\] Sequence Diagram Test Case Specification and Virtual Integration Analysis using Timed-Arc Petri Nets \- arXiv, accessed November 22, 2025, [https://arxiv.org/abs/1302.5170](https://arxiv.org/abs/1302.5170)
48. Generating sequence diagrams from tests : r/golang \- Reddit, accessed November 22, 2025, [https://www.reddit.com/r/golang/comments/c067sa/generating\_sequence\_diagrams\_from\_tests/](https://www.reddit.com/r/golang/comments/c067sa/generating_sequence_diagrams_from_tests/)
49. Event-Driven Systems & Loosely Coupled Architectures Explained \- Temporal, accessed November 22, 2025, [https://temporal.io/blog/event-driven-systems-and-the-truth-about-loosely-coupled-architectures](https://temporal.io/blog/event-driven-systems-and-the-truth-about-loosely-coupled-architectures)
50. Finite State Machines in C \- enums \- Stack Overflow, accessed November 22, 2025, [https://stackoverflow.com/questions/50165534/finite-state-machines-in-c](https://stackoverflow.com/questions/50165534/finite-state-machines-in-c)
51. Dataflow and State Machine Extraction from C/C++ Code \- Christian-Albrechts-Universität zu Kiel, accessed November 22, 2025, [https://rtsys.informatik.uni-kiel.de/\~biblio/downloads/theses/lan-mt.pdf](https://rtsys.informatik.uni-kiel.de/~biblio/downloads/theses/lan-mt.pdf)
52. llms-full.txt \- ast-grep, accessed November 22, 2025, [https://ast-grep.github.io/llms-full.txt](https://ast-grep.github.io/llms-full.txt)
53. How to write ast-grep rules in these case? \- Stack Overflow, accessed November 22, 2025, [https://stackoverflow.com/questions/78118826/how-to-write-ast-grep-rules-in-these-case](https://stackoverflow.com/questions/78118826/how-to-write-ast-grep-rules-in-these-case)
54. Automated Finite State Machine Extraction \- Linhai Song, accessed November 22, 2025, [https://songlh.github.io/paper/feast02.pdf](https://songlh.github.io/paper/feast02.pdf)
55. Cleaning up business logic with state machines | by Tim \- Inside HeliosX, accessed November 22, 2025, [https://inside.heliosx.com/cleaning-up-business-logic-with-state-machines-393f2e7e9646](https://inside.heliosx.com/cleaning-up-business-logic-with-state-machines-393f2e7e9646)
56. How accurate is "Business logic should be in a service, not in a model"?, accessed November 22, 2025, [https://softwareengineering.stackexchange.com/questions/218011/how-accurate-is-business-logic-should-be-in-a-service-not-in-a-model](https://softwareengineering.stackexchange.com/questions/218011/how-accurate-is-business-logic-should-be-in-a-service-not-in-a-model)
57. Dependency scanning by using SBOM \- GitLab Docs, accessed November 22, 2025, [https://docs.gitlab.com/user/application\_security/dependency\_scanning/dependency\_scanning\_sbom/](https://docs.gitlab.com/user/application_security/dependency_scanning/dependency_scanning_sbom/)
