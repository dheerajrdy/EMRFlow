AI Voice Assistant for Patient Support (Multi-Agent System)

Overview

Heidi Health’s hackathon challenge seeks novel applications of voice agents in healthcare to improve patient care and service efficiency . In response, this Product Requirements Document (PRD) outlines a smart voice-based AI assistant that handles patient phone calls for a clinic. The system addresses a critical need by automating routine patient inquiries – such as scheduling appointments and answering medical-related questions – through natural voice interactions. Both input and output are voice-based to provide a hands-free, accessible experience . This solution integrates into existing healthcare workflows, aiming to free up staff time and allow providers to focus more on direct patient care  . A key aspect of our design is the use of a multi-agent architecture behind the scenes: specialized AI modules will collaborate (for speech recognition, language understanding, data lookup, etc.) to fulfill user requests. The result is an ambient, human-like voice assistant that can meaningfully impact patient services in at least one high-need area (appointment management and information access) .

Objectives and Goals
	•	Enhance Patient Experience: Provide patients with immediate, 24/7 assistance via natural voice conversation. Patients can manage appointments, request medical information, receive reminders and follow-ups without waiting on hold for a human receptionist .
	•	Reduce Administrative Burden: Automate routine call handling (scheduling, FAQs, information lookup) to lighten the load on administrative staff. This directly supports Heidi Health's mission to reduce clerical tasks for healthcare providers  and cuts down call handling time for staff .
	•	Showcase Multi-Agent AI Proficiency: Demonstrate a multi-agent system where different AI components (speech-to-text, NLU, scheduling agent, records agent, etc.) work in concert. The hackathon prototype will highlight how modular AI agents can be orchestrated to handle complex, multi-step workflows in a seamless voice interaction .
	•	Seamless Healthcare Integration: Design the solution to fit into existing healthcare workflows. For example, it should integrate with (or simulate) a clinic's scheduling system and patient records. This ensures the voice assistant provides meaningful, context-aware responses and actions (e.g. booking an appointment in the clinic's calendar) .
	•	Deliver a Functional Prototype: Build a working demo that meets hackathon requirements – a live voice agent interface showing end-to-end functionality (from voice input to voice output). The prototype will illustrate the key use cases and prove the concept in action, ready for handoff to development (e.g. using Claude to generate code) for implementation.

Hackathon Scope

To ensure focused execution and avoid overbuilding, we explicitly define scope boundaries:

**In Scope (Must Have):**
	•	Voice → Text → Intent → Response pipeline (end-to-end)
	•	2-3 core use cases fully working: appointment scheduling, appointment management, medical info queries
	•	Mock data (patients, schedules, FAQs) - no real EHR integration
	•	Text-based testing first (voice as stretch goal)
	•	Sequential + Conditional workflow orchestration
	•	Conversation logging for debugging/demo
	•	Basic evaluation with 5-10 test scenarios
	•	Web-based voice UI OR Twilio (pick one based on time)
	•	PHI sanitization in logs

**Out of Scope (Future Work):**
	•	Complex medical triage logic
	•	Real EHR/FHIR integration
	•	Multi-language support
	•	Production security (OAuth, encryption)
	•	Billing/insurance integration
	•	Staff dashboards
	•	Advanced analytics beyond basic metrics
	•	Load testing / scalability optimization

**Success Criteria:**
	1.	Functional demo completing 3 end-to-end scenarios
	2.	Clear multi-agent architecture visible in presentation
	3.	Demonstrated healthcare value (patient experience improvement)
	4.	Clean code, passing tests, stable performance
	5.	Bonus: Voice UI working, evaluation metrics shown

Target Users and Personas
	•	Patients (Primary Users): The main users are patients who call the clinic. They may be individuals managing their own healthcare or calling on behalf of a family member. Their needs include scheduling appointments, asking about test results or prescriptions, receiving follow-up instructions, and general inquiries . These users might not be tech-savvy, so the voice agent must be intuitive, patient, and helpful, using simple language to communicate medical information. Ensuring a friendly and empathetic tone will make patients feel comfortable interacting with an AI over the phone.
	•	Clinic Administrative Staff (Secondary/Indirect): Receptionists and scheduling staff benefit indirectly. Currently, they handle numerous calls for appointments and routine questions, contributing to high workload and wait times . By offloading calls to the voice assistant, staff can focus on in-person patients and complex tasks. The staff’s role may shift to overseeing the system (receiving escalations for requests the AI can’t handle, or reviewing logs for quality). The solution should be designed such that staff can trust it to handle routine cases reliably, and intervene only when necessary.
	•	Healthcare Providers (Future Persona): While not the immediate focus of this prototype, doctors and nurses could eventually use voice agents to quickly retrieve patient data during clinical work (for example, verbally asking for a patient’s latest lab results during a consultation) . Our system’s architecture will be flexible enough to add such capabilities later. This demonstrates potential for multi-user-group support, though the hackathon implementation will concentrate on the patient use-case first .

User Journeys & Use Cases

To illustrate the system’s value, below are key user journeys that the voice assistant will support. Each journey describes how a patient interacts with the voice agent and how the multi-agent system fulfills the request behind the scenes:

Use Case 1: Appointment Scheduling (New Appointment)

Goal: A patient wants to book a new appointment over the phone.
	1.	Call and Greet: The patient calls the clinic’s number. The voice agent answers with a friendly greeting (e.g., “Hello, thank you for calling [Clinic Name]. I’m Heidi, the virtual assistant. How can I help you today?”). The agent’s greeting sets a helpful tone and invites the user’s request.
	2.	Patient Request: The patient says, for example, “I’d like to schedule an appointment for a check-up next week.” The speech recognition module transcribes this, and the NLU agent interprets the intent as a Scheduling request, extracting details like appointment type (check-up) and time frame (next week).
	3.	Authentication (if needed): If the system doesn’t recognize the caller ID or needs confirmation, the agent will politely ask for a verification (e.g., “Sure. May I have your name and date of birth to find your records?”). The patient provides their name/DOB, which the system checks against the mock patient database. This step ensures the agent is accessing the correct patient profile before scheduling.
	4.	Check Availability: The Dialogue Manager delegates to the Appointment Scheduling Agent. This agent queries the clinic’s mock scheduling system for available slots (for a check-up, presumably with the patient’s primary doctor or a relevant provider). For example, it finds that Dr. Smith has openings next week on Tuesday at 10 AM and Wednesday at 2 PM.
	5.	Offer Time Slots: The voice assistant responds with options: “I see Dr. Smith has an opening on Tuesday at 10:00 AM and another on Wednesday at 2:00 PM. Which would you prefer?” The patient selects a slot (e.g., Tuesday 10 AM).
	6.	Book Appointment: The Appointment Agent confirms the slot is still free, then creates a new appointment entry in the mock schedule for that patient.
	7.	Confirmation: The agent confirms to the patient: “Great, I’ve booked you for a check-up with Dr. Smith on Tuesday, November 7th at 10:00 AM. You’ll receive a reminder the day before. Is there anything else I can help you with?” This confirmation includes date/time and provider name for clarity.
	8.	Completion: If the patient has no further requests, the agent ends the call politely: “Thank you for calling, have a nice day!”. If the patient has another question, the agent seamlessly transitions to handle that (e.g., the patient might next ask about a prescription—demonstrating multiple tasks in one call, which our system can handle in one workflow ).

Alternate flows:
	•	If the patient requested a specific doctor or a specific date/time, the agent will attempt to accommodate that and either confirm or offer the nearest alternatives if the requested slot is unavailable.
	•	If no suitable slots are found (e.g., next week is fully booked), the agent can apologize and offer to check the following week or put the patient on a waitlist.
	•	If the patient is new (not in database), the agent can collect basic information and either create a new profile (in the demo, simply note it) or transfer to a human staff for onboarding.

Use Case 2: Appointment Management (Reschedule/Cancel)

