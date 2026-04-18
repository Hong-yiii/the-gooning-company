# Objective
 I'm aiming to build a agent harness for specific company functions specifically 
 1. Product / UX 
 2. Marketing 
 3. Finance

 The main goal is to provide the foudneders with decision making leverage, to reduce friction between sprase but annoying company functions

 Each of these agents exist as long running agents in a company, each with their own scopes concerns, system prompts etc. they are agents from OpenHarness
    you may read https://github.com/HKUDS/OpenHarness/blob/main/docs/SHOWCASE.md to understand what agents from openharness are capable of and how they are spawned and eg. exposing tools 
    you are free to crawl the docs and should always refer to them when you are unsure 

In /Product-requirement-doc we indicate the roles and responsibilities of each agent, we should work towards 
- what tools to expose 
- communication contracts 
- tieing down interconnects between these agents for tieing down the workflow

The user should communicate with a "the-gooning-copmany" agent which acts as a simple router and basic context enricher.

key concepts: 
1. **"god md"** each agent owns a this markdown file. it is the active living doc of the company related to each agent's concerns 
2. interagent communication — it should be automatic, if the company updates the product roadmap(owned by product / UX), it should update marketing and finance: this will allow abstractions such as new financial projections and implications, additionally, additionall if actions like new marketing campaign is started, finance agent should be informed 
3. tool use: this is a project done for a hackathon, so the tool calls etc can be fake and can contain fake data, but we should host a "tool server" / MCP to simulate real tool calls even with mocked replies 

# Additional requirements on top of what is already enabled within openharness 

## Product roadmap 
This is geared towards teams which work by a product roadmap, so this should be a foundational tool we implement
- it should basically show the diff functions across the diff domains, the status, high level, almost like a kanban board.
- in theory, this drives the company and anything changed to the product roadmap cascasdes into actions across the other agents. Similarly, if marketing agent sees a problem, it should be raised into the roadmap, so its a living doc; a decision making panel for founders of sorts

### Dashboard 
- We keep the dynamic product roadmap
- here we implement observability to the **"god md"** 



### Extras:
- keep important concepts for devs to note in /dev-concepts
    - this may be like how context is handled, key implementation invariatnts etc