# Personal, Offline, Always-On AI Companion

## 2. Problem Description

### 2.1 Description

Build a personal AI companion - in a form factor of the team's own choosing (wearable, desk companion, or otherwise) - that is continuously listening/sensing its environment and helps amplify human potential. The AI's reasoning must run entirely on-device; the only permitted online calls are for real-time factual lookups (weather, search, news), never for reasoning or decision-making. Teams choose their own focus area - memory and recall, productivity and task management, learning and skill-building, decision-support/wellbeing, or a combination - and are encouraged to work within a constrained compute budget (edge device like Raspberry Pi preferred, phone-class app next, local-network laptop least preferred).

### 2.2 Business Context

#### What is the exact need

A genuinely private, always-available personal AI that does not depend on a cloud connection or subscription to function, addressing a real, current market gap.

#### What is driving this in 2026

- The AI-wearable category has publicly struggled precisely on this point: cloud-dependent devices like the Humane AI Pin and the original Rabbit R1 either shut down entirely or underdelivered when their backend services changed or were discontinued, while pendants that "always listen" (Limitless, Bee, Omi) have raised ongoing privacy and consent debates. There is a clear, current opening for a device that keeps reasoning local by design rather than as an afterthought - immune to service shutdowns, acquisitions, or connectivity loss, and inherently more private.
- Simultaneously, small/edge-optimized language models and local inference tooling (quantized SLMs, efficient runtimes) have matured enough in 2025-2026 that meaningfully capable offline reasoning on constrained hardware is now realistic, not aspirational.

#### What is the value that the problem will bring to Infosys

Builds an internal capability in edge AI/on-device inference, small-model optimization, and privacy-first personal-AI design - a capability increasingly relevant to client conversations around data sovereignty, latency-sensitive AI, and edge deployment.

### 2.3 Key Stakeholders

The problem statement does not specify additional key stakeholders.

## 3. Solution Features

### 3.1 Deliverables

- A working physical prototype (any form factor) with continuous local sensing.
- An on-device reasoning pipeline (local LLM/SLM) capable of supporting at least one human-potential use case end-to-end.
- Demonstrated, working privacy safeguards (see Must Have).
- A clear demo showing the strict online/offline boundary in action, meaning an online lookup happening alongside fully local reasoning.

### 3.2 Must Have

- Continuous local audio/environment sensing.
- All AI reasoning and decision-making performed on-device - no cloud LLM calls; online calls limited strictly to real-time factual lookups such as weather, search, or news.
- A physical mute switch and a visible listening indicator (light).
- Raw audio never leaves the device - no cloud sync of recordings.
- A working demo in at least one chosen human-potential domain: memory/recall, productivity, learning, or decision-support/wellbeing.

### 3.3 Good to Have

- Support for multiple human-potential domains in a single device.
- Long battery life or power-efficient design appropriate to the chosen form factor.
- Thoughtful, ergonomic, or genuinely wearable/desk-friendly industrial design.
- Graceful degradation or honest fallback behavior when a query exceeds the on-device model's capability, rather than failing silently or hallucinating.

### 3.4 Existing Solutions and Products

- **Limitless Pendant:** A leading always-listening pendant for conversation capture and summarization; cloud-dependent, and the product was pulled from sale to new customers after Meta's acquisition in December 2025 - a useful cautionary example of what full cloud dependency risks.
- **OpenClaw:** An open-source, self-hosted personal AI agent framework with an extensible plugin ecosystem (ClawHub). It can be configured to run entirely on a local LLM (via Ollama or LM Studio) instead of a cloud provider, giving it "no data leaves the machine" privacy properties. It is a software analog of the local-reasoning-first architecture this problem asks for, though it is typically deployed on a home server or mini-PC rather than wearable hardware - a useful reference for the on-device agent/tool-use pattern, not the form factor.
- **Omi (formerly Friend, by Based Hardware):** An open-source AI wearable pendant that explicitly markets local processing and user data ownership as differentiators, and is the closest existing hardware comparable to what this problem asks teams to build, though it still commonly relies on cloud AI for its more advanced features.

### 3.5 Reference

- **llama.cpp / GGUF:** A widely used open-source C/C++ inference engine purpose-built for running quantized language models efficiently on CPUs and edge hardware, from Raspberry Pi to laptops. It is the practical foundation most local-LLM tooling, including Ollama, is built on.
- **Small/edge-optimized language model families:** Models such as Gemma, Phi, Llama 3.2, and similar models are compact and quantization-friendly, designed to preserve capability while fitting tight memory and power budgets. They are directly relevant to sizing the on-device reasoning component.

### 3.6 Relevance

Directly applicable to the emerging personal/wearable AI product category and to any client scenario where data sovereignty, offline reliability, or edge inference matters. The resulting capability could be reused in demos or proposals in those spaces.

## 4. Requirements

### 4.1 Software Required

Open-source technology only; no mandated framework. Teams are free to choose their own local inference runtime, such as llama.cpp-based tooling, model, and application stack, provided all reasoning stays strictly on-device.

### 4.2 Hardware Required

Teams design and bring their own device, with the following strongly encouraged compute-budget ordering from most to least preferred:

1. Raspberry Pi/microcontroller-class edge device
2. Phone-class app
3. Local-network laptop