Goal: A patient wants to change an existing appointment.
	1.	Call and Verify: The patient calls and says, “I need to reschedule my appointment.” The agent asks for identification (if not already known) to pull up the patient’s record and upcoming appointments.
	2.	Find Existing Appointment: Using the Patient Records Agent and scheduling data, the system finds the patient’s upcoming appointment (e.g., a check-up on Nov 7 at 10 AM with Dr. Smith). The agent confirms: “I see you have an appointment on Nov 7 at 10:00 AM with Dr. Smith. Would you like to reschedule or cancel it?”
	3.	Patient Request: The patient says they want to reschedule to a different day. The agent invokes the Scheduling Agent to find new available slots, just like in Use Case 1. It then offers: “Dr. Smith is available the following week on Tuesday at 9 AM. Does that work for you?” (If patient had a preference, the agent would try to match it.)
	4.	Update Appointment: Once the patient agrees, the agent updates the appointment in the system (old slot freed, new slot booked) and confirms: “Your appointment has been rescheduled to Tuesday, November 14th at 9:00 AM with Dr. Smith. I’ve canceled your previous appointment.”
	5.	Cancellation (alternative): If the patient wanted to cancel outright, the agent would mark the appointment as canceled and perhaps offer to help rebook later. It would confirm cancellation: “Your appointment on Nov 7th has been canceled. If you need to rebook at any time, just let us know. Is there anything else I can do for you today?”

This flow reduces no-show rates by making it easy for patients to reschedule rather than just not showing up. It also frees staff from handling these routine changes.

Use Case 3: Medical Information Query

Goal: A patient inquires about their personal medical information or a follow-up question after a visit.
	1.	Patient Request: After greeting, the patient asks a question such as “Can you tell me if my blood test results are in?” or “What did the doctor say about my medication?”. Natural language understanding identifies this as an Information Query intent, concerning test results or doctor’s notes.
	2.	Identity Verification: Since this involves sensitive personal data, the agent must verify the caller. If not already done, it asks a security question (e.g., date of birth or an account PIN) to confirm identity.
	3.	Data Retrieval: The Patient Records Agent accesses the mock electronic health record (EHR) for that patient. For the blood test example, it finds the lab results in the patient’s record (e.g., “Blood test from Oct 20: cholesterol 210 mg/dL, slightly above normal; doctor’s note: advise dietary changes and retest in 3 months”). The agent also checks if the doctor has reviewed the results and left any interpretation or message for the patient.
	4.	Compose Answer: The assistant formulates a concise, patient-friendly explanation. For instance: “Your recent blood test results came in. Your cholesterol level was a bit high at 210, which is slightly above the normal range. Dr. Smith noted that you should consider some dietary changes and come back for a re-test in about 3 months. Would you like to schedule that follow-up appointment now?”. The inclusion of an offer to schedule follow-up demonstrates proactive assistance and connects two tasks (info + scheduling) in one conversation flow .
	5.	Patient Follow-up: The patient might ask an additional question (“What diet changes should I make?”). If the information is in the doctor’s notes or a general knowledge base, the agent can provide it (e.g., “The doctor recommends reducing saturated fats and increasing fiber. We can also email you some dietary guidelines.”). If the question goes beyond available data or into medical advice, the agent will respond cautiously: “I’m sorry, I can’t provide specific medical advice on that. It’s best to consult your doctor for detailed guidance.”. Ensuring the agent stays within its knowledge limits maintains safety.
	6.	Closure: The agent asks if anything else is needed. If not, it thanks the patient and ends the call.

Other examples of queries:
	•	“When is my next appointment?” – The agent retrieves upcoming appointments from the schedule and answers with date/time, e.g., “You have a follow-up with Dr. Lee on March 3rd at 2 PM.”
	•	“What medications am I supposed to take right now?” – The agent pulls the medication list from the record (e.g., “Metformin 500 mg once daily”) and any instructions, and reads them to the patient. It might add, “Please follow the dosage as prescribed. If you have any concerns, contact your pharmacist or doctor.”
	•	General FAQ: If a patient asks a general question like “What are your clinic hours?” or “Do I need a referral to see a specialist?”, the agent can answer from a pre-loaded FAQ knowledge base. For example: “Our clinic is open Monday through Friday, 8 AM to 6 PM.” or “No referral is needed for most specialists, but it depends on your insurance.”. These don’t require personal data, so the agent can answer directly or, if unsure, advise to call during business hours for detailed info.

Each of these use cases demonstrates a critical need that a voice agent addresses – quick scheduling, accessible health information, and instant answers . By handling these scenarios, the voice assistant improves service for patients and efficiency for the clinic.

Key Features and Requirements

Below is a summary of the core features and system requirements for the voice assistant, derived from the user needs and use cases:
	•	Natural Voice Interaction: The system supports bi-directional voice communication, accepting spoken input and providing spoken responses . The voice assistant should respond in a clear, polite, and empathetic manner, with a tone appropriate for a healthcare setting.
	•	Speech Recognition (ASR): Use automatic speech recognition to transcribe patient utterances in real-time. The ASR component must handle medical terminology (e.g., medication names, common symptoms) and varying accents as much as possible. In the prototype, a cloud API (like Google Speech-to-Text or Whisper) or an open-source model can be used to ensure accuracy.
	•	Natural Language Understanding: Implement NLU to interpret the caller’s intent and extract details from the transcribed text. This could be achieved via a fine-tuned language model or prompt-based parsing using a large language model (LLM). The NLU should categorize requests (e.g., AppointmentBooking, AppointmentChange, InfoQuery, GeneralQuery) and capture key entities like dates, symptoms, patient identifiers, etc.
	•	Dialogue Management (Orchestration): A central dialogue manager will control the flow of conversation. It should handle turn-taking, context, and multi-turn interactions. This includes the ability to ask follow-up questions for clarification and manage context if the user switches topics or has multiple requests in one call. The dialogue manager also orchestrates multiple sub-agents (modules), effectively functioning as the “brains” that decide which agent to invoke for a given intent – exemplifying the multi-agent system approach.
	•	Appointment Scheduling Module: Provide functionality to book, reschedule, and cancel appointments. This module will interface with a mock scheduling database containing provider availabilities and existing appointments. It must ensure no double-booking (e.g., check slot availability before confirming) and update the schedule accordingly. When offering times to patients, it should consider constraints like clinic hours or doctor’s working times.
	•	Patient Records Access: Securely access mock medical data for patients. This includes retrieving upcoming appointments, basic medical history, recent lab results, medication lists, or post-visit summaries from a simulated EHR or database. The system should use this data to answer patient-specific queries (as in Use Case 3). For the prototype, a small dummy patient database (e.g., a JSON file or in-memory data structure) will be used. This database will contain fictional patient profiles with fields such as name, DOB, contact info, appointments, and health data (test results, medications, doctor notes, etc.).
	•	FAQ Knowledge Base: For general questions not tied to a specific patient, the assistant will refer to a simple knowledge base. This could be a set of hard-coded Q&A pairs or a small document covering frequent inquiries (clinic hours, location, basic medical advice for common symptoms, etc.). The system should be able to search or match the question to this FAQ and respond appropriately. (For the hackathon, this can be a straightforward dictionary lookup or a semantic search on a text file.)
	•	Multi-Agent Collaboration: Under the hood, the solution is composed of multiple specialized agents or components working together. Each agent (ASR, NLU, Scheduling, Records, Knowledge, TTS) handles its specialty. The requirement is that these components communicate through well-defined interfaces so that the overall system behaves as one coherent assistant. This modular design is critical for showcasing our proficiency in multi-agent systems and for future scalability – new agents (e.g., a billing agent or a symptom triage agent) can be added without rewriting the whole system.
	•	Conversational Flexibility: The assistant should handle multi-step dialogues. For example, if a patient first asks about a lab result and then says “Actually, can I schedule that follow-up?”, the agent should carry context from the previous discussion (knowing which lab result and which follow-up was suggested) and seamlessly transition to scheduling. This requires the system to maintain state (contextual memory) during the call.
	•	Error Handling and Fallback: The system must be robust to misunderstandings or unsupported queries. If the ASR produces garbled text or the intent is unclear, the agent should politely ask for repetition or clarification (“I’m sorry, I didn’t catch that. Could you please repeat?”). If the user asks something beyond the system’s capability (e.g., a complex medical diagnosis question), the assistant should gracefully decline and offer an alternative (“I’m not able to help with that. Let me connect you to a staff member.” or suggest a doctor consultation). Ensuring a graceful fallback protects the user experience and patient safety.
	•	Security and Privacy: Even though we use mock data in this hackathon project, the design considers patient privacy. Any personal health information retrieved is only used to serve the authenticated caller. In a real deployment, all data transactions would be encrypted and the system would comply with healthcare privacy regulations (HIPAA, etc.). The assistant should also avoid speaking sensitive information unless the patient’s identity is confirmed. For demo purposes, simple verification will be implemented, but the design notes where stricter security would be needed in production.
	•	Logging and Analytics (REQUIRED): **Every conversation MUST be logged as a structured execution trace.** This is a first-class requirement, not optional. Logging serves multiple critical functions:
		○	Debugging during development (trace conversation flow, identify failures)
		○	Demo at hackathon (show judges a sample conversation trace to prove system works)
		○	Evaluation framework (compute success rate, latency metrics)
		○	Compliance audit trail (verify PHI protection, authentication)

		**Required log data per conversation:**
		1. Session/Call ID (unique identifier)
		2. Per-turn data:
			• Timestamp
			• User utterance (ASR output, PHI-sanitized)
			• NLU intent + extracted entities
			• Chosen backend agent (Scheduling, Records, FAQ)
			• Agent action/result (e.g., "booked appointment A-123")
			• Final response text (PHI-sanitized)
			• Latency in milliseconds
		3. Errors/warnings triggered
		4. Call metadata: patient ID (if authenticated), total duration, outcome (success/failure)

		**Storage format:** JSONL (JSON Lines) - one file per conversation in `runs/<session_id>.jsonl`. Each line represents one turn or event. This format is simple to write, easy to parse for analysis, and human-readable for debugging.

		**PHI Protection in logs:** Before logging, apply sanitization:
		• Patient names → "[NAME]"
		• Dates of birth → "[DOB]"
		• Specific lab values → "[LAB_VALUE]"
		• Contact info → "[CONTACT]"

		The `run_storage.py` module will implement this. All agents will call `run_storage.log_turn()` to ensure comprehensive logging.
	•	Performance: The voice assistant should operate in real-time or near real-time. Users expect prompt responses on a phone call. The system should aim to respond within a couple of seconds after the user finishes speaking. This may influence the choice of models (e.g., using faster neural models or offloading heavy processing to a server with adequate resources). Since this is a prototype, we will balance complexity with speed to ensure a smooth live demo.

