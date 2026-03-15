# Research Report Template

<!-- This template is used by the synthesizer to structure final research output. -->
<!-- Fields in {{}} are filled by the pipeline. Remove comments before use. -->

---

topic: "{{topic}}"
wave: {{wave_number}}
generated_at: "{{timestamp}}"
agents: {{agent_count}}
gate_score: {{gate_score}}
delta_score: {{delta_score}}
token_cost: {{token_cost}}

---

# {{title}}

## Executive Summary

<!-- 2-3 sentences: what was researched, what was found, what's the key takeaway. -->

{{executive_summary}}

## Key Findings

<!-- Numbered list of the most important findings. Each should be a specific, verifiable claim. -->

{{#each key_findings}}
{{@index}}. {{this}}
{{/each}}

## Detailed Analysis

### {{section_1_title}}

{{section_1_content}}

### {{section_2_title}}

{{section_2_content}}

### {{section_3_title}}

{{section_3_content}}

## Skeptic Challenges Addressed

<!-- This section is populated by the synthesizer when with_skeptic=True. -->
<!-- Each challenge from the skeptic should be addressed or acknowledged here. -->

{{#if skeptic_challenges}}
The following challenges were raised and addressed:

{{#each skeptic_challenges_addressed}}

- **{{claim}}**: {{resolution}}
  {{/each}}
  {{/if}}

## Gaps and Open Questions

<!-- What this research did NOT cover, and what remains uncertain. -->

{{gaps_and_questions}}

## Methodology

- **Research waves**: {{wave_count}}
- **Parallel agents**: {{agent_count}}
- **Skeptic pass**: {{skeptic_used}}
- **Pre-flight overlap**: {{preflight_similarity}}
- **Gate bounces**: {{bounce_count}}

## Citations and Sources

<!-- All sources cited in the report. Include year where known. -->

{{#each citations}}

- {{this}}
  {{/each}}