Mandatory safeguards given continuous audio sensing:

- Physical mute switch
- Visible listening indicator (light)
- No raw audio leaving the device and no cloud sync of recordings

## 5. How to Test

The live demo must show:

1. Continuous local sensing in action.
2. The mute switch and listening indicator functioning correctly.
3. A complete interaction in the team's chosen human-potential domain handled entirely by on-device reasoning.
4. At least one moment where an online lookup, such as weather or search, is clearly distinguished from the local reasoning happening around it.

At similar capability, the differentiating factors are:

- How constrained the compute footprint is, according to the encouraged hardware ordering.
- How honestly and gracefully the device handles queries beyond the on-device model's ability.

## 6. Input Datasets

No external dataset is required. Any personal/context data used in the demo, such as calendar entries, notes, or sample conversations, should be team-provided or synthetic and kept and processed entirely on-device.

## 7. Evaluation Criteria

| Criterion | Evaluation Question | Weight |
|---|---|---:|
| Creativity | How creative or innovative is the idea within the given challenge? Has this been done before, or is this something completely new and original in architecture, design, or implementation? | 10% |
| Innovative Technology and Quality | How has the team utilized existing technologies in the solution, and what is the quality of the code? | 20% |
| User Experience and Functionality | Is the overall user experience intuitive? Does the flow make sense? | 10% |
| Simplicity | How elegantly does it solve the problem? Is the approach smart rather than unnecessarily difficult? | 10% |
| Feasibility, Impact, Reuse, Extensibility, and Modularity | Does the solution work? Can it be implemented at scale? Can it be extended to other similar problem statements? | 30% |
| Progress and Execution | How much is accomplished in a day? | 10% |
| Demo and Presentation | How well did the team present? | 10% |

## 8. Proposed Solution

### 8.1 Concept: The Compliance-Safe AI Colleague

A desk companion that gives regulated professionals (lawyers, doctors, bankers, defense/gov staff) the same "always-listening meeting memory + task assistant" experience as tools like Otter.ai or Fireflies - except compliance can actually approve it, because zero audio or reasoning ever leaves the device. It combines the memory/recall and productivity domains: it continuously captures conversations, extracts action items and notes entirely on-device, and answers recall queries against its own local memory store.

### 8.2 Why This Wins

- Directly maps to the stated Infosys value driver: data sovereignty, latency-sensitive AI, and edge deployment relevant to client conversations.
- Cloud meeting-bots being blocked by compliance/legal teams is a real, current, widely recognized pain point in regulated industries - the problem is instantly credible, not invented.
- Same core stack extends cleanly to multiple verticals (healthcare bedside notes under HIPAA, banking client-meeting notes under data-residency rules, legal privileged-conversation capture, defense/field ops with no connectivity) - one prototype, several pitchable business cases.
- Gives a sharp narrative arc for the demo instead of a feature tour, and makes the mandatory offline/online boundary demo (see Section 5) the emotional centerpiece rather than an afterthought.

### 8.3 Architecture / Stack

- **STT (local):** whisper.cpp, tiny/base.en quantized model.
- **Reasoning (local):** llama.cpp running a quantized SLM - Llama 3.2 3B-Instruct (Q4_K_M) or Phi-3-mini (Q4) - for extracting action items/notes and answering recall queries.
- **Memory store (local):** SQLite plus a lightweight local embedding search (llama.cpp embeddings or a small ONNX sentence-transformer) for RAG-style recall over past conversations.
- **TTS (local):** Piper for fast, lightweight offline voice replies.
- **Online lookup (isolated):** a single, clearly separated code path for non-sensitive factual queries only (e.g., weather, public dates) - never touches reasoning or stored memory.
- **Hardware I/O:** GPIO push-button that physically cuts mic input in software (mute switch); GPIO LED that is solid while listening and visibly changes state (color/blink) during an online lookup, making the offline/online boundary visually unmistakable.

### 8.4 Demo Narrative Arc (~90 seconds)

1. State the pain: a hospital/bank/law firm wants meeting AI, but compliance blocks any cloud AI from touching the audio.
2. Show the physical mute switch and LED as a hardware guarantee, not a policy promise.
3. Have a "confidential" conversation, mute mid-sentence (LED goes off) - proving raw audio isn't being captured.
4. Unmute, continue talking about a case/deal/patient - device extracts action items/notes on-device.
5. Ask it to recall something from earlier (e.g., "what did we decide about the Henderson account?") - fully local RAG answer.
6. Ask one clearly non-sensitive factual question (e.g., "what's the weather for tomorrow's client visit?") - LED/screen visibly flips to an "online lookup" state, then flips back, satisfying the Section 5 requirement to distinguish online lookups from local reasoning.
7. Close on extensibility: same device, swap the vertical - legal, healthcare, banking, field ops - because the constraint isn't the model, it's trust, and trust is what edge inference buys you.

### 8.5 Alternate Framing (fallback)

**The Off-Grid Field Companion:** same underlying tech, reframed as a memory/task assistant for workers with no reliable connectivity (disaster response, mining, remote infrastructure, maritime), where cloud AI is unavailable for physical rather than compliance reasons. Slightly less aligned with Infosys's stated enterprise-client value, but an equally clean offline/online demo (e.g., a weather forecast ahead of a storm at a remote site).