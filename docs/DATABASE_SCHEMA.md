# Database Schema (PostgreSQL)

The AI Financial Crime Investigation Platform relies on a normalized relational database schema (PostgreSQL) with `pgvector` for vector embeddings.

## Tables

### Users and RBAC
1. `users`
   - `id` (UUID, PK)
   - `email` (String, Unique)
   - `hashed_password` (String)
   - `full_name` (String)
   - `role_id` (UUID, FK -> roles.id)
   - `is_active` (Boolean)
   - `created_at` (Timestamp)
   - `updated_at` (Timestamp)

2. `roles`
   - `id` (UUID, PK)
   - `name` (String, Unique) e.g., 'Admin', 'Analyst', 'Investigator'
   - `permissions` (JSONB)
   - `created_at` (Timestamp)

### Core Banking (Synthetic Data)
3. `customers`
   - `id` (UUID, PK)
   - `first_name` (String)
   - `last_name` (String)
   - `date_of_birth` (Date)
   - `email` (String, Unique)
   - `phone_number` (String)
   - `address` (String)
   - `country` (String)
   - `risk_score` (Float) - Pre-calculated baseline risk score
   - `created_at` (Timestamp)

4. `accounts`
   - `id` (UUID, PK)
   - `customer_id` (UUID, FK -> customers.id)
   - `account_number` (String, Unique)
   - `account_type` (String) e.g., 'checking', 'savings', 'business'
   - `balance` (Decimal)
   - `currency` (String)
   - `status` (String) e.g., 'active', 'dormant', 'suspended'
   - `created_at` (Timestamp)

5. `transactions`
   - `id` (UUID, PK)
   - `source_account_id` (UUID, FK -> accounts.id, Nullable for external deposit)
   - `destination_account_id` (UUID, FK -> accounts.id, Nullable for external withdrawal)
   - `amount` (Decimal)
   - `currency` (String)
   - `transaction_type` (String) e.g., 'transfer', 'deposit', 'withdrawal', 'payment'
   - `status` (String) e.g., 'completed', 'pending', 'failed'
   - `timestamp` (Timestamp)
   - `location_country` (String)

### Investigation & Alerts
6. `alerts`
   - `id` (UUID, PK)
   - `transaction_id` (UUID, FK -> transactions.id)
   - `customer_id` (UUID, FK -> customers.id)
   - `alert_type` (String) e.g., 'AML_RULE', 'ML_ANOMALY'
   - `severity` (String) e.g., 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
   - `status` (String) e.g., 'NEW', 'UNDER_REVIEW', 'ESCALATED', 'CLOSED'
   - `risk_score` (Float)
   - `created_at` (Timestamp)

7. `investigations` (Cases)
   - `id` (UUID, PK)
   - `alert_id` (UUID, FK -> alerts.id, Unique)
   - `assigned_to` (UUID, FK -> users.id, Nullable)
   - `status` (String) e.g., 'OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'
   - `summary` (Text) - AI generated summary
   - `overall_risk_score` (Float)
   - `created_at` (Timestamp)
   - `updated_at` (Timestamp)

8. `investigation_evidence`
   - `id` (UUID, PK)
   - `investigation_id` (UUID, FK -> investigations.id)
   - `evidence_type` (String) e.g., 'TRANSACTION', 'GRAPH_LINK', 'REGULATION'
   - `description` (Text)
   - `metadata` (JSONB) - Stores relevant IDs or data points

9. `aml_rules`
   - `id` (UUID, PK)
   - `name` (String)
   - `description` (Text)
   - `parameters` (JSONB) e.g., threshold values
   - `is_active` (Boolean)

10. `triggered_rules`
    - `id` (UUID, PK)
    - `alert_id` (UUID, FK -> alerts.id)
    - `rule_id` (UUID, FK -> aml_rules.id)
    - `evidence` (JSONB)

### Knowledge & AI
11. `regulatory_documents`
    - `id` (UUID, PK)
    - `title` (String)
    - `content` (Text)
    - `embedding` (Vector) - pgvector for RAG
    - `source_url` (String)
    - `created_at` (Timestamp)

12. `reports`
    - `id` (UUID, PK)
    - `investigation_id` (UUID, FK -> investigations.id)
    - `generated_by_agent` (Boolean)
    - `content` (Text) - Markdown or structured JSON
    - `status` (String) e.g., 'DRAFT', 'APPROVED'
    - `created_at` (Timestamp)

## Relationships summary
- A `Role` has many `Users`.
- A `Customer` has many `Accounts`.
- An `Account` can have many `Transactions` (as source or destination).
- A `Transaction` can generate `Alerts`.
- An `Alert` can trigger an `Investigation` (1:1 or 1:N depending on aggregation, here 1:1 for simplicity, though alerts can be grouped).
- An `Investigation` contains many `InvestigationEvidence` and `Reports`.