By fulfilling these requirements, the prototype will demonstrate a comprehensive voice agent solution that aligns with the Heidi Health challenge goals – focusing on a vital use-case (patient calls) and implementing it in a working system .

Technical Architecture

The architecture of the AI voice assistant is designed as a collection of collaborating modules (multi-agent components), each responsible for a part of the workflow. Below is an overview of the system's architecture and data flow:

Orchestration Pattern

For the hackathon prototype, we employ a **Workflow-based Orchestration Pattern** that combines sequential and conditional logic:

**Sequential Pipeline per Turn:**
Each conversation turn follows a deterministic sequence:
1. ASR (Speech-to-Text) → Transcribe user speech
2. NLU (Intent Classification) → Extract intent and entities
3. Routing (Dialogue Manager) → Dispatch to appropriate backend agent
4. Backend Agent Execution → Scheduling/Records/FAQ agent processes request
5. Response Generation → Format natural language response
6. TTS (Text-to-Speech) → Synthesize and deliver voice response
7. Loop → Return to step 1 for next turn

**Conditional Routing Logic:**
Within the Dialogue Manager, conditional branching routes requests to specialized agents:
- `ScheduleAppointment`, `RescheduleAppointment`, `CancelAppointment` → Scheduling Agent
- `InfoQuery` (lab results, medications, appointments) → Records Agent
- `FAQ` (clinic hours, general questions) → Knowledge Agent
- Unclear/unsupported → Fallback (clarification or human handoff)

**Why This Pattern:**
We chose explicit workflow orchestration (rather than fully autonomous multi-agent communication) for several key reasons:
- **Deterministic behavior**: Critical for healthcare safety and compliance
- **Clear audit trail**: Each step is traceable for debugging and regulatory review
- **Low latency**: No multi-agent negotiation overhead
- **Predictable UX**: Patients get consistent, reliable responses
- **Easy to extend**: New intents and agents can be added by extending the routing logic

This approach aligns with best practices for production multi-agent systems in regulated domains: start with explicit workflows, add autonomy only where it provides clear value. For our hackathon scope, this pattern delivers the right balance of modularity (multi-agent benefits) and control (production-ready reliability).

