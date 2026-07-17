# Architecture Documentation

## System Architecture
The AI Financial Crime Investigation Platform follows a microservices-inspired monolithic architecture initially for ease of deployment, separated into clear domains.

- **Frontend:** React Dashboard (to be developed in Phase 8).
- **Backend Core:** FastAPI providing RESTful APIs.
- **Database:** PostgreSQL (with `pgvector`) for relational data and document embeddings.
- **Graph Database:** Neo4j for relationship mapping.
- **Caching/State:** Redis.
- **AI Agents:** LangGraph orchestrated agents for intelligence and reasoning.

## Authentication and RBAC Architecture

### Authentication
- Uses **JWT (JSON Web Tokens)** for stateless API authentication.
- Users authenticate via `/api/v1/auth/login` to receive an `access_token`.
- The token must be passed in the `Authorization: Bearer <token>` header for protected routes.
- Passwords are securely hashed using `bcrypt` (via `passlib`).

### Role-Based Access Control (RBAC)
- Roles are stored in the `roles` table. Each user belongs to a role.
- Standard roles:
  1. **Admin:** Full access to system configuration and user management.
  2. **Analyst:** Can view alerts, run investigations, and manage cases.
  3. **Investigator:** Specialized analyst with deep-dive capabilities.
  4. **Compliance Officer:** Read-only access to reports and investigations for regulatory review.
- RBAC is enforced at the API route level using FastAPI dependencies (e.g., `Depends(get_current_user_with_roles(['Admin', 'Analyst']))`).

## Docker Compose Services (Phase 1)
For the development environment, Docker Compose orchestrates the core infrastructure components:

1. **db (PostgreSQL + pgvector):**
   - Image: `pgvector/pgvector:pg16`
   - Ports: `5432:5432`
   - Volumes: `postgres_data`
   - Purpose: Core relational storage and vector embeddings.

2. **neo4j:**
   - Image: `neo4j:5`
   - Ports: `7474:7474` (HTTP), `7687:7687` (Bolt)
   - Volumes: `neo4j_data`
   - Purpose: Knowledge graph.

3. **redis:**
   - Image: `redis:7-alpine`
   - Ports: `6379:6379`
   - Purpose: Caching and session/agent state.

*(The backend API itself will run locally for development initially, and will be containerized in later phases for complete deployment).*
