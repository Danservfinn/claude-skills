# Claude Code Skills

65 skills for Claude Code, including the Horde multi-agent orchestration ecosystem.

## For Machines

Copy and paste this into Claude Code to install all skills:

```
Clone https://github.com/Danservfinn/claude-skills and copy every subdirectory (excluding .git, __pycache__, *.zip, *.zip.bak) into ~/.claude/skills/. Each subdirectory is a skill. Do not overwrite any existing skills that are already installed. After copying, list the skills that were installed.
```

Or run this in your terminal:

```bash
git clone https://github.com/Danservfinn/claude-skills.git /tmp/claude-skills-install && \
rsync -av --ignore-existing --exclude='.git' --exclude='__pycache__' --exclude='*.zip' --exclude='*.zip.bak' --exclude='README.md' /tmp/claude-skills-install/ ~/.claude/skills/ && \
rm -rf /tmp/claude-skills-install && \
echo "Installed $(ls ~/.claude/skills/ | wc -l) skills"
```

## Skill Categories

### Horde Ecosystem (Multi-Agent Orchestration)

The horde skills form a layered orchestration system for dispatching and coordinating multiple AI agents.

| Skill | Description |
|---|---|
| **golden-horde** | Master orchestrator. 9 collaboration patterns, 60+ agent types across 3 tiers, embedded methodologies from all horde skills. Use for tasks requiring inter-agent communication: review loops, debates, pipelines, consensus. |
| **horde-swarm** | Fire-and-forget parallel dispatch. 35+ agent types. Use for embarrassingly parallel tasks where agents work independently. |
| **horde-plan** | Structured planning with EnterPlanMode/ExitPlanMode. Produces phased implementation plans with dependency graphs. |
| **horde-implement** | Full implementation pipeline: prompt engineering, task decomposition, subagent execution, status audit, review. |
| **horde-test** | Comprehensive test suite execution via parallel agent dispatch. Unit, integration, e2e, edge case coverage. |
| **horde-review** | Multi-disciplinary critical review across backend, security, performance, architecture, DevOps, accessibility. |
| **horde-brainstorming** | Structured ideation with diverge-evaluate-converge phases. Multiple perspectives via parallel agents. |
| **horde-learn** | Extract actionable insights from sources. Categorizes findings as techniques, principles, warnings, opportunities. |
| **horde-gate-testing** | Integration tests between implementation phases. Contract testing, schema validation, regression checks. |
| **horde-skill-creator** | 7-phase workflow for creating new skills with validation and review. |

### Senior Specialists

Domain expert agents with deep knowledge in specific technical areas.

| Skill | Domain |
|---|---|
| senior-architect | System design, architecture patterns, tech decisions |
| senior-backend | API design, database optimization, backend security |
| senior-frontend | React, Next.js, component architecture, performance |
| senior-fullstack | End-to-end web application development |
| senior-devops | CI/CD, infrastructure as code, deployment strategies |
| senior-data-engineer | Data pipelines, ETL, data architecture |
| senior-data-scientist | Statistical modeling, experimentation, ML |
| senior-ml-engineer | MLOps, model deployment, RAG systems |
| senior-computer-vision | Image/video processing, object detection |
| senior-prompt-engineer | LLM optimization, prompt patterns, agent design |

### Development Workflow

| Skill | Purpose |
|---|---|
| brainstorming | Creative exploration before building |
| writing-plans | Structured implementation planning |
| executing-plans | Plan execution in separate sessions |
| subagent-driven-development | Execute plans with independent task agents |
| dispatching-parallel-agents | Parallel task execution |
| code-reviewer | Comprehensive code review |
| requesting-code-review | Pre-merge review workflow |
| receiving-code-review | Implementing review feedback |
| verification-before-completion | Final checks before declaring done |
| systematic-debugging | Root cause analysis for bugs |
| implementation-status | Audit completion of implementation plans |
| ship-it | Test, document, commit, deploy pipeline |
| generate-tests | Test suite generation |

### Specialized Tools

| Skill | Purpose |
|---|---|
| agent-collaboration | Cross-agent communication via Signal protocol |
| agent-development | Creating new Claude Code agents |
| command-development | Building slash commands |
| skill-creator | Creating new skills |
| skill-development | Skill development workflow |
| changelog-generator | Git-based changelog creation |
| claude-cleanup | Clean orphaned subagent processes |
| file-organizer | Intelligent file/folder organization |
| video-downloader | Download videos for offline use |
| webapp-testing | Test local web apps with Playwright |
| oauth-setup | Google/Facebook OAuth setup |
| theme-factory | Style artifacts with themes |
| web-artifacts-builder | Multi-component HTML artifacts |
| frontend-design | Production-grade UI interfaces |

### Analysis & Content

| Skill | Purpose |
|---|---|
| accessibility-auditor | WCAG compliance auditing |
| critical-reviewer | Adversarial analysis of web pages |
| content-research-writer | Research-backed content creation |
| seo-optimizer | Search engine optimization |
| lead-research-assistant | Lead identification and research |
| ui-design-system | Design tokens and component systems |
| ux-researcher-designer | UX research and design |
| product-strategist | OKR cascades, product strategy |

### Leadership & Advisory

| Skill | Purpose |
|---|---|
| cto-advisor | Engineering leadership, tech decisions |
| ceo-advisor | Board strategy, M&A, compensation |
| parse-cfo | Financial monitoring for Parse SaaS |

### Project-Specific

| Skill | Purpose |
|---|---|
| molt | Molt bot configuration and deployment |
| kurultai-model-switcher | LLM model switching for Kurultai agents |
| data-ingestion | Data scraping and ingestion pipelines |
| last30days | Recent activity tracking |

## Architecture

```
golden-horde (master orchestrator)
  ├── Embeds all horde skill methodologies as prompt templates
  ├── 9 collaboration patterns (review loop, debate, pipeline, etc.)
  ├── 60+ agent types in 3 tiers:
  │     ├── Tier 1: Implementation (35+ from horde-swarm)
  │     ├── Tier 2: System (Plan, Explore, Bash, docs, payment, etc.)
  │     └── Tier 3: Judgment (cost analyst, chaos engineer, etc.)
  └── Nested horde-swarm for parallel sub-tasks (max depth: 2)

horde-swarm (parallel dispatch)
  └── Fire-and-forget agents, no inter-agent communication

horde-plan → horde-implement → horde-test → horde-review
  └── Full lifecycle pipeline (each can be used standalone or embedded in golden-horde)
```

## License

These skills are provided as-is for use with Claude Code.