**System Components:**
	•	Telephony/Voice Interface: The entry point is a phone call or microphone input. We will integrate with a voice platform (e.g., Twilio for phone calls or a web-based microphone for the demo) that captures the caller’s audio and streams it to our system in real time. Similarly, it will play the synthesized voice responses back to the caller. This layer handles the telephony details (call connection, DTMF if needed, etc.), so our focus can remain on the AI logic.
	•	1. Speech-to-Text (ASR) Agent: This module converts incoming speech to text. For the prototype, we might use an API like Google Cloud Speech or an open-source model like OpenAI Whisper to ensure high accuracy, especially for medical terms. The ASR agent streams partial transcriptions if possible for faster turn-around. Once the user finishes speaking, it provides the final text to the Dialogue Manager. (Example: User says “I want to book an appointment”; ASR outputs the text “i want to book an appointment”.)
	•	2. Natural Language Understanding (NLU) Agent: Upon receiving the text, the NLU agent interprets it. This could be implemented via a rule-based intent classifier (for known phrases) plus an LLM for flexible understanding. We will likely utilize a large language model (such as Anthropic Claude or GPT-4 via API) in a controlled manner: for instance, sending the transcribed text to a prompt that asks the model to identify the intent and key entities. The NLU agent outputs a structured representation of the user’s request, e.g., {"intent": "ScheduleAppointment", "date": "next week", "type": "check-up"}. This structured data drives the next steps.
	•	3. Dialogue Manager (Central Orchestrator): The dialogue manager is the control center of the system – essentially the “brain” that embodies the business logic and conversation state. It receives the NLU output and the current context, then decides how to respond. Key responsibilities of the Dialogue Manager include:
	•	Determining which backend agent or database to query based on intent (e.g., call the scheduling module for an appointment intent, call the records module for an info query).
	•	Managing conversation flow: if the intent requires multi-step interaction (like scheduling needs picking a time), the manager knows to ask the next question (“What day works for you?”) and update the state with each answer.
	•	Handling context: if the user’s next utterance is related to the previous topic (or changes the topic), the manager updates the dialog state and may switch intents or handle sub-intents as needed.
	•	Error recovery: if NLU confidence is low or response from a module is empty (e.g., no available slots found), decide on fallback prompts or alternative actions.
	•	Composing the final response content (possibly with help from a language generation function or the LLM). The manager might pass a template with slots (e.g., <DoctorName>, <Date> at <Time>) to be filled by data, or it may feed all relevant info to an LLM prompt to generate a natural response sentence.
	•	4. Backend Agents / Modules: These do the domain-specific heavy lifting. We have several in our design:
	•	Appointment Scheduling Agent: Connects to the clinic’s scheduling system or (for our prototype) a mock schedule database. It can check availability, reserve or cancel slots, and return results. For example, if asked to find an appointment next week, it might query the appointments table for openings in the date range and return a list of options. The module could be a simple Python function querying a data structure in the prototype. In a real system, this would integrate with calendar APIs or an EHR scheduling module.
	•	Patient Records Agent: Interfaces with the patient information database. On an info request, this agent looks up the patient by ID and pulls the requested data. In our mock setup, this could be a JSON file or in-memory object containing patient records. It might support queries like get_lab_results(patient_id, test_name) or get_medications(patient_id). The agent ensures the data is retrieved in a structured format (e.g., lab test result value and a normal range, or upcoming appointment details) so that the dialogue manager/LLM can turn it into a sentence.
	•	Knowledge Base / FAQ Agent: Handles general questions by searching a small knowledge base. For the prototype, we might implement a simple keyword-based lookup or use an embedding search for semantic matching if using an LLM. For example, if user asks “What are your hours?”, the agent will fetch the answer from an FAQ dictionary. If the question isn’t found, it flags that for the dialogue manager to handle as a fallback (maybe by saying it’s not sure or escalating).
	•	(Potential additional agents:) In a broader multi-agent system, we could imagine more specialized modules, such as a Triage Agent (for symptom assessment calls, using clinical protocols) or a Billing Agent (for insurance or billing questions using something like the MBS rules mentioned in the challenge ). These are beyond our current scope but illustrate how the modular architecture allows extension. Our design ensures new agents can be plugged in with minimal changes to the core system, which listens for new intent types and routes accordingly.
	•	5. Response Generation: Once the Dialogue Manager has gathered the necessary information from backend agents, it formulates a response. This can be done in two ways depending on context:
	•	Template-based: For very structured transactions (like confirming an appointment booking), we can fill in a predefined sentence template. E.g., template = "Your appointment is confirmed for {Date} at {Time} with Dr. {Name}." filled with actual details. This ensures clarity and avoids AI hallucination for critical info.
	•	LLM-based natural response: For more open-ended info (like explaining a lab result or answering a FAQ), we will use the language model to generate a friendly answer. For example, after fetching a lab result and doctor’s note, we might prompt the LLM: “Explain the following lab result and note to the patient in one or two sentences: [data]”. The LLM’s output (e.g., “Your blood test looked mostly normal except for a slightly high cholesterol level. Dr. Smith recommends improving your diet and will recheck it in 3 months.”) is then used as the agent’s spoken reply. We will curate these prompts carefully to keep responses factual and concise.
	•	6. Text-to-Speech (TTS) Agent: The final text response is sent to the TTS module to synthesize an audio voice message. For the prototype, we can use a cloud TTS service (Google, Amazon Polly) or open-source tools (like Coqui TTS) with a clear female or male voice. The output audio is then streamed back to the caller via the telephony interface. The TTS agent should produce natural and easy-to-understand speech, ideally with a tone that matches a friendly clinical assistant. Latency is a consideration here: we may use faster synthesis or cache certain phrases to speed up common responses.
	•	7. Continuous Dialog Loop: The system then listens for the user’s next utterance, and the cycle repeats (ASR -> NLU -> DM -> etc.) until the call is complete. The Dialogue Manager keeps track of the conversation state throughout. If the call is ended (user hangs up or says goodbye), the system logs the conversation and disengages.

Diagram Description: (Textual) The interaction can be visualized in sequence:
	1.	Caller (Patient) – speaks into phone, e.g., “Schedule an appointment next week.”
	2.	ASR Module – transcribes speech to text: “schedule an appointment next week.”
	3.	NLU Module – interprets text to intent: {intent: ScheduleAppointment, timing: next week}.
	4.	Dialogue Manager – receives intent, verifies patient identity (with Records Agent if needed), then calls Scheduling Agent.
	5.	Scheduling Agent – looks up availability for next week, returns options (Tuesday 10 AM, Wed 2 PM).
	6.	Dialogue Manager – forms a question to user with options.
	7.	TTS Module – voices the question: “We have Tuesday at 10 AM or Wednesday at 2 PM open. Which do you prefer?”
	8.	Caller – responds with choice.
	9.	(Loop back to ASR/NLU, then DM confirms booking via Scheduling Agent).
	10.	Dialogue Manager – after booking, prepares confirmation text. Possibly uses template or LLM for nicety.
	11.	TTS – speaks confirmation to caller.
	12.	Caller – says thank you/goodbye, or asks another question (if another question, DM routes to appropriate agent like Records or FAQ, continuing the loop).
	13.	Call Ends – the system either hangs up on user’s cue or if idle. Logs are saved.

Throughout this architecture, multiple AI components (agents) are at work in a coordinated fashion – this multi-agent orchestration is what enables the voice assistant to handle complex requests. For example, in the lab results scenario, the system might invoke ASR -> NLU -> Records Agent -> LLM for explanation -> TTS. In the scheduling scenario, it might invoke ASR -> NLU -> Records (to identify patient) -> Scheduling -> back-and-forth -> TTS. The Dialogue Manager is key to smoothly interweaving these components.

Technology Stack & Integration:
	•	We plan to implement the server logic in Python, given its rich ecosystem of AI libraries. For instance, we can utilize libraries like SpeechRecognition with Google’s API or OpenAI’s Whisper for ASR, the Anthropic Claude API (or OpenAI) for NLU and response generation, and gTTS or cloud TTS for speech synthesis.
	•	The telephony integration can be done with Twilio: Twilio can send the call audio to our Python server via a webhook (Twilio TwiML  or  with speech input) and we can respond with  for TTS playback, or use Twilio’s Media Streams to pipe audio in/out for real-time interaction. If telephony is complex for the hackathon timeframe, we’ll simulate calls using a web interface where the user can press a button to talk (using the browser mic) and hear the agent’s response audio. This simulation would still use the same backend logic.
	•	Data storage will be minimal: perhaps a simple SQLite database or in-memory Python data structures for the schedule and patient info. This is sufficient for the demo (e.g., a few doctors, a few patients, and a week’s schedule of time slots). We’ll include some sample data (e.g., 2-3 patients, each with some medical info and maybe an existing appointment) to make the interactions realistic.
	•	The system’s design is modular: for instance, we could develop each agent as a separate function or class. This modularity not only aids the multi-agent demonstration but also means we could potentially distribute components (run ASR on one service, NLU on another, etc.). However, for the hackathon prototype, all components will likely run in a single application for simplicity, sequentially or with asynchronous calls as needed.

Overall, the technical architecture emphasizes clarity, modularity, and use of AI where it adds value (language understanding and generation), combined with rule-based logic for deterministic tasks like checking a schedule. This hybrid approach ensures reliability in critical operations (appointments) while leveraging AI for natural interaction – a balance that’s important in healthcare settings.

UX and Conversation Design

Designing a good user experience (UX) for a voice interface is crucial. Even though there’s no graphical UI, the “voice UI” – the flow of dialogue and the content of responses – determines usability. Below are the key UX considerations and examples of conversational content for our voice assistant:
	•	Persona and Tone: The assistant will introduce itself (e.g., “I’m Heidi, the virtual assistant”) to set expectations that the caller is talking to an AI. The tone is friendly, calm, and professional. We avoid technical jargon; language will be simple and reassuring. For example, instead of saying “Your query cannot be processed,” it would say “I’m sorry, I’m having trouble with that.” This persona aligns with a helpful nurse or receptionist – knowledgeable but empathetic.
	•	Guiding the Conversation: The agent will use prompts to guide users through tasks, especially for multi-step processes like scheduling. It asks one question at a time and uses confirmation. For instance, “What day would you like to come in?” followed by “Morning or afternoon preference?” helps the user understand how to answer. After an appointment is scheduled, a confirmation prompt like “Okay, I have booked that. Is there anything else I can help you with?” both confirms action and gently prompts for additional needs, ensuring the user is satisfied before ending the call.
	•	Handling Uncertainty: If the assistant is unsure of what the user said or meant, it employs graceful clarification. For example, if the user mumbles a date, the agent might respond, “Just to confirm, did you say next Tuesday, November 7th?” This approach (reflective listening) confirms understanding and gives the user a chance to correct if wrong. In case of ASR errors, the agent will apologize and ask the user to repeat or rephrase (“I’m sorry, I didn’t catch that. Could you say it again?”). We limit how many times we reprompt (for UX, usually 2 tries before offering an alternative like “Would you like to speak to a staff member?”).
	•	Example Dialogue Snippet: (Combining several UX elements)
