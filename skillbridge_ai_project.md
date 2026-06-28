## **SkillBridge AI** 

Student Project Brief: Building an Education and Recruitment Copilot with LLMs 

Building LLM Applications with Prompt Engineering 

June 14, 2026 

## **Abstract** 

SkillBridge AI is a student project idea for building a practical LLM-based application in education, human resources, and recruitment. The system helps learners identify skill gaps, receive personalized learning recommendations, practice interviews, and connect their abilities to suitable job opportunities. It also helps recruiters review candidates using explainable, skillbased evidence rather than simple keyword matching. The project applies prompt engineering, LangChain workflows, structured output, chatbot design, and tool-using agents. 

## **1 Project Context** 

Large Language Models (LLMs) can be used to build applications that analyze text, generate recommendations, support conversations, extract structured data, and use external tools. In this project, students will design a prototype that connects learning outcomes with employability. 

The goal is not only to create a chatbot. The goal is to design a complete LLM workflow that can read learner and recruitment data, reason over it, produce structured outputs, and support a human decision-maker. 

## **2 Project Vision** 

The main idea is to build an AI system that follows a learner from education to employment. The system analyzes a learner profile, compares it with real job requirements, recommends learning actions, simulates interviews, and supports recruiters with structured candidate insights. 

## **3 Problem Statement** 

Education and recruitment are often disconnected. Learners may complete courses without knowing whether they are ready for real jobs. Educators may not have a clear view of current market needs. Recruiters spend a large amount of time reviewing CVs manually and may overlook strong candidates because traditional screening often depends on keywords. 

## **Main Problems** 

- Learners do not clearly understand their missing skills for a target role. 

- Courses are often generic and not personalized to career goals. 

- Recruiters spend too much time screening CVs manually. 

- Hiring decisions are sometimes based on weak or unclear evidence. 

- Interview preparation is not always realistic or role-specific. 

1 

## **4 Learning Objectives** 

By completing this project, students should be able to: 

- Apply iterative prompt engineering to solve a realistic business and education problem. 

- Use prompt templates to standardize repeated LLM tasks. 

- Organize LLM workflows using LangChain and LangChain Expression Language (LCEL). 

- Generate structured outputs for downstream use, such as skill lists, scores, tags, and recommendations. 

- Design a chatbot experience using system, human, and AI messages. 

- Explain when an LLM should call an external tool or API. 

- Evaluate LLM outputs for accuracy, fairness, usefulness, and safety. 

## **5 Proposed Solution** 

SkillBridge AI provides a unified AI workflow for education and recruitment. The system uses LLMs to analyze documents, generate structured insights, personalize learning, and assist HR teams in making explainable recruitment decisions. 

## **Technologies Applied** 

- **NVIDIA NIM:** Deploy and access a powerful language model in a production-ready way. 

- **Llama 3.1:** Generate, analyze, classify, and reason over text. 

- **LangChain:** Organize prompts, chains, runnables, and application workflows. 

- **LCEL:** Compose multiple LLM chains into one larger application workflow. 

- **Prompt Templates:** Standardize prompts for skill analysis, coaching, and recruitment. 

- **Structured Output:** Extract skills, scores, tags, and recommendations as JSON-like data. 

- **Tools and Agents:** Connect the LLM to external APIs such as job market data, salary data, calendars, and HR systems. 

2 

## **6 Project Chart** 

|**Module**|**Problem**|**LLM Solution**|**Output**|
|---|---|---|---|
|Learner Skill Scan-<br>ner|Learners do not know<br>which skills are missing<br>for a target job.|Analyze CVs, projects,<br>course history, and job<br>descriptions using<br>structured prompts.|Skill gap map,<br>readiness score,<br>recommended learning<br>path.|
|Adaptive Learning<br>Coach|Generic learning<br>content does not adapt<br>to the learner’s needs.|Generate personalized<br>explanations, exercises,<br>quizzes, and feedback<br>using prompt<br>templates and<br>LangChain chains.|Personalized lessons,<br>practice tasks, and<br>weekly progress notes.|
|Recruitment<br>Match Engine|Recruiters lose time<br>screening CVs and may<br>miss non-traditional<br>candidates.|Extract structured<br>skills and match them<br>against job<br>requirements with<br>explainable scoring.|Candidate shortlist, ft<br>score, and match<br>rationale.|
|Interview<br>Simula-<br>tor|Candidates lack<br>realistic role-specifc<br>interview practice.|Use system messages,<br>chat history, and<br>rubric-based prompts<br>to simulate interviews.|Interview transcript,<br>performance feedback,<br>and improvement plan.|
|HR<br>Agent<br>With<br>Tools|Recruitment decisions<br>need live data and<br>internal policy context.|Use an agent that can<br>call salary APIs, job<br>market APIs, HR<br>databases, and policy<br>documents.|Evidence-backed HR<br>recommendation with<br>tool results.|



## **7 Suggested Implementation Steps** 

## 1. **Discovery and Data Collection** 

