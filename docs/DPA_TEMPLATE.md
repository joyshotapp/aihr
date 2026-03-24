# UniHR Data Processing Agreement (Template)

Last Updated: 2026-03-23

This Data Processing Agreement ("DPA") forms part of the Master Services Agreement, Order Form, or other written agreement (collectively, the "Agreement") between:

- Customer: [Customer Legal Name]
- Processor: UniHR / [Operating Entity Legal Name]

## 1. Purpose

This DPA governs UniHR's processing of Personal Data on behalf of Customer in connection with the UniHR SaaS platform.

## 2. Roles of the Parties

- Customer acts as Controller, or as Processor acting on behalf of its own controller.
- UniHR acts as Processor, or Sub-processor where Customer acts as Processor.

## 3. Subject Matter and Duration

- Subject matter: provision of UniHR document management, AI retrieval, chat, tenant administration, authentication, and support services.
- Duration: for the term of the Agreement and until Personal Data is deleted or returned in accordance with Section 10.

## 4. Nature and Purpose of Processing

UniHR may process Personal Data to:

- host and store customer-uploaded documents and metadata;
- authenticate users and manage tenant accounts;
- perform document parsing, search, retrieval, and AI-assisted responses;
- provide support, monitoring, backup, audit logging, and security operations;
- send transactional emails such as invitations, password reset, and service notices.

## 5. Categories of Personal Data

Depending on Customer's use of the service, Personal Data may include:

- user profile data such as name, work email, department, role, and login history;
- employee records and HR-related document content uploaded by Customer;
- usage logs, IP addresses, device/browser metadata, and audit records;
- support communications and administrative configuration data.

## 6. Categories of Data Subjects

- Customer employees, contractors, administrators, and authorized users;
- Customer end users whose data appears in uploaded HR documents;
- Customer support contacts and billing/technical contacts.

## 7. Customer Instructions

UniHR shall process Personal Data only on documented instructions from Customer, including as necessary to provide the service under the Agreement, unless otherwise required by applicable law.

## 8. Processor Obligations

UniHR shall:

- process Personal Data only as instructed by Customer;
- ensure personnel with access are bound by confidentiality obligations;
- implement appropriate technical and organizational security measures;
- assist Customer with data subject requests where legally required and technically feasible;
- notify Customer without undue delay after becoming aware of a confirmed Personal Data Breach affecting Customer Data;
- maintain records of sub-processors and update Customer of material changes where contractually required.

## 9. Security Measures

UniHR maintains security controls including, as applicable:

- tenant isolation and application/database access controls;
- role-based access control and audit logging;
- encryption in transit and protected infrastructure access;
- malware scanning for uploaded files;
- backup, monitoring, alerting, and incident response procedures;
- secrets management, least privilege, and change control practices.

Customer acknowledges that no security measure eliminates all risk and remains responsible for configuring access controls and uploading only authorized content.

## 10. Sub-processors

UniHR may engage sub-processors for infrastructure, storage, email delivery, monitoring, and AI model services. UniHR shall:

- maintain an internal sub-processor list;
- impose data protection obligations on sub-processors consistent with this DPA;
- remain responsible for sub-processor performance to the extent required by law and contract.

## 11. International Transfers

If Personal Data is transferred across borders, the parties will rely on an appropriate transfer mechanism under applicable law, such as contractual clauses, adequacy decisions, or other recognized safeguards.

## 12. Audit and Information Rights

Upon reasonable written request, UniHR will provide information reasonably necessary to demonstrate compliance with this DPA, subject to confidentiality, security, and scope limitations. On-site audits, if any, must be mutually agreed in advance and may be limited to once per year except where required by law or following a verified security incident.

## 13. Data Subject Requests

Where UniHR receives a request directly from a data subject relating to Customer Data, UniHR will:

- notify Customer unless prohibited by law;
- not respond substantively except on Customer's documented instruction or as required by law.

## 14. Security Incident Notification

UniHR will notify Customer without undue delay after confirming a Personal Data Breach affecting Customer Data. Such notice will include, to the extent available:

- nature of the incident;
- categories of affected data;
- likely consequences;
- containment and remediation steps taken or proposed.

## 15. Return and Deletion

Upon termination or upon Customer's documented request, UniHR will delete or return Customer Personal Data in accordance with the Agreement and UniHR's operational deletion procedures, unless retention is required by applicable law or backup recovery cycles.

## 16. Liability

Liability under this DPA is subject to the limitation of liability terms in the Agreement unless prohibited by applicable law.

## 17. Governing Terms

If there is a conflict between this DPA and the Agreement regarding Personal Data processing, this DPA controls to the extent of that conflict.

## Annex A. Processing Details

- Subject matter: SaaS knowledge base and HR assistant platform
- Frequency: continuous for the term of the Agreement
- Location: [Primary hosting region], with any approved backup or sub-processor regions
- Retention: per Agreement, support obligations, backup lifecycle, and deletion SOP

## Annex B. Sub-processor Register

| Sub-processor | Service | Data Processed | Location |
|---|---|---|---|
| Linode (Akamai) | Cloud hosting & compute | All platform data | US / configurable region |
| Cloudflare R2 | Object storage (uploaded documents) | Uploaded files (encrypted at rest) | Global / nearest region |
| Pinecone | Vector database | Document embeddings + metadata (tenant-isolated namespaces) | US-East (AWS) |
| Google (Gemini) | LLM answer generation | User queries + retrieved context (no storage) | US |
| Voyage AI | Text embedding & reranking | Document chunks + queries (no storage) | US |
| LlamaParse (LlamaIndex) | Document parsing (PDF/DOCX) | Uploaded file content (transient) | US |
| SendGrid (Twilio) | Transactional email delivery | Email addresses, email content | US |
| PostgreSQL (self-hosted) | Primary database | All structured data (RLS-isolated per tenant) | Same as hosting region |
| Redis (self-hosted) | Cache & task broker | Session tokens, rate limit counters | Same as hosting region |
| ClamAV (self-hosted) | Malware scanning | Uploaded file bytes (transient) | Same as hosting region |

## Signature Block

- Customer Authorized Signatory: ____________________
- Title: ____________________
- Date: ____________________

- UniHR Authorized Signatory: ____________________
- Title: ____________________
- Date: ____________________