Agent: “Hello! Thank you for calling Green Valley Clinic. I’m Heidi, the virtual assistant. How can I help you today?”
User: “Hi, I need to know if Dr. Lee sent my prescription to the pharmacy.”
Agent: “Sure, I can help with that. First, could I have your name and date of birth to pull up your records?” (Polite verification)
User: “It’s John Doe, birth date July 5, 1980.”
Agent: “Thank you, John.” (Using the caller’s name can create a personal touch.) “Let me check your records… ” (slight pause as it ‘looks up’ data) “I see that Dr. Lee prescribed amoxicillin for you on Monday, and yes, it was sent to your pharmacy on file that same day. You should be able to pick it up. Would you like the pharmacy’s phone number or address?” (Provides answer and an extra help offer.)
User: “No, that’s okay. I have it. Thanks.”
Agent: “Glad I could help. Is there anything else you need today?”
User: “Actually, can I schedule a follow-up with Dr. Lee in 2 weeks?” (User initiates a second task in same call)
Agent: “Absolutely. Dr. Lee has an opening on Tuesday, November 21st at 9 AM. Does that work?” (Multi-agent: switches to scheduling seamlessly)
User: “Yes, that’s perfect.”
Agent: “Great, I’ve booked you for November 21st at 9 AM with Dr. Lee. You’ll get a reminder a day before. Anything else?”
User: “No, that’s all. Thank you.”
Agent: “You’re welcome! Thank you for calling, and take care.” (Friendly closing.)
In this example, the assistant handled a medical info query followed by scheduling, maintaining context (knowing it’s Dr. Lee the user is talking about, then scheduling with Dr. Lee) and demonstrating a smooth multi-intent dialogue. The user didn’t have to call back or speak to a human for the second task, which shows the convenience of connecting activities into one workflow .
	•	Confirmation and Acknowledgment: The agent frequently uses confirmation strategies: repeating key info back to the user (“You said…”, “I’ve booked you on…”) to ensure accuracy. It also uses acknowledgments like “Alright,” “Sure,” “Got it,” to make the conversation feel natural and show it’s actively listening and processing requests. This feedback loop is important in voice UX since the user cannot see what the system is doing.
	•	Latency and Pauses: The system will be designed to minimize noticeable delays (through efficient processing and possibly brief filler phrases like “Let me check that for you…” while performing a lookup). Small verbal pauses or typing sounds can be added to indicate the system is working, which prevents the user from feeling the need to repeat the question. We must avoid long silence which could confuse the caller.
	•	Error Messaging: If something goes wrong (e.g., a backend service fails or an unexpected error), the agent will not expose technical details. Instead, it will say a generic apology and fallback: “I’m sorry, something went wrong on my end.” and then either try an alternative or direct the call to human support (“Let me transfer you to a staff member who can assist further.”). For the demo, we might simulate transfer simply by ending the AI interaction in such cases.
	•	Accessibility and Language: The assistant communicates in English for the prototype. We ensure clarity in pronunciation via the TTS voice. If time permits, we may include options for other languages or at least design with that possibility (multi-lingual support) in mind for future. Additionally, for users with hearing impairment who use phone assistive devices, the system’s clear enunciation and option to repeat information is helpful.

Overall, the UX design focuses on making the interaction natural and user-friendly, similar to speaking with a knowledgeable receptionist. By pre-defining conversation flows for each use case and using the language model’s flexibility for less scripted parts, we strike a balance between consistent behavior and adaptability to user input. All dialogue content will be tested for tone and clarity. This careful UX content design ensures that the innovative tech (multi-agent AI) translates into a positive experience for real users.

Data Management and Mock Medical Data

To power the voice assistant’s intelligence, we will prepare and utilize mock data that reflects real-world healthcare information. All data used in the prototype will be fictional, avoiding any real patient information. Here’s how we’ll handle data:
	•	Patient Database (Mock EHR): We will create a small dataset of fictional patients (perhaps 3-5 sample patients for demo purposes). For each patient, we will include fields such as:
	•	Personal Info: Name, date of birth, phone number (which could be used for caller ID recognition if we simulate that), and maybe an ID or medical record number.
	•	Appointments: A list of past and upcoming appointments (date, time, provider, purpose). This allows the agent to answer questions like “When’s my next appointment?” and to know context (e.g., if calling to reschedule, what they currently have booked).
	•	Medications: Current medications and dosages (for queries like “what meds am I on”).
	•	Lab Results: Some recent lab test entries with results and normal range, plus a doctor’s comment for each. We will keep these simple (e.g., a blood test with a couple of values and a one-line note from the doctor).
	•	Visit Notes / Instructions: A brief summary from the last visit or any post-visit instruction (e.g., “Patient advised to exercise and follow up in 3 months”). This can be used to answer follow-up questions or for the agent to remind patients of doctor’s orders if asked.
The patient data can be stored as a JSON or YAML file for easy loading. For example:

{
  "patients": [
    {
      "id": 1,
      "name": "John Doe",
      "dob": "1980-07-05",
      "appointments": [
        {"date": "2025-11-07", "time": "10:00", "doctor": "Dr. Smith", "type": "Check-up"},
        {"date": "2026-02-01", "time": "09:00", "doctor": "Dr. Lee", "type": "Follow-up"}
      ],
      "medications": ["Atorvastatin 20mg daily"],
      "lab_results": [
        {"date": "2025-10-20", "test": "Cholesterol", "result": "210 mg/dL (High)", "note": "Slightly elevated, advise diet change."}
      ],
      "last_visit_note": "Discussed cholesterol management. Advised to improve diet and recheck in 3 months."
    },
    ...
  ]
}

The agent (via the Records module) will query this structure. For instance, if John Doe asks for lab results, it finds the lab_results list for John Doe and retrieves the latest entry.

	•	Scheduling Data: We will also maintain a schedule data structure representing doctors’ availability. For simplicity, we might predefine available slots for the next couple of weeks for the doctors in our scenario (e.g., Dr. Smith, Dr. Lee). This could be as simple as a dictionary with dates as keys and list of available times, or a list of slot objects. During an appointment booking, the system will search this schedule and then mark a slot as booked (removing it from availability and adding an appointment to the patient’s record). Since this is a demo, we don’t need a full calendar system – just enough to show the logic. We will need to ensure the scheduling agent checks this data consistently (possibly locking it during a transaction if multi-threaded, to avoid race conditions in a real system, though concurrency issues are unlikely in a single-call demo).
	•	Knowledge Base (FAQ): A small file (or even a Python dictionary) will contain common questions mapped to answers. For example:

{
  "What are your hours?": "Our clinic is open Monday through Friday, from 8 AM to 6 PM, and on Saturdays from 9 AM to 1 PM.",
  "Where is the clinic located?": "We are located at 123 Health St, San Francisco. The cross street is 5th Avenue.",
  "Do I need a referral to see a specialist?": "For most specialists at our clinic, you do not need a referral. However, some insurance plans might require one."
}

During the call, if an intent is classified as a general inquiry, the Knowledge Agent will attempt to find the closest match to the user’s question in this FAQ (exact match or maybe using a simple similarity measure for phrasing differences). If found, it returns the answer text to the Dialogue Manager to be read out. This covers a range of likely non-personal questions without needing live internet or external databases (which we avoid for simplicity and to ensure we meet the hackathon’s “working prototype” expectation within a limited scope).

	•	No External PHI Access: The system will not connect to any real patient databases or external medical record systems in this prototype. Using strictly mock data ensures we don’t risk any privacy issues and can run the demo offline if needed. It also allows us to craft specific scenarios (like a particular lab result) that we know the assistant can handle, showcasing its capabilities.
	•	Data Initialization: We will write a setup script or code to initialize the mock data at the start of the program (loading the JSON files into memory or a lightweight database). The data can be easily modified for different demo scenarios (for instance, if we want to show a certain type of question, we can populate the data accordingly beforehand).
	•	Data Consistency: Even though it’s fake data, consistency is important. If the patient schedules a new appointment, we will update both the schedule data and the patient’s record (adding that appointment to their list) during the session. This way, if later in the same call the patient asks “when is my appointment,” the agent will include the newly booked one. For the demo, we’ll manage this consistency in memory. In a persistent system, we’d commit to a database.