- Collect or create sample learner profiles, CVs, job descriptions, course outlines, project portfolios, and recruiter evaluation rubrics. 

## 2. **Prompt Engineering Prototype** 

Design prompts for skill extraction, gap analysis, learning recommendations, interview questions, and candidate summaries. Test several prompt versions and compare their outputs. 

## 3. **LangChain Workflow Design** 

   - Build reusable chains with LangChain Expression Language. Use parallel chains for CV analysis, job analysis, and learning path generation. 

4. **Structured Output Layer** 

   - Define schemas for skills, scores, evidence, risk flags, interview feedback, and recommendations. 

## 5. **Agent and Tool Integration** 

- Connect the system to external tools such as job market APIs, salary benchmarks, LMS platforms, HR databases, and calendar systems. 

## 6. **Pilot Test** 

Test the system with students, educators, recruiters, and hiring managers. Measure time saved, quality of recommendations, learner readiness, and hiring outcomes. 

3 

7. **Evaluation and Improvement** 

Improve prompts, scoring rules, structured output reliability, and human review workflows based on pilot feedback. 

## **8 Expected Student Deliverables** 

Each team should prepare the following deliverables: 

- **Project brief:** A short explanation of the problem, users, solution, and expected value. 

- **Prompt library:** At least five prompts, including prompts for skill extraction, learning recommendation, interview simulation, structured output, and recruiter summary. 

- **Workflow diagram:** A simple diagram showing inputs, LLM chains, tools, outputs, and human review points. 

- **Prototype:** A working notebook, script, or small application that demonstrates the core workflow. 

- **Structured output example:** A sample JSON-like output showing skills, scores, evidence, and recommendations. 

- **Evaluation report:** A short analysis of output quality, limitations, risks, and improvements. 

- **Final presentation:** A concise demonstration explaining the value of the solution. 

## **9 Added Value** 

|**Stakeholder**|**Added Value**|**Expected Result**|
|---|---|---|
|Learners|Clear understanding of missing<br>skills and next learning actions.|Better confdence, stronger<br>portfolios, and faster job readiness.|
|Educators|Visibility into class-level skill gaps<br>and weak concepts.|More targeted teaching and<br>improved learning outcomes.|
|Recruiters|Explainable candidate screening<br>based on skills and evidence.|Less manual work and<br>higher-quality shortlists.|
|Hiring Managers|Interview questions generated from<br>real candidate evidence.|More focused interviews and faster<br>decisions.|
|Organizations|One system connecting learning,<br>internal mobility, and recruitment.|Lower hiring cost and stronger<br>talent pipelines.|



## **10 Innovative Extension: AI Career Twin** 

The most innovative extension is the **AI Career Twin** . Each learner receives a living AI profile that understands their skills, learning history, project evidence, interview performance, and career goals. 

## **How It Works** 

- For the learner, it creates weekly learning missions. 

- For the educator, it generates coaching briefs and class insights. 

- For the recruiter, it creates explainable candidate summaries. 

4 

- For the hiring manager, it suggests interview questions based on real evidence. 

This creates a continuous pipeline: learn, practice, prove, interview, and match to jobs using the same trusted evidence base. 

## **11 Responsible AI and Ethics** 

Because this project deals with education and recruitment, students must think carefully about responsible AI. 

- **Human review:** The system should support decisions, not replace educators or recruiters. 

- **Fairness:** The application should avoid unfairly penalizing candidates based on background, writing style, school name, gender, age, or nationality. 

- **Privacy:** CVs, student records, and interview transcripts should be treated as sensitive data. 

- **Transparency:** Recommendations should include evidence and explanation. 

- **Limitations:** The system should clearly state when information is uncertain or incomplete. 

## **12 Expected Impact** 

|**Metric**|**Target Improvement**|
|---|---|
|Manual CV screening time|40% reduction|
|Learner role readiness|30% improvement|
|Qualifed shortlist quality|25% improvement|
|Explainability of recommendations|100% required|
|Interview preparation quality|35% improvement|



## **13 Assessment Criteria** 

|**Criterion**|**What Will Be Evaluated**|**Weight**|
|---|---|---|
|Problem understanding|Clarity of the problem, target users, and real-world<br>relevance.|15%|
|Prompt<br>engineering<br>quality|Use of clear instructions, examples, iteration, and<br>task-specifc prompt design.|25%|
|Workfow design|Efective use of LangChain concepts, chaining,<br>structured output, and tool-use logic.|25%|
|Prototype<br>demonstra-<br>tion|Ability to show a working or realistic proof of concept<br>with meaningful outputs.|20%|
|Evaluation and ethics|Quality analysis, responsible AI considerations,<br>limitations, and improvement plan.|15%|



## **14 Conclusion** 

SkillBridge AI is a strong student project because it applies modern LLM technologies to a realworld problem with measurable value. It demonstrates prompt engineering, LangChain workflows, structured output, chatbot design, and tool-using agents in one consistent application. Students are encouraged to start with a simple prototype, evaluate its outputs carefully, and improve it through iteration. 

5 

