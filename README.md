# Deep Research With Gemini

This project harnesses the power of Google's **Gemini 2.5 Flash** model to perform automated, deep research on any given topic. Be it for academic purposes, interview preparation, or skill mastery, this system acts as a personalized research assistant that plans, curates, and compiles comprehensive study materials.

## Why This Project?

In an era of information overload, finding structured, high-quality, and comprehensive learning resources can be time-consuming. This tool solves that by:
*   **Automating Research:** Instead of spending hours manually searching and filtering results, the system uses Gemini's deep research capabilities to find the most relevant and up-to-date information.
*   **Structured Learning:** It doesn't just dump information; it creates a logical, step-by-step study plan tailored to the topic.
*   **Comprehensive Coverage:** From basic concepts to advanced "gotchas" and interview questions, it ensures a holistic understanding of the subject.
*   **Visual & Portable Output:** The final output is a beautifully formatted HTML report that you can save, print, or share.

## How It Works (The Flow)

The system operates as a multi-agent pipeline, where specialized AI agents collaborate to produce the final report:

1.  **User Input**: You provide a topic (e.g., "Advanced Python Concurrency" or "History of Rome").
2.  **Phase 1: Research & Planning (`StudyPlanAgent`)**:
    *   The agent performs a deep search using Google Search grounding to understand the topic's scope, trends, and key requirements.
    *   It generates a detailed **Study Plan** broken down by weeks or modules.
3.  **Phase 2: Content Generation (`StudyMaterialAgent`)**:
    *   Using the approved study plan, this agent acts as a textbook author.
    *   It writes an exhaustive, A-to-Z study guide covering every item in the plan with definitions, examples, code snippets, and real-world applications.
4.  **Phase 3: Interview Preparation (`InterviewPrepAgent`)**:
    *   Acting as a senior interviewer, this agent generates 20+ challenging questions, scenarios, and "gotchas" relevant to the topic to test your mastery.
5.  **Phase 4: Compilation & Reporting**:
    *   The system aggregates all generated content, calculates token usage and estimated costs.
    *   It renders a polished **HTML Report** using Jinja2 templates, ready for use.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Deep-Research-With-Gemini
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration:**
    Create a `.env` file in the root directory and add your Google API key:
    ```env
    GOOGLE_API_KEY=your_api_key_here
    ```

## Usage

Run the main script from the root directory:

```bash
python src/main.py
```

Follow the on-screen prompts to enter your research topic. The final report will be saved in the `output/` directory.

## Project Structure

-   `src/`: Contains the source code.
    -   `agents.py`: Defines the AI agents (StudyPlan, Material, Interview).
    -   `main.py`: The entry point that orchestrates the workflow.
    -   `utils.py`: Helper functions for HTML generation.
-   `templates/`: Jinja2 templates for styling the HTML report.
-   `output/`: Destination for generated reports.