By planning out the mock data in advance, we ensure the voice assistant’s demo is rich and realistic – the agent will have something meaningful to say for each supported query. It also demonstrates how the system would integrate with real data sources in a production environment, by mimicking those interactions with the fake data.

Implementation Plan and Tools

Delivering this solution in a hackathon timeframe requires choosing the right tools and simplifying where possible. Below is our high-level implementation approach, which we can hand off to developers or an AI coding assistant (like Claude) to generate and refine code:
	•	Programming Language: Python will be used for the backend implementation. Python is ideal due to its extensive libraries for both AI (NLTK/Transformers, etc.) and integration (Flask for webhooks, Twilio library for calls). It also allows quick prototyping. We may structure the project as a simple Flask (or FastAPI) application if we integrate with Twilio for phone calls, handling routes like /voice for Twilio webhooks. If using a purely local demo, we might create a command-line or basic GUI instead.
	•	ASR Integration: We’ll use an API or library for speech-to-text. Two likely options:
	•	The Google Speech-to-Text API (which can be accessed via the speechrecognition Python library) – it’s reliable and quick for short phrases. This would require internet access and an API key.
	•	OpenAI Whisper (via openai-whisper or whisper library) – which can run locally if we have the capacity. Whisper’s accuracy is good, but local inference might be slower on large models. We could use a smaller Whisper model to keep it real-time.
For hackathon simplicity, we might start with Google’s API for immediate results, and have Whisper as a backup if needed. The code will likely involve capturing audio from Twilio or mic and sending it to the ASR service, then receiving text back.
	•	LLM (NLU & NLG): For understanding intents and generating responses, we plan to use a large language model. Since we have access to Claude, we can use Claude’s API for this. We will craft a few prompt templates for different purposes:
	•	Intent Classification Prompt: e.g., “User said: ‘…’. List the intent (Schedule, Cancel, InfoQuery, FAQ, Other) and any details.”. However, an alternative is to manually parse with simple heuristics for known phrases (like “schedule” or “appointment” keywords) to reduce dependency on an LLM for every step. A hybrid might be best: simple regex or keyword matching for high-frequency tasks (schedule, cancel, etc.) and fallback to LLM for more complex utterances.
	•	Response Generation Prompt: e.g., “Generate a friendly response to the user with this info: [context].”. Context may include pieces like {appointment_options} or {lab_result_summary}. We will instruct the model to be concise and accurate.
Using Claude or GPT can accelerate development since we don’t need to train a custom model; we just need to ensure prompts are well-designed. We should also handle possible LLM quirks: constrain outputs (perhaps by giving examples in the prompt or using few-shot demonstrations).
One advantage: Claude’s coding abilities could even generate initial code for parts of this system if needed, but here we focus on using it at runtime for NLU/NLG within the product itself.
	•	Scheduling Logic: We’ll implement a simple scheduling function in Python. Likely, a function that given a date range (or just “next available”), returns a list of open slots from our mock schedule. Another function to book a slot (mark as taken and associate with a patient). This can be done with plain Python lists/dicts. We’ll make sure to include some business rules, like not double-booking and maybe enforcing that appointments are only during working hours. The complexity is low, so this can be hand-coded or done with minimal logic.
	•	Data Access: Since our data is small, we can load the JSON files into Python objects (like a dict of patients and a dict of schedule). We can then write helper functions: get_patient_by_name(name, dob) to retrieve a patient record, get_lab_result(patient, test_name) etc., and get_upcoming_appointment(patient) to fetch the next appointment. Similarly, a schedule_appointment(patient, date, time, doctor) to place a new appointment. These will be straightforward functions. We should also write a couple of unit-test-like checks for these to avoid runtime surprises during demo (for example, ensure that our date format is consistent when comparing or printing).
	•	Twilio (or Voice I/O) Integration: If using Twilio, we will set up a voice webhook. When the call comes in, Twilio will request our /voice endpoint. Initially, we can respond with TwiML that starts  or continuous  with input speech, but to keep simpler, Twilio has a  that can transcribe up to a few seconds of speech and then hit our webhook again with the transcription. However, that turn-by-turn approach might cause pauses. Alternatively, Twilio Media Streams can send real-time audio to our server via WebSocket; that’s more advanced. For hackathon, the easier route: use Twilio  in a loop (prompt, gather, Twilio sends text to /voice, respond with next prompt, etc.). This essentially externalizes ASR to Twilio’s built-in speech reco. Twilio’s accuracy might be limited, but it covers telephony noise and is quick to implement. The design doc can mention Twilio integration but actual coding might simplify with whatever is fastest to implement.
If not Twilio, a desktop or web app could simulate the call. For example, a small Python script using pyaudio to record from microphone and Google STT, then using OS speech engine or playing an MP3 for TTS. But that’s more custom work. Given time, Twilio’s platform might ironically be faster to get a working phone call demo if the team is familiar with it.
	•	Text-to-Speech Output: Twilio has  with some voices which might suffice (they have Polly voices integrated). If not using Twilio’s TTS, the Python code could call a TTS API to get an audio file URL and return TwiML  that file. For a local demo, we might directly output via speakers. We will choose a natural-sounding voice (female voice was used in example, but that’s arbitrary). The key is clarity in the audio.
	•	Multi-Agent Coordination: In code, while conceptually we have multiple agents, we might implement them as classes or just functions within a single process. For instance, an Assistant class that has sub-components: asr, nlu, dm, scheduler, records, tts as attributes, each with a .process() method or similar. The Dialogue Manager (DM) can be a method that uses others. For hackathon, we might not literally spin off separate processes for agents – that overhead isn’t needed – but we will structure the code to reflect these separations. This modular code structure will make it easier to maintain and also to potentially parallelize or distribute if needed.
	•	Testing Plan: We will test each module individually with sample inputs. For example, feed recorded audio of a sample query to the ASR and check the text, feed sample texts to the NLU prompt and see if intents are correctly identified (we can log what the LLM returns and adjust prompt as needed), test scheduling functions with boundary conditions (no slots left, invalid date), etc. Then we’ll do end-to-end tests with simulated conversations (possibly writing a script with predetermined inputs and verifying the assistant’s outputs). This ensures that during the live demo, we are confident in the flows.
	•	Claude Code Assistance: After writing this design, we can leverage Claude (or another AI coding assistant) by providing it with specific module specifications to generate code. For instance, ask Claude to “generate a Python function to find available appointment slots given a schedule data structure X”. This could speed up development. We must review and integrate any AI-generated code carefully to ensure it fits our needs and fix any errors (since during a hackathon, quick iteration is key). Given that our design is modular, different team members or AI agents could work on different modules in parallel (one on the Twilio integration, one on the NLU, etc.).

By following this implementation plan, we intend to have a working prototype by the end of the hackathon that covers the main use cases. The approach is pragmatic – using existing APIs and services for heavy-lifting tasks (speech and language) – and focuses our custom development on the glue and logic that make the system coherent for our specific healthcare scenario. The result will be a system that not only works for the demo but is built on components that could be expanded or replaced with more robust versions for a real product in the future.

Multi-Agent System Considerations

One of the standout aspects of our project is the emphasis on a multi-agent system architecture. While the end-user experiences a single unified assistant, under the hood we have multiple agents (modules) collaborating. Here we discuss why this approach is beneficial and how we manage the multi-agent interactions:
	•	Specialization: Each agent is specialized for its task – this follows the principle of single responsibility. For example, the ASR agent’s sole job is converting speech to text; the Scheduling agent only cares about calendar logic. This specialization means each component can be optimized or even replaced independently. If a better ASR service comes along, we can swap that agent without affecting how scheduling or NLU works, as long as the interface (input audio, output text) remains the same.
	•	Parallel Development: In a multi-agent approach, different team members (or different AI subsystems) can work somewhat independently. For instance, one could improve the NLU model while another refines the appointment booking logic. They interact through defined APIs. In our hackathon scenario, this modularity also allowed us to use AI coding assistants on individual parts safely – e.g., asking for help specifically with the database query code won’t confuse it with the speech recognition code.
	•	Agent Communication: The Dialogue Manager is essentially the mediator between agents. We ensure that the data formats are standardized. For instance, after NLU, we might have a Python dict representing the user’s request. The DM will know which keys to look for (like "intent": "ScheduleAppointment"). Each backend agent might have its own expected input format: the DM transforms the information as needed. For example, DM takes intent “ScheduleAppointment” and calls scheduling_agent.find_slots(patient_id, preferred_date_range); or for an info query, calls records_agent.get_lab_results(patient_id).
	•	State Management: Multi-agent systems require a shared understanding of the state. Our Dialogue Manager will maintain an object with the conversation state (e.g., conversation_state = {"authenticated": True, "patient_id": 1, "current_intent": "ScheduleAppointment", "slots_offered": [...], "last_user_input": "...", ...}). This state object can be passed to or accessed by agents if they need context. For instance, the NLU agent might perform better if it knows the previous question was about lab results (to interpret “Can we schedule that follow-up?” correctly as meaning a follow-up for the lab). We might handle that by including recent dialogue turns in the LLM prompt or by setting flags in state that influence the next action. This is how the multiple agents achieve a form of collaborative memory.
	•	Concurrency and Sequence: In our design, most interactions are sequential because they depend on the user’s turn-taking. However, certain multi-agent operations could be parallelized. For example, if the user asks a compound question (“Can I schedule an appointment and also, what were my test results?”), theoretically the system could query the schedule and the records at the same time. Our initial implementation will likely handle one intent at a time (maybe the first part then the second), but the architecture could be extended for parallel agent invocation if needed (with proper thread safety or async calls).
	•	Error Isolation: If one agent fails or produces an error (say the Records database query fails), the Dialogue Manager can catch that and decide on a fallback. The failure of one component doesn’t necessarily crash the whole system. This isolation is beneficial. For example, if the knowledge base agent doesn’t find an answer, that “None” result is caught and the DM can then default to “I’m not sure” message. This is easier to manage when each agent clearly signals success/failure, as opposed to a monolithic black-box system.
	•	Extensibility: The hackathon solution focuses on a few agents, but future versions could integrate more. Our design, influenced by the challenge guidelines , allows addressing multiple activities or user types. For instance, adding a Provider-facing agent (to retrieve patient info for doctors via voice in an exam room) would involve creating a new intent class (e.g., “ProviderQuery”) and an agent that maybe connects to a different data source (like a hospital EHR interface). The Dialogue Manager could detect if the caller is a provider (maybe by a different phone line or a verbal cue) and route accordingly. Similarly, a Medication Refill Agent could be added to handle prescription refill requests (connecting to a pharmacy API). Our multi-agent framework can accommodate these by simply adding new modules and extending the NLU to recognize the new intents. This shows how the system can grow in capability in an organized way.
	•	Coordination Example (Technical): Suppose the user asks, “I recently had blood work done and I also need to schedule a follow-up. Can you help?”. A naive system might be confused, but our multi-agent approach could handle it as follows: The NLU agent might either identify this as two intents in one utterance or pick one intent and note the other. We might do something clever: use the LLM to split the query or to produce a combined plan (some advanced prompt engineering: “If the user request includes multiple intents, list them.”). The Dialogue Manager could then decide to handle them one by one: first fetch lab results, present them, then move to scheduling. It would maintain context that after giving results, it should ask about scheduling. Essentially, the DM acts like a conductor making sure each agent plays their part in turn. This kind of coordination is complex but feasible, and it’s the kind of challenge multi-agent systems are meant to solve.

In summary, our design doesn’t use “multi-agent” as a buzzword; we truly break down the problem and allocate it to different AI and non-AI agents working together. This architecture aligns with cutting-edge AI system designs and showcases how voice assistants can be more than just one big model – instead, they are structured systems integrating multiple models and services to achieve robust behavior.

Security and Privacy Considerations

Given the healthcare context, security and privacy are paramount. While our hackathon prototype uses only fake data, we have designed with real-world standards in mind:
	•	Patient Data Privacy: In a real deployment, any patient information accessed by the voice agent would be protected under regulations like HIPAA. This means we would enforce authentication (patient verification) before releasing sensitive info (which we do via DOB/name checks in the conversation flow). In production, one might use even stronger auth (PINs, voiceprint recognition, etc.). Our system is careful not to divulge personal health details to anyone but the verified patient. For example, if a caller fails verification, the agent will not proceed to give out data – it might politely say it cannot confirm identity and direct them to staff for assistance.
	•	Data Security: All communication channels would be encrypted. For the telephony part, Twilio uses secure protocols, and our server would run on HTTPS for webhooks. The data at rest (patient records, etc.) would be in a secured database with access controls. In the prototype, security is simulated (we won’t actually have encryption on JSON files in memory), but we can mention encryption where appropriate (like hashing any stored PINs, etc., in comments or documentation).
	•	PHI Handling in Logs: In our demo, we will log conversation text for analysis, but in a real scenario logs containing PHI (Protected Health Information) should be handled carefully or anonymized. If we continue development, we’d integrate a logging filter to mask or omit sensitive details (names, test results) in logs.
	•	Consent and Disclosure: The voice agent clearly identifies itself as an automated system at the start of the call. This transparency is important so users know they’re not speaking to a human (which might matter to some in terms of what they feel comfortable asking or disclosing). Also, if calls are recorded for quality (as many clinics do), that should be announced as well. For the hackathon, we’ll likely skip an explicit recording notice, but we will say “virtual assistant” in the greeting to cover the AI disclosure.
	•	Error Safety (Medical): The assistant will not provide diagnosis or complex medical advice. This is a deliberate limitation for safety. If a user asks a symptom-related question that falls outside the safe knowledge base (e.g., “I have chest pain, what should I do?”), the agent’s response will be a safe redirect: “I’m not a medical professional, but chest pain could be serious – please seek emergency care or speak to a nurse/doctor immediately.” We can include a few of these critical advisories in our knowledge base. It’s better to be cautious. For less urgent but still medical queries (“I have a cough, should I come in?”), the agent might say, “I’m not able to assess symptoms over the phone. If you’re concerned, I can help schedule an appointment or I can have a nurse call you back.” This approach ensures the AI doesn’t overstep and cause harm by giving incorrect advice.
	•	System Reliability: While not traditionally seen as security, reliability is related – for example, ensuring the system doesn’t crash mid-call (which could lead to confusion or data inconsistency). We will handle exceptions in code to avoid the assistant hanging. At worst, if the system encounters a fatal error, it should fail gracefully (perhaps telling the user there’s a technical issue and then end the call or transfer). In the demo, we’ll test thoroughly to avoid any such crashes.
	•	Future Authentication Enhancements: To inspire future work, we note that voice authentication (speaker recognition) could be added so that returning patients might be recognized by voice alone after initial enrollment. We won’t implement that now, but it aligns with Heidi Health’s theme of ambient AI – the system could seamlessly identify and personalize the interaction. This would have to be balanced with error rates though (fallback to DOB check if voice ID isn’t confident).

In short, our design is mindful that healthcare applications carry extra responsibility. We ensure the prototype’s design could meet those standards with additional production hardening. For hackathon demo purposes, we’ll follow the spirit of these considerations (e.g., always ask DOB, no unauthorized info). This gives the judges confidence that we haven’t ignored the real-world constraints while focusing on the tech.

Limitations and Future Improvements

Limitations of the Current Prototype:
	•	Scope of Understanding: The assistant in its current form is limited to the scripts and data we’ve given it. It will perform well for the use cases we anticipate (appointments, basic info) but could be confused by completely unexpected inputs. For example, if a patient asks a very complex multi-part question or speaks for a long time continuously, our simple NLU approach might falter. Large language models help generalize, but without extensive training or fine-tuning, there’s a risk of misunderstanding or off-target answers in edge cases.
	•	Medical Knowledge: Our knowledge base is very limited (only common FAQs and what’s in the patient record). The system does not tap into extensive medical databases or symptom checkers in this prototype. Thus, it cannot answer detailed medical questions or provide comprehensive advice. We chose to limit this to avoid misinformation. Expanding medical knowledge would require integrating vetted sources or medical ontologies, which is outside hackathon scope.
	•	Voice Recognition Accuracy: In noisy environments or with heavy accents, the ASR might make errors. While we use good ASR engines, this is always a challenge. Mis-transcriptions could lead to incorrect agent actions (e.g., scheduling on the wrong date). We mitigate by confirmations (“Did you say Tuesday the 7th?”), but it’s not foolproof. In a demo setting (likely quieter), this should be fine, but real-world usage would need more robust handling (maybe cross-confirm via text message or so for important actions).
	•	Single-Channel Interaction: The current design assumes one caller interacting with the system at a time. It doesn’t cover scenarios like a conference call or multiple people talking (e.g., patient and a family member together). Also, it doesn’t handle multiple concurrent calls in the prototype, since we’ll likely just run one call for demo. Scalability to many simultaneous calls would require a more distributed system and possibly multiple instances of the agent running in parallel. This is more of a deployment scaling issue, which we won’t tackle in the hackathon but is solvable by cloud infrastructure in a real product.
	•	No GUI or Multimodal Interface: Our solution is voice-only. For some users, a complementary visual (like receiving a text confirmation for an appointment, or a link to lab results) would enhance experience. We do mention sending an email or text for certain info (like dietary guidelines) but that is not fully implemented in prototype (we can simulate by just stating we would). In the future, the agent could automatically send a summary of the call or details via SMS/email for record-keeping.
	•	Rule-Based Dialogue Management: Our dialogue manager logic, while functional, is mostly rule-based or flowchart-like, with a bit of help from LLM for language. This is manageable for defined scenarios but doesn’t learn from experience. In complex dialogues, a purely learned approach might handle the flow more flexibly. However, training a reinforcement learning-based dialogue policy is far beyond hackathon scope. So we stick to a deterministic approach with limited adaptability.

Future Improvements and Extensions:
Should this prototype move beyond the hackathon into further development, we see several avenues to enhance it:
	•	Expanded Multi-Agent Capabilities: Introduce additional agents to broaden the assistant’s utility. For example, a Symptom Triage Agent that, given certain symptom descriptions, can ask further questions and suggest next steps (using established clinical decision trees). This could be integrated so that patients calling with illness concerns get guided advice (and then perhaps an appointment if needed). Another agent could be a Billing/Insurance Agent to answer “Do I have any co-pay for my next visit?” or “What’s the cost of X procedure?”, which might involve looking up insurance coverage rules (the Heidi challenge hint about MBS Online  suggests such possibilities). Incorporating these would move the system closer to a comprehensive front-line assistant for many call types a clinic receives.
	•	Natural Language Understanding Improvement: Fine-tune a domain-specific language model for healthcare dialogues. Using conversation transcripts (maybe synthetic) of patient calls, we could train the NLU to better recognize intents and even detect emotional tone (if a patient sounds upset or urgent, the system might prioritize or respond with extra empathy). This could reduce reliance on cloud APIs and improve reliability.
	•	Contextual Personalization: If connected to a real EHR, the assistant could use more context proactively. For example, if it sees the patient had a recent ER visit or an upcoming surgery, it might proactively ask if they are calling about that (“Are you calling about your upcoming surgery on May 10?”). This level of personalization can make the agent feel more helpful. It would require careful design not to seem intrusive.
	•	Multi-Modal Integration: As mentioned, complement voice with text or app integration. A possible future iteration could be a smartphone app where a patient can either speak or type to the same assistant agent and get responses (including images if relevant, like a map to the clinic). Or, after a voice call, the assistant sends a summary via text. These multi-modal additions would enhance user satisfaction.
	•	Incorporating User Feedback: Build a feedback mechanism. After each call or interaction, the system could ask, “Was I able to resolve your issue today?” or later send a survey link. Gathering this feedback would help identify shortcomings. The system could even learn from it (with supervised updates or by flagging misunderstood queries for developers to address).
	•	Deployment and Scalability: To use this in production, we’d deploy on a cloud platform with autoscaling (so multiple calls at once are handled). We’d also integrate with actual phone lines, possibly using SIP or other telephony systems for clinics. Real-time monitoring dashboards could be built to track calls handled by the AI vs transferred to humans, etc., to measure efficacy.
	•	Compliance and Certifications: If we productize, we’d pursue necessary certifications for healthcare IT products, ensure all data handling is compliant, and possibly allow an opt-in/opt-out for patients who prefer a human (some patients might always want to talk to a person; the system could recognize those preferences from a CRM and directly route such callers to staff).

Finally, a long-term vision could be that such a voice agent becomes an ambient presence in healthcare – not just on calls, but perhaps in hospital rooms or at home via smart speakers, assisting patients throughout their care journey. Heidi Health’s focus is ambient AI, and our solution could be a stepping stone: first mastering phone calls, then expanding to other voice-touchpoints in healthcare.

Conclusion

In this PRD and design document, we presented a comprehensive plan for a Smart Voice Assistant for Patient Support, tailored to Heidi Health’s hackathon challenge. The solution focuses on a high-impact area – managing patient phone calls – where a voice agent can greatly improve efficiency and patient satisfaction. By enabling natural voice interactions for appointment management and medical information queries, we address critical needs in the healthcare domain  . Patients gain 24/7 access to assistance, and healthcare staff see reduced routine workload, aligning with Heidi Health’s mission to let providers spend more time on patient care rather than paperwork and calls .

Our design stands out by leveraging a multi-agent system architecture. This modular approach not only showcases advanced AI integration (speech recognition, language understanding, scheduling logic, data retrieval working in unison) but also provides a robust framework for future expansion. We demonstrated through user journeys and technical architecture how multiple activities can be connected in one seamless workflow  – for example, checking a lab result and booking a follow-up in the same call – delivering a fluid experience that goes beyond a single-use chatbot.

The document covered in detail the user experience design, ensuring the voice assistant communicates in a polite, clear, and helpful manner. We also elaborated on the technical implementation plan, from chosen tools (Python, APIs, TTS engines) to how we will structure and develop each component. Important considerations like data privacy, error handling, and future scalability were addressed, demonstrating that we’ve thought through not just the “happy path” but also real-world constraints and how the system would behave under various conditions.

By adhering to these plans, our team is confident we can build a working prototype that meets the hackathon requirements: a live demo of a voice-controlled healthcare assistant that is both innovative and practical. The prototype will illustrate the core functionality and prove the concept. With more time, the same architecture can be extended and refined into a full-fledged product that could be deployed in clinics, truly making an impact.

In summary, this voice agent project fulfills the brief of identifying a critical need (patient call handling) and designing an effective AI solution for it . It highlights the power of combining conversational AI with healthcare data systems in a safe and user-centric way. We believe this system will showcase proficiency in multi-agent AI and impress upon the judges the potential of voice technology in healthcare, all while being achievable within the hackathon’s scope. We are excited to proceed with implementation and bring this concept to life with the help of Claude and our development efforts, ultimately demonstrating how an ambient voice assistant can elevate healthcare experiences for both patients and providers